import pandas as pd
import pytest

from analyzer.summary import extract_key_values


class TestExtractKeyValues:
    def test_extracts_revenue(self):
        df = pd.DataFrame({
            "항목": ["매출액", "매출원가", "매출총이익"],
            "당기": [1000000, 600000, 400000],
        })
        result = extract_key_values([df])
        assert result.get("매출액") == 1000000

    def test_extracts_operating_income(self):
        df = pd.DataFrame({
            "항목": ["매출액", "영업이익"],
            "당기": [1000000, 120000],
        })
        result = extract_key_values([df])
        assert result.get("영업이익") == 120000

    def test_handles_no_match(self):
        df = pd.DataFrame({
            "항목": ["기타항목"],
            "당기": [999],
        })
        result = extract_key_values([df])
        assert result.get("매출액") is None

    def test_handles_partial_match(self):
        df = pd.DataFrame({
            "항목": ["매출액(수익)", "영업이익(손실)"],
            "당기": [5000, 300],
        })
        result = extract_key_values([df])
        assert result.get("매출액") == 5000
        assert result.get("영업이익") == 300
