import pandas as pd

from parser.data_cleaner import clean_financial_table, parse_number


class TestParseNumber:
    def test_plain_number(self):
        assert parse_number("1234567") == 1234567

    def test_comma_separated(self):
        assert parse_number("1,234,567") == 1234567

    def test_negative_with_parentheses(self):
        assert parse_number("(1,234)") == -1234

    def test_negative_with_minus(self):
        assert parse_number("-1,234") == -1234

    def test_empty_returns_none(self):
        assert parse_number("") is None
        assert parse_number("-") is None

    def test_dash_variants_return_none(self):
        assert parse_number("―") is None
        assert parse_number("–") is None

    def test_whitespace(self):
        assert parse_number(" 1,234 ") == 1234

    def test_float_value(self):
        assert parse_number("1,234.56") == 1234.56

    def test_returns_int_when_possible(self):
        result = parse_number("1,234")
        assert result == 1234
        assert isinstance(result, int)

    def test_returns_float_when_decimal(self):
        result = parse_number("1,234.50")
        assert isinstance(result, float)


class TestCleanFinancialTable:
    def test_removes_empty_columns(self):
        df = pd.DataFrame({
            "항목": ["매출액", "영업이익"],
            "": [None, None],
            "당기": ["1,000", "200"],
        })
        result = clean_financial_table(df)
        assert "" not in result.columns

    def test_converts_numbers(self):
        df = pd.DataFrame({
            "항목": ["매출액"],
            "당기": ["1,234,567"],
        })
        result = clean_financial_table(df)
        assert result["당기"].iloc[0] == 1234567

    def test_first_column_preserved_as_string(self):
        df = pd.DataFrame({
            "항목": ["매출액"],
            "당기": ["1,000"],
        })
        result = clean_financial_table(df)
        assert result["항목"].iloc[0] == "매출액"

    def test_drops_all_none_rows(self):
        df = pd.DataFrame({
            "항목": ["매출액", "소계"],
            "당기": ["1,000", "-"],
            "전기": ["500", "―"],
        })
        result = clean_financial_table(df)
        assert len(result) == 1
        assert result["항목"].iloc[0] == "매출액"

    def test_resets_index(self):
        df = pd.DataFrame({
            "항목": ["매출액", "빈행", "영업이익"],
            "당기": ["1,000", "-", "200"],
        })
        result = clean_financial_table(df)
        assert list(result.index) == list(range(len(result)))
