"""
Tests for CPP table extraction None value handling.

This test module validates the fixes for handling None values in table cells
during KPI and budget extraction.

OBSOLETE: cpp_ingestion.tables module no longer exists.
Table extraction functionality has been refactored/removed in SPC migration.
"""

import pytest

pytestmark = pytest.mark.skip(reason="obsolete - cpp_ingestion.tables module removed during SPC refactor")

# Old import (no longer valid):
# from saaaaaa.processing.cpp_ingestion.tables import TableExtractor


class TestTableExtractionNoneHandling:
    """Test suite for None value handling in table extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create a TableExtractor instance."""
        return TableExtractor()
    
    def test_extract_kpis_with_none_values(self, extractor):
        """Test KPI extraction with None values in cells."""
        table = {
            "table_id": "test_table_1",
            "page": 1,
            "headers": ["indicador", "línea base", "meta", "unidad", "año"],
            "data_rows": [
                ["Tasa de cobertura", "85%", "95%", "%", "2028"],
                [None, "100", "150", None, "2027"],  # None values
                ["Población atendida", None, "5000", "personas", None],  # More None values
                [None, None, None, None, None],  # All None
            ],
        }
        
        kpis = extractor._extract_kpis(table)
        
        # Should extract KPIs even with None values
        assert len(kpis) >= 2, "Should extract at least 2 KPIs with valid data"
        
        # First row - all values present
        kpi1 = kpis[0]
        assert kpi1["indicator"] == "Tasa de cobertura"
        assert kpi1["unit"] == "%"
        
        # Second row - None indicator should use first non-empty cell or "Unknown"
        kpi2 = kpis[1]
        assert kpi2["indicator"] in ["100", "Unknown"]  # Should handle None gracefully
        
        # Third row - None baseline and year should not cause errors
        kpi3 = kpis[2]
        assert kpi3["indicator"] == "Población atendida"
        assert kpi3.get("unit", "") == "personas"
    
    def test_extract_budgets_with_none_values(self, extractor):
        """Test budget extraction with None values in cells."""
        table = {
            "table_id": "budget_table_1",
            "page": 2,
            "headers": ["fuente", "uso", "monto", "año"],
            "data_rows": [
                ["SGP Educación", "Infraestructura", "$5,000,000,000", "2024"],
                [None, "Docentes", "$2,000,000,000", None],  # None values
                ["Regalías", None, None, "2025"],  # None use and amount
                [None, None, None, None],  # All None
            ],
        }
        
        budgets = extractor._extract_budgets(table)
        
        # Should extract budgets even with None values
        assert len(budgets) >= 2, "Should extract at least 2 budgets with valid data"
        
        # First row - all values present
        budget1 = budgets[0]
        assert budget1["source"] == "SGP Educación"
        assert budget1["use"] == "Infraestructura"
        
        # Second row - None source should default to "Unknown"
        budget2 = budgets[1]
        assert budget2["source"] == "Unknown"
        assert budget2["use"] == "Docentes"
        
        # Third row - None values should not cause AttributeError
        budget3 = budgets[2]
        assert budget3["source"] == "Regalías"
        # None use should be handled gracefully
    
    def test_extract_kpis_empty_cells_in_row(self, extractor):
        """Test KPI extraction with empty strings and None mixed."""
        table = {
            "table_id": "mixed_table",
            "page": 1,
            "headers": ["indicador", "baseline", "target"],
            "data_rows": [
                ["", None, "100"],  # Empty string and None
                [None, "", None],  # None and empty string
                ["Valid Indicator", None, None],  # Valid indicator with None values
            ],
        }
        
        kpis = extractor._extract_kpis(table)
        
        # Should handle mixed empty/None values without errors
        assert isinstance(kpis, list)
        
        # Should extract at least the row with valid indicator
        valid_kpis = [kpi for kpi in kpis if kpi.get("indicator") == "Valid Indicator"]
        assert len(valid_kpis) == 1
    
    def test_extract_budgets_no_strip_error(self, extractor):
        """Test that None values don't cause AttributeError: 'NoneType' object has no attribute 'strip'."""
        table = {
            "table_id": "none_test",
            "page": 1,
            "headers": ["fuente", "uso", "monto"],
            "data_rows": [
                [None, None, None],
                [None, "Valid Use", "$1000"],
                ["Valid Source", None, "$2000"],
            ],
        }
        
        # This should not raise AttributeError
        try:
            budgets = extractor._extract_budgets(table)
            assert isinstance(budgets, list)
            # Should have extracted some budgets with valid data
            assert len(budgets) >= 1
        except AttributeError as e:
            if "'NoneType' object has no attribute 'strip'" in str(e):
                pytest.fail("None value handling failed - AttributeError on .strip()")
            raise
    
    def test_year_extraction_with_none(self, extractor):
        """Test year extraction when cell value is None."""
        table = {
            "table_id": "year_test",
            "page": 1,
            "headers": ["indicador", "año"],
            "data_rows": [
                ["Indicator 1", "2024"],  # Valid year
                ["Indicator 2", None],  # None year
                ["Indicator 3", ""],  # Empty year
                ["Indicator 4", "No year here"],  # Invalid year format
            ],
        }
        
        kpis = extractor._extract_kpis(table)
        
        # Should handle None/empty/invalid years without errors
        assert len(kpis) == 4
        
        # First should have year
        assert kpis[0].get("year") == 2024
        
        # Others should not have year or should handle gracefully
        for i in range(1, 4):
            # Should not raise error and year should be None or not present
            year = kpis[i].get("year")
            assert year is None or isinstance(year, int)
    
    def test_parse_numeric_with_none(self, extractor):
        """Test _parse_numeric helper with None input."""
        # Should handle None without errors
        result = extractor._parse_numeric(None)
        assert result is None or result == 0.0
        
        # Should handle empty string
        result = extractor._parse_numeric("")
        assert result is None or result == 0.0
        
        # Should still parse valid numbers
        result = extractor._parse_numeric("85%")
        assert result is not None
        assert result > 0
    
    def test_parse_currency_with_none(self, extractor):
        """Test _parse_currency helper with None input."""
        # Should handle None without errors
        result = extractor._parse_currency(None)
        assert result is None
        
        # Should handle empty string
        result = extractor._parse_currency("")
        assert result is None
        
        # Should still parse valid currency
        result = extractor._parse_currency("$5,000,000")
        assert result is not None
        assert result > 0


class TestTableExtractionIntegration:
    """Integration tests for table extraction with real-world scenarios."""
    
    @pytest.fixture
    def extractor(self):
        """Create a TableExtractor instance."""
        return TableExtractor()
    
    def test_extract_from_raw_objects_with_none_cells(self, extractor):
        """Test extract method with raw_objects containing None values."""
        raw_objects = {
            "pages": [
                {
                    "page_number": 1,
                    "tables": [
                        {
                            "table_id": "table_1",
                            "page": 1,
                            "headers": ["Indicador", "Meta"],
                            "rows": [
                                ["Indicador", "Meta"],  # Header row
                                ["Cobertura", "95%"],
                                [None, "100"],  # None cell
                                ["Población", None],  # None cell
                            ],
                        }
                    ],
                }
            ]
        }
        
        # This should not raise AttributeError
        try:
            result = extractor.extract(raw_objects)
            assert isinstance(result, dict)
            assert "tables" in result
            assert "kpis" in result
            assert "budgets" in result
        except AttributeError as e:
            if "'NoneType' object has no attribute 'strip'" in str(e):
                pytest.fail("Integration test failed - None handling issue")
            raise
