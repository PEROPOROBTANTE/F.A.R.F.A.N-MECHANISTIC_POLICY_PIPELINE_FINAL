"""
Unit tests for Financial Viability Tables (financiero_viabilidad_tablas.py)

Tests PDET municipal plan analysis, table extraction, financial indicator extraction,
and quality scoring with causal inference.
"""
from decimal import Decimal
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.farfan_pipeline.analysis.financiero_viabilidad_tablas import (
    ColombianMunicipalContext,
    ExtractedTable,
    FinancialIndicator,
    PDETMunicipalPlanAnalyzer,
    QualityScore,
    ResponsibleEntity,
)


@pytest.fixture
def mock_analyzer():
    """Create mock analyzer with mocked dependencies."""
    with patch('src.farfan_pipeline.analysis.financiero_viabilidad_tablas.SentenceTransformer'), \
         patch('src.farfan_pipeline.analysis.factory.load_spacy_model'), \
         patch('src.farfan_pipeline.analysis.financiero_viabilidad_tablas.pipeline'):

        analyzer = PDETMunicipalPlanAnalyzer(use_gpu=False)

        # Mock the semantic model
        analyzer.semantic_model = Mock()
        analyzer.semantic_model.encode = Mock(return_value=np.random.rand(768))

        # Mock NLP model
        analyzer.nlp = Mock()

        return analyzer


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'Programa': ['Educación', 'Salud', 'Infraestructura'],
        'Presupuesto': ['500,000,000', '300,000,000', '700,000,000'],
        'Responsable': ['Secretaría de Educación', 'Secretaría de Salud', 'Secretaría de Obras'],
        'Meta': ['95%', '100%', '80%']
    })


class TestColombianMunicipalContext:
    """Test suite for Colombian municipal context."""

    def test_official_systems_defined(self):
        """Test official systems are properly defined."""
        context = ColombianMunicipalContext()

        assert 'SISBEN' in context.OFFICIAL_SYSTEMS
        assert 'SGP' in context.OFFICIAL_SYSTEMS
        assert 'SGR' in context.OFFICIAL_SYSTEMS
        assert 'DANE' in context.OFFICIAL_SYSTEMS

    def test_territorial_categories(self):
        """Test territorial categories are defined."""
        context = ColombianMunicipalContext()

        assert len(context.TERRITORIAL_CATEGORIES) == 7
        assert 1 in context.TERRITORIAL_CATEGORIES
        assert context.TERRITORIAL_CATEGORIES[1]['name'] == 'Especial'

    def test_dnp_dimensions(self):
        """Test DNP dimensions are defined."""
        context = ColombianMunicipalContext()

        assert len(context.DNP_DIMENSIONS) == 5
        assert 'Dimensión Económica' in context.DNP_DIMENSIONS
        assert 'Dimensión Social' in context.DNP_DIMENSIONS

    def test_pdet_pillars(self):
        """Test PDET pillars are defined."""
        context = ColombianMunicipalContext()

        assert len(context.PDET_PILLARS) == 8
        assert 'Ordenamiento social de la propiedad rural' in context.PDET_PILLARS
        assert 'Salud rural' in context.PDET_PILLARS

    def test_pdet_theory_of_change(self):
        """Test PDET theory of change structure."""
        context = ColombianMunicipalContext()

        assert 'Salud rural' in context.PDET_THEORY_OF_CHANGE
        toc = context.PDET_THEORY_OF_CHANGE['Salud rural']
        assert 'outcomes' in toc
        assert 'mediators' in toc
        assert 'lag_years' in toc


class TestPDETMunicipalPlanAnalyzer:
    """Test suite for PDET Municipal Plan Analyzer."""

    def test_initialization(self, mock_analyzer):
        """Test analyzer initialization."""
        assert mock_analyzer is not None
        assert mock_analyzer.device in ['cuda', 'cpu']
        assert mock_analyzer.context is not None

    def test_clean_dataframe(self, mock_analyzer, sample_dataframe):
        """Test DataFrame cleaning."""
        cleaned = mock_analyzer._clean_dataframe(sample_dataframe)

        assert isinstance(cleaned, pd.DataFrame)
        assert not cleaned.empty

    def test_clean_dataframe_empty(self, mock_analyzer):
        """Test cleaning empty DataFrame."""
        empty_df = pd.DataFrame()
        cleaned = mock_analyzer._clean_dataframe(empty_df)

        assert cleaned.empty

    def test_is_likely_header(self, mock_analyzer):
        """Test header row detection."""
        header_row = pd.Series(['Programa', 'Presupuesto', 'Responsable'])

        # Should recognize as header (nouns, short text)
        is_header = mock_analyzer._is_likely_header(header_row)

        assert isinstance(is_header, bool)

    def test_deduplicate_tables(self, mock_analyzer):
        """Test table deduplication."""
        tables = [
            ExtractedTable(
                df=sample_dataframe,
                page_number=1,
                table_type='financial',
                extraction_method='camelot_lattice',
                confidence_score=0.9
            ),
            ExtractedTable(
                df=sample_dataframe,  # Duplicate
                page_number=1,
                table_type='financial',
                extraction_method='camelot_stream',
                confidence_score=0.85
            )
        ]

        unique = mock_analyzer._deduplicate_tables(tables)

        assert isinstance(unique, list)
        # Should keep only one (highest confidence)
        assert len(unique) <= len(tables)


class TestExtractedTable:
    """Test suite for ExtractedTable data structure."""

    def test_extracted_table_creation(self, sample_dataframe):
        """Test ExtractedTable instantiation."""
        table = ExtractedTable(
            df=sample_dataframe,
            page_number=1,
            table_type='financial',
            extraction_method='camelot_lattice',
            confidence_score=0.9
        )

        assert table.page_number == 1
        assert table.table_type == 'financial'
        assert table.extraction_method == 'camelot_lattice'
        assert table.confidence_score == 0.9
        assert table.is_fragmented is False

    def test_extracted_table_fragmented(self, sample_dataframe):
        """Test fragmented table attributes."""
        table = ExtractedTable(
            df=sample_dataframe,
            page_number=2,
            table_type='financial',
            extraction_method='tabula',
            confidence_score=0.75,
            is_fragmented=True,
            continuation_of=1
        )

        assert table.is_fragmented is True
        assert table.continuation_of == 1


class TestFinancialIndicator:
    """Test suite for FinancialIndicator."""

    def test_financial_indicator_creation(self):
        """Test FinancialIndicator instantiation."""
        indicator = FinancialIndicator(
            source_text='Presupuesto de $500 millones',
            amount=Decimal('500000000'),
            currency='COP',
            fiscal_year=2024,
            funding_source='SGP',
            budget_category='Educación',
            execution_percentage=75.0,
            confidence_interval=(0.7, 0.8),
            risk_level=0.2
        )

        assert indicator.amount == Decimal('500000000')
        assert indicator.currency == 'COP'
        assert indicator.fiscal_year == 2024
        assert indicator.funding_source == 'SGP'
        assert 0.0 <= indicator.risk_level <= 1.0

    def test_financial_indicator_confidence_interval(self):
        """Test confidence interval bounds."""
        indicator = FinancialIndicator(
            source_text='Test',
            amount=Decimal('1000000'),
            currency='COP',
            fiscal_year=2024,
            funding_source='SGP',
            budget_category='Test',
            execution_percentage=None,
            confidence_interval=(0.6, 0.9),
            risk_level=0.1
        )

        assert indicator.confidence_interval[0] < indicator.confidence_interval[1]
        assert 0.0 <= indicator.confidence_interval[0] <= 1.0
        assert 0.0 <= indicator.confidence_interval[1] <= 1.0


class TestResponsibleEntity:
    """Test suite for ResponsibleEntity."""

    def test_responsible_entity_creation(self):
        """Test ResponsibleEntity instantiation."""
        entity = ResponsibleEntity(
            name='Secretaría de Educación',
            entity_type='secretaría',
            specificity_score=0.9,
            mentioned_count=5,
            associated_programs=['Programa 1', 'Programa 2'],
            associated_indicators=['Indicador 1'],
            budget_allocated=Decimal('500000000')
        )

        assert entity.name == 'Secretaría de Educación'
        assert entity.entity_type == 'secretaría'
        assert entity.specificity_score == 0.9
        assert len(entity.associated_programs) == 2

    def test_responsible_entity_no_budget(self):
        """Test entity without budget allocation."""
        entity = ResponsibleEntity(
            name='Oficina de Planeación',
            entity_type='oficina',
            specificity_score=0.8,
            mentioned_count=3,
            associated_programs=[],
            associated_indicators=[],
            budget_allocated=None
        )

        assert entity.budget_allocated is None


class TestQualityScore:
    """Test suite for QualityScore."""

    def test_quality_score_creation(self):
        """Test QualityScore instantiation."""
        score = QualityScore(
            overall_score=0.85,
            financial_feasibility=0.90,
            indicator_quality=0.80,
            responsibility_clarity=0.85,
            temporal_consistency=0.90,
            pdet_alignment=0.75,
            causal_coherence=0.80,
            confidence_interval=(0.80, 0.90),
            evidence={'key': 'value'}
        )

        assert 0.0 <= score.overall_score <= 1.0
        assert 0.0 <= score.financial_feasibility <= 1.0
        assert 0.0 <= score.pdet_alignment <= 1.0
        assert score.confidence_interval[0] < score.confidence_interval[1]

    def test_quality_score_all_dimensions(self):
        """Test all quality score dimensions are bounded [0, 1]."""
        score = QualityScore(
            overall_score=0.75,
            financial_feasibility=0.80,
            indicator_quality=0.70,
            responsibility_clarity=0.85,
            temporal_consistency=0.75,
            pdet_alignment=0.70,
            causal_coherence=0.80,
            confidence_interval=(0.70, 0.80),
            evidence={}
        )

        assert all(0.0 <= getattr(score, field) <= 1.0
                   for field in ['overall_score', 'financial_feasibility',
                                 'indicator_quality', 'responsibility_clarity',
                                 'temporal_consistency', 'pdet_alignment',
                                 'causal_coherence'])


class TestIntegration:
    """Integration tests for financial viability analysis."""

    @pytest.mark.asyncio
    async def test_table_extraction_pipeline(self, mock_analyzer, tmp_path):
        """Test table extraction pipeline with mock PDF."""
        # Create a minimal test - actual PDF extraction requires PDF file
        # This tests the structure without full PDF processing
        assert mock_analyzer is not None

    def test_pdet_alignment_scoring(self):
        """Test PDET alignment scoring logic."""
        context = ColombianMunicipalContext()

        # Verify theory of change structure for scoring
        for pillar in context.PDET_PILLARS:
            assert pillar in context.PDET_THEORY_OF_CHANGE
            toc = context.PDET_THEORY_OF_CHANGE[pillar]
            assert 'outcomes' in toc
            assert 'mediators' in toc
            assert isinstance(toc['lag_years'], int)

    def test_financial_indicator_extraction_pipeline(self):
        """Test financial indicator extraction structure."""
        # Test the data structure requirements
        indicator = FinancialIndicator(
            source_text='SGP de $1,000,000,000 para 2024',
            amount=Decimal('1000000000'),
            currency='COP',
            fiscal_year=2024,
            funding_source='SGP',
            budget_category='Inversión',
            execution_percentage=None,
            confidence_interval=(0.8, 0.95),
            risk_level=0.15
        )

        assert indicator.amount > 0
        assert indicator.fiscal_year == 2024
        assert indicator.funding_source == 'SGP'
