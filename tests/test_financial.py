"""재무 분석 모듈 테스트."""

from analyzer.financial import calculate_indicators, get_explanation


class TestCalculateIndicators:
    def test_operating_margin(self):
        data = {"매출액": 1000, "영업이익": 120}
        result = calculate_indicators(data)
        assert result["영업이익률"]["value"] == 12.0

    def test_debt_ratio(self):
        data = {"부채총계": 600, "자본총계": 400}
        result = calculate_indicators(data)
        assert result["부채비율"]["value"] == 150.0

    def test_current_ratio(self):
        data = {"유동자산": 500, "유동부채": 250}
        result = calculate_indicators(data)
        assert result["유동비율"]["value"] == 200.0

    def test_missing_data_returns_none(self):
        data = {"매출액": 1000}
        result = calculate_indicators(data)
        assert result["영업이익률"]["value"] is None

    def test_revenue_included(self):
        data = {"매출액": 5000}
        result = calculate_indicators(data)
        assert result["매출액"]["value"] == 5000

    def test_operating_cashflow(self):
        data = {"영업활동현금흐름": 300}
        result = calculate_indicators(data)
        assert result["영업활동 현금흐름"]["value"] == 300


class TestGetExplanation:
    def test_returns_three_keys(self):
        exp = get_explanation("영업이익률")
        assert "what" in exp
        assert "why" in exp
        assert "guide" in exp

    def test_unknown_indicator(self):
        exp = get_explanation("존재하지않는지표")
        assert exp is None
