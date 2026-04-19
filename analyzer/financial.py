"""재무 지표 계산 및 학습용 설명을 제공하는 모듈."""

EXPLANATIONS: dict[str, dict[str, str]] = {
    "매출액": {
        "what": "회사가 제품이나 서비스를 팔아서 번 총 금액입니다.",
        "why": "회사의 규모와 시장에서의 위치를 가장 직관적으로 보여주는 숫자입니다. 투자심사 시 '이 회사가 얼마나 큰 사업을 하고 있는가'를 먼저 파악합니다.",
        "guide": "단독으로 좋고 나쁨을 판단하기보다, 전년 대비 성장률과 동종업계 대비 규모를 함께 봅니다.",
    },
    "영업이익률": {
        "what": "매출에서 원가와 판매관리비를 빼고 남은 비율입니다. 본업으로 얼마나 효율적으로 벌고 있는지를 나타냅니다.",
        "why": "투자심사 시 '이 회사가 본업만으로 돈을 벌 수 있는 구조인가'를 판단하는 핵심 지표입니다. 일회성 이익이나 금융수익을 제외한 순수 사업 역량을 보여줍니다.",
        "guide": "10% 이상이면 일반적으로 양호합니다. 다만 업종마다 기준이 다릅니다 (IT/소프트웨어는 20%+ 가능, 제조업은 5~10%도 괜찮은 수준).",
    },
    "부채비율": {
        "what": "회사가 가진 자본 대비 빚이 얼마나 되는지를 나타냅니다. (부채 ÷ 자본 × 100)",
        "why": "회사의 재무 안정성을 보여주는 대표 지표입니다. 부채가 너무 많으면 이자 부담이 커지고, 경기 하락 시 위험해집니다.",
        "guide": "100% 이하면 안정적, 200% 이상이면 주의가 필요합니다. 업종 특성상 부채가 높은 경우(금융, 건설 등)도 있으니 업종 평균과 비교하세요.",
    },
    "유동비율": {
        "what": "1년 안에 현금화할 수 있는 자산이 1년 안에 갚아야 할 부채의 몇 배인지를 나타냅니다.",
        "why": "단기적으로 회사가 빚을 갚을 능력이 있는지를 보여줍니다. 이 비율이 낮으면 당장 현금이 부족해 흑자도산할 수 있습니다.",
        "guide": "200% 이상이면 안정적, 100% 미만이면 단기 유동성 위험이 있습니다.",
    },
    "영업활동 현금흐름": {
        "what": "회사가 본업(영업)을 통해 실제로 벌어들인 현금입니다. 손익계산서의 이익과 다를 수 있습니다.",
        "why": "이익은 회계적 수치이지만, 현금흐름은 실제 돈의 흐름입니다. 이익이 나도 현금이 안 들어오면 회사는 망할 수 있습니다. 투자심사에서 매우 중요합니다.",
        "guide": "양수(+)여야 정상입니다. 음수(-)가 지속되면 본업에서 현금을 못 벌고 있다는 뜻으로 위험 신호입니다.",
    },
}


def calculate_indicators(data: dict) -> dict:
    """재무 데이터로부터 5가지 핵심 지표를 계산한다.

    Args:
        data: 재무 항목명을 키로, 금액을 값으로 갖는 딕셔너리.

    Returns:
        각 지표명을 키로, {"value": ..., "unit": ...} 를 값으로 갖는 딕셔너리.
    """
    # 매출액
    revenue = data.get("매출액")

    # 영업이익률
    operating_income = data.get("영업이익")
    if revenue is not None and operating_income is not None and revenue != 0:
        operating_margin = round(operating_income / revenue * 100, 1)
    else:
        operating_margin = None

    # 부채비율
    total_debt = data.get("부채총계")
    total_equity = data.get("자본총계")
    if total_debt is not None and total_equity is not None and total_equity != 0:
        debt_ratio = round(total_debt / total_equity * 100, 1)
    else:
        debt_ratio = None

    # 유동비율
    current_assets = data.get("유동자산")
    current_liabilities = data.get("유동부채")
    if current_assets is not None and current_liabilities is not None and current_liabilities != 0:
        current_ratio = round(current_assets / current_liabilities * 100, 1)
    else:
        current_ratio = None

    # 영업활동 현금흐름
    operating_cashflow = data.get("영업활동현금흐름")

    return {
        "매출액": {"value": revenue, "unit": "원"},
        "영업이익률": {"value": operating_margin, "unit": "%"},
        "부채비율": {"value": debt_ratio, "unit": "%"},
        "유동비율": {"value": current_ratio, "unit": "%"},
        "영업활동 현금흐름": {"value": operating_cashflow, "unit": "원"},
    }


def get_explanation(indicator_name: str) -> dict | None:
    """지표에 대한 학습용 설명을 반환한다.

    Args:
        indicator_name: 지표명 (예: "영업이익률").

    Returns:
        {"what", "why", "guide"} 키를 가진 딕셔너리, 또는 알 수 없는 지표면 None.
    """
    return EXPLANATIONS.get(indicator_name)
