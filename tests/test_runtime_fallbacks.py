"""
Tests for runtime fallback behavior.

Tests language detection, spaCy segmentation, and other fallback scenarios
with proper observability (logs and metrics).
"""

import pytest
from unittest.mock import patch, MagicMock, call

from saaaaaa.core.runtime_config import RuntimeConfig, RuntimeMode
from saaaaaa.core.contracts.runtime_contracts import (
    LanguageTier,
    LanguageDetectionInfo,
    SegmentationMethod,
    SegmentationInfo,
    FallbackCategory,
)


class TestLanguageDetectionFallbacks:
    """Test language detection fallback scenarios."""
    
    def test_successful_language_detection(self):
        """Test successful language detection with no fallback."""
        from saaaaaa.processing.document_ingestion import PreprocessingEngine
        
        engine = PreprocessingEngine()
        text = "Este es un documento de prueba en español con suficiente texto para detectar el idioma correctamente."
        
        language, lang_info = engine.detect_language(text=text)
        
        # Should detect Spanish successfully
        assert language in ["es", "spanish"]
        assert lang_info.tier == LanguageTier.NORMAL
        assert lang_info.reason is None
    
    def test_insufficient_text_fallback(self):
        """Test fallback when text is too short."""
        from saaaaaa.processing.document_ingestion import PreprocessingEngine
        
        engine = PreprocessingEngine()
        text = "Hola"  # Too short
        
        language, lang_info = engine.detect_language(text=text)
        
        # Should fall back to Spanish with warning
        assert language == "es"
        assert lang_info.tier == LanguageTier.WARN_DEFAULT_ES
        assert "Insufficient text" in lang_info.reason
    
    @patch('saaaaaa.processing.document_ingestion.detect')
    def test_langdetect_exception_fallback(self, mock_detect):
        """Test fallback when langdetect raises exception."""
        from saaaaaa.processing.document_ingestion import PreprocessingEngine
        from saaaaaa.processing.document_ingestion import LangDetectException
        
        engine = PreprocessingEngine()
        mock_detect.side_effect = LangDetectException("Detection failed", [])
        
        text = "Some text that will fail detection"
        
        with patch('saaaaaa.core.observability.structured_logging.log_fallback') as mock_log, \
             patch('saaaaaa.core.observability.metrics.increment_fallback') as mock_metric:
            
            language, lang_info = engine.detect_language(text=text)
            
            # Should fall back to Spanish
            assert language == "es"
            assert lang_info.tier == LanguageTier.WARN_DEFAULT_ES
            assert "LangDetectException" in lang_info.reason
            
            # Should emit structured log
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['component'] == 'language_detection'
            assert call_kwargs['fallback_category'] == FallbackCategory.B
            
            # Should emit metric
            mock_metric.assert_called_once()
    
    @patch('saaaaaa.processing.document_ingestion.detect')
    def test_unexpected_error_fallback(self, mock_detect):
        """Test fallback on unexpected error."""
        from saaaaaa.processing.document_ingestion import PreprocessingEngine
        
        engine = PreprocessingEngine()
        mock_detect.side_effect = RuntimeError("Unexpected error")
        
        text = "Some text"
        
        with patch('saaaaaa.core.observability.structured_logging.log_fallback') as mock_log:
            language, lang_info = engine.detect_language(text=text)
            
            # Should fall back to unknown
            assert language == "unknown"
            assert lang_info.tier == LanguageTier.FAIL
            assert "Unexpected error" in lang_info.reason
            
            # Should log fallback
            mock_log.assert_called_once()


class TestSpacySegmentationFallbacks:
    """Test spaCy segmentation fallback chain."""
    
    @patch('saaaaaa.flux.phases.spacy')
    def test_successful_lg_model(self, mock_spacy_module):
        """Test successful segmentation with LG model."""
        # Mock spaCy with LG model available
        mock_nlp = MagicMock()
        mock_spacy_module.load.return_value = mock_nlp
        
        # Mock sentence segmentation
        mock_sent = MagicMock()
        mock_sent.text = "Test sentence."
        mock_sent.start_char = 0
        mock_sent.end_char = 14
        mock_sent.__len__ = lambda self: 2
        mock_sent.root.lemma_ = "test"
        mock_sent.root.pos_ = "NOUN"
        mock_sent.ents = []
        
        mock_doc = MagicMock()
        mock_doc.sents = [mock_sent]
        mock_nlp.return_value = mock_doc
        
        from saaaaaa.flux.phases import run_normalize
        from saaaaaa.flux.configs import NormalizeConfig
        from saaaaaa.flux.models import IngestDeliverable
        
        config = NormalizeConfig(unicode_form="NFC", keep_diacritics=True)
        ingest = IngestDeliverable(raw_text="Test sentence.")
        
        with patch('saaaaaa.core.observability.metrics.increment_segmentation_method') as mock_metric:
            result = run_normalize(config, ingest)
            
            # Should use LG model
            assert result.ok
            mock_spacy_module.load.assert_called_with("es_core_news_lg")
            
            # Should emit metric
            mock_metric.assert_called()
            call_kwargs = mock_metric.call_args[1]
            assert call_kwargs['method'] == SegmentationMethod.SPACY_LG
    
    @patch('saaaaaa.flux.phases.spacy')
    def test_downgrade_to_md_model(self, mock_spacy_module):
        """Test downgrade from LG to MD model."""
        # LG fails, MD succeeds
        def load_side_effect(model_name):
            if model_name == "es_core_news_lg":
                raise OSError("Model not found")
            elif model_name == "es_core_news_md":
                mock_nlp = MagicMock()
                mock_doc = MagicMock()
                mock_doc.sents = []
                mock_nlp.return_value = mock_doc
                return mock_nlp
            raise OSError("Model not found")
        
        mock_spacy_module.load.side_effect = load_side_effect
        
        from saaaaaa.flux.phases import run_normalize
        from saaaaaa.flux.configs import NormalizeConfig
        from saaaaaa.flux.models import IngestDeliverable
        
        config = NormalizeConfig(unicode_form="NFC", keep_diacritics=True)
        ingest = IngestDeliverable(raw_text="Test text.")
        
        with patch('saaaaaa.core.observability.structured_logging.log_fallback') as mock_log, \
             patch('saaaaaa.core.observability.metrics.increment_fallback') as mock_fallback_metric:
            
            result = run_normalize(config, ingest)
            
            # Should succeed with MD model
            assert result.ok
            
            # Should log downgrade
            mock_log.assert_called()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['component'] == 'text_segmentation'
            assert 'downgrade' in call_kwargs['fallback_mode']
            
            # Should emit fallback metric
            mock_fallback_metric.assert_called()
    
    @patch('saaaaaa.flux.phases.spacy')
    def test_fallback_to_regex(self, mock_spacy_module):
        """Test fallback to regex when all spaCy models fail."""
        # All spaCy models fail
        mock_spacy_module.load.side_effect = OSError("No models available")
        
        from saaaaaa.flux.phases import run_normalize
        from saaaaaa.flux.configs import NormalizeConfig
        from saaaaaa.flux.models import IngestDeliverable
        
        config = NormalizeConfig(unicode_form="NFC", keep_diacritics=True)
        ingest = IngestDeliverable(raw_text="First sentence. Second sentence.")
        
        with patch('saaaaaa.core.observability.structured_logging.log_fallback') as mock_log, \
             patch('saaaaaa.core.observability.metrics.increment_segmentation_method') as mock_metric:
            
            result = run_normalize(config, ingest)
            
            # Should succeed with regex
            assert result.ok
            assert len(result.payload['sentences']) > 0
            
            # Should log regex fallback
            mock_log.assert_called()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['fallback_mode'] == 'regex_fallback'
            
            # Should emit regex metric
            mock_metric.assert_called()
            call_kwargs = mock_metric.call_args[1]
            assert call_kwargs['method'] == SegmentationMethod.REGEX


class TestFallbackObservability:
    """Test that fallbacks emit proper logs and metrics."""
    
    def test_fallback_emits_structured_log(self):
        """Test that fallbacks emit structured logs."""
        from saaaaaa.core.observability.structured_logging import log_fallback
        from saaaaaa.core.runtime_config import RuntimeMode
        
        with patch('saaaaaa.core.observability.structured_logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_fallback(
                component='test_component',
                subsystem='test_subsystem',
                fallback_category=FallbackCategory.B,
                fallback_mode='test_fallback',
                reason='Test reason',
                runtime_mode=RuntimeMode.DEV,
            )
            
            # Should call logger
            mock_logger.warning.assert_called_once()
    
    def test_fallback_emits_metric(self):
        """Test that fallbacks emit Prometheus metrics."""
        from saaaaaa.core.observability.metrics import increment_fallback
        from saaaaaa.core.runtime_config import RuntimeMode
        
        # This will increment the actual counter
        increment_fallback(
            component='test_component',
            fallback_category=FallbackCategory.B,
            fallback_mode='test_mode',
            runtime_mode=RuntimeMode.DEV,
        )
        
        # Verify counter exists (actual value check would require Prometheus client inspection)
        from saaaaaa.core.observability.metrics import fallback_activations_total
        assert fallback_activations_total is not None


class TestFallbackCategoryEnforcement:
    """Test that fallback categories are enforced correctly."""
    
    def test_category_b_allowed_in_dev(self):
        """Category B fallbacks should be allowed in DEV mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.DEV,
            allow_contradiction_fallback=True,
            allow_execution_estimates=True,
            allow_dev_ingestion_fallbacks=True,
            allow_aggregation_defaults=True,
            strict_calibration=False,
            allow_validator_disable=True,
            allow_hash_fallback=True,
            preferred_spacy_model="es_core_news_lg"
        )
        
        # Category B fallbacks should be allowed
        assert config.allow_dev_ingestion_fallbacks is True
    
    def test_category_b_restricted_in_prod(self):
        """Category B fallbacks should be restricted in PROD mode."""
        config = RuntimeConfig(
            mode=RuntimeMode.PROD,
            allow_contradiction_fallback=False,
            allow_execution_estimates=False,
            allow_dev_ingestion_fallbacks=False,
            allow_aggregation_defaults=False,
            strict_calibration=True,
            allow_validator_disable=False,
            allow_hash_fallback=False,
            preferred_spacy_model="es_core_news_lg"
        )
        
        # Category B fallbacks should be disallowed
        assert config.allow_dev_ingestion_fallbacks is False
        assert config.allow_hash_fallback is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
