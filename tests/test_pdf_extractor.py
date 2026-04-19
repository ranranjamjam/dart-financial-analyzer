"""Tests for parser.pdf_extractor module."""

import os
import pytest
import pandas as pd

from parser.pdf_extractor import extract_tables, extract_text_by_section

SAMPLE_PDF = os.path.join(
    os.path.dirname(__file__), os.pardir, "data", "sample.pdf"
)


@pytest.fixture
def sample_pdf_path():
    path = os.path.normpath(SAMPLE_PDF)
    if not os.path.isfile(path):
        pytest.skip("data/sample.pdf not found — skipping PDF tests")
    return path


class TestExtractTables:
    def test_returns_list_of_dataframes(self, sample_pdf_path):
        result = extract_tables(sample_pdf_path)
        assert isinstance(result, list)
        for df in result:
            assert isinstance(df, pd.DataFrame)

    def test_dataframes_have_rows_and_columns(self, sample_pdf_path):
        result = extract_tables(sample_pdf_path)
        for df in result:
            assert len(df) > 0, "DataFrame should have at least one row"
            assert len(df.columns) > 0, "DataFrame should have at least one column"


class TestExtractTextBySection:
    def test_returns_dict(self, sample_pdf_path):
        result = extract_text_by_section(sample_pdf_path)
        assert isinstance(result, dict)

    def test_has_at_least_one_entry(self, sample_pdf_path):
        result = extract_text_by_section(sample_pdf_path)
        assert len(result) >= 1, "Should contain at least one section"

    def test_keys_and_values_are_strings(self, sample_pdf_path):
        result = extract_text_by_section(sample_pdf_path)
        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
