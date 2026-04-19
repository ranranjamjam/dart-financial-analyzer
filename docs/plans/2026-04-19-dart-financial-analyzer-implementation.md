# DART 사업보고서 재무 분석기 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** DART 사업보고서 PDF를 업로드하면 재무제표를 파싱하고, 핵심 5대 지표를 학습 카드 형태로 보여주는 Streamlit 대시보드를 만든다.

**Architecture:** PDF → pdfplumber로 표/텍스트 추출 → pandas DataFrame으로 정제 → 재무 비율 계산 → Streamlit 대시보드에 학습 해설과 함께 표시. 파싱/정제/분석/표시가 모듈별로 분리되어 향후 LLM 연동이 가능한 구조.

**Tech Stack:** Python 3.10+, pdfplumber, pandas, streamlit, plotly

---

### Task 1: 프로젝트 초기 세팅

**Files:**
- Create: `requirements.txt`
- Create: `parser/__init__.py`
- Create: `analyzer/__init__.py`
- Create: `data/.gitkeep`

**Step 1: 프로젝트 디렉토리 구조 생성**

```bash
cd dart-financial-analyzer
mkdir -p parser analyzer data
touch parser/__init__.py analyzer/__init__.py data/.gitkeep
```

**Step 2: requirements.txt 작성**

```text
pdfplumber==0.11.4
pandas==2.2.3
streamlit==1.41.1
plotly==5.24.1
openpyxl==3.1.5
```

**Step 3: 가상환경 생성 및 의존성 설치**

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

Expected: 모든 패키지 설치 성공

**Step 4: git 초기화 및 커밋**

```bash
git init
echo "venv/" > .gitignore
echo "data/*.pdf" >> .gitignore
echo "data/*.csv" >> .gitignore
echo "__pycache__/" >> .gitignore
git add .
git commit -m "chore: init project structure with dependencies"
```

---

### Task 2: PDF 텍스트 추출기

**Files:**
- Create: `parser/pdf_extractor.py`
- Create: `tests/test_pdf_extractor.py`

**Step 1: 테스트용 샘플 PDF 준비**

DART에서 아무 기업의 사업보고서 PDF를 하나 다운받아 `data/sample.pdf`에 저장.
(테스트에서는 이 파일이 있다고 가정)

**Step 2: 실패하는 테스트 작성**

```python
# tests/test_pdf_extractor.py
import pytest
from parser.pdf_extractor import extract_tables, extract_text_by_section

class TestExtractTables:
    def test_returns_list_of_dataframes(self, sample_pdf_path):
        tables = extract_tables(sample_pdf_path)
        assert isinstance(tables, list)
        assert len(tables) > 0

    def test_dataframe_has_rows_and_columns(self, sample_pdf_path):
        tables = extract_tables(sample_pdf_path)
        for df in tables:
            assert len(df) > 0
            assert len(df.columns) > 0

class TestExtractTextBySection:
    def test_returns_dict(self, sample_pdf_path):
        sections = extract_text_by_section(sample_pdf_path)
        assert isinstance(sections, dict)

    def test_contains_known_sections(self, sample_pdf_path):
        sections = extract_text_by_section(sample_pdf_path)
        # 최소한 하나 이상의 섹션이 추출되어야 함
        assert len(sections) > 0

@pytest.fixture
def sample_pdf_path():
    """data/sample.pdf가 있어야 테스트 실행 가능"""
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "data", "sample.pdf")
    if not os.path.exists(path):
        pytest.skip("data/sample.pdf not found - download a DART report first")
    return path
```

**Step 3: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_pdf_extractor.py -v
```

Expected: ImportError (모듈 없음)

**Step 4: 구현**

```python
# parser/pdf_extractor.py
import pdfplumber
import pandas as pd

# DART 사업보고서의 주요 섹션 키워드
SECTION_KEYWORDS = [
    "I. 회사의 개요",
    "II. 사업의 내용",
    "III. 재무에 관한 사항",
    "IV. 이사의 경영진단 및 분석의견",
    "V. 감사인의 감사의견",
]


def extract_tables(pdf_path: str) -> list[pd.DataFrame]:
    """PDF에서 모든 테이블을 추출하여 DataFrame 리스트로 반환한다."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                for table in page_tables:
                    if len(table) > 1:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df = df.dropna(how="all")
                        if not df.empty:
                            tables.append(df)
    return tables


def extract_text_by_section(pdf_path: str) -> dict[str, str]:
    """PDF 전체 텍스트를 추출한 뒤, 섹션 키워드로 구분하여 dict로 반환한다."""
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    sections = {}
    for i, keyword in enumerate(SECTION_KEYWORDS):
        start = full_text.find(keyword)
        if start == -1:
            continue
        # 다음 섹션 키워드 위치를 찾아서 현재 섹션의 끝으로 사용
        end = len(full_text)
        for next_keyword in SECTION_KEYWORDS[i + 1:]:
            next_start = full_text.find(next_keyword)
            if next_start != -1:
                end = next_start
                break
        sections[keyword] = full_text[start:end].strip()

    return sections
```

**Step 5: 테스트 실행 → 통과 확인**

```bash
pytest tests/test_pdf_extractor.py -v
```

Expected: sample.pdf가 있으면 PASS, 없으면 SKIP

**Step 6: 커밋**

```bash
git add parser/pdf_extractor.py tests/test_pdf_extractor.py
git commit -m "feat: add PDF table and section text extractor"
```

---

### Task 3: 데이터 정제 모듈

**Files:**
- Create: `parser/data_cleaner.py`
- Create: `tests/test_data_cleaner.py`

**Step 1: 실패하는 테스트 작성**

```python
# tests/test_data_cleaner.py
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

    def test_whitespace(self):
        assert parse_number(" 1,234 ") == 1234


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
```

**Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_data_cleaner.py -v
```

Expected: ImportError

**Step 3: 구현**

```python
# parser/data_cleaner.py
import re
import pandas as pd


def parse_number(value: str) -> int | float | None:
    """재무제표 숫자 문자열을 파싱한다.
    '1,234,567' → 1234567
    '(1,234)' → -1234
    '-' → None
    """
    if not isinstance(value, str):
        return None

    value = value.strip()
    if value in ("", "-", "―", "–"):
        return None

    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1]

    value = value.replace(",", "").replace(" ", "")

    try:
        number = float(value)
        if number == int(number):
            number = int(number)
        return -number if negative else number
    except ValueError:
        return None


def clean_financial_table(df: pd.DataFrame) -> pd.DataFrame:
    """추출된 재무제표 DataFrame을 정제한다."""
    # 빈 컬럼명 제거
    df = df.loc[:, df.columns.astype(str).str.strip() != ""]

    # 첫 번째 컬럼(항목명)을 제외한 나머지 컬럼의 숫자를 파싱
    first_col = df.columns[0]
    for col in df.columns[1:]:
        df[col] = df[col].apply(parse_number)

    # 모든 숫자 컬럼이 None인 행 제거
    numeric_cols = [c for c in df.columns if c != first_col]
    df = df.dropna(subset=numeric_cols, how="all")

    return df.reset_index(drop=True)
```

**Step 4: 테스트 실행 → 통과 확인**

```bash
pytest tests/test_data_cleaner.py -v
```

Expected: PASS

**Step 5: 커밋**

```bash
git add parser/data_cleaner.py tests/test_data_cleaner.py
git commit -m "feat: add financial table data cleaner with number parser"
```

---

### Task 4: 재무 분석 모듈

**Files:**
- Create: `analyzer/financial.py`
- Create: `tests/test_financial.py`

**Step 1: 실패하는 테스트 작성**

```python
# tests/test_financial.py
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
        data = {"매출액": 1000}  # 영업이익 없음
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
```

**Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_financial.py -v
```

Expected: ImportError

**Step 3: 구현**

```python
# analyzer/financial.py

EXPLANATIONS = {
    "매출액": {
        "what": "회사가 제품이나 서비스를 팔아서 번 총 금액입니다.",
        "why": "회사의 규모와 시장에서의 위치를 가장 직관적으로 보여주는 숫자입니다. "
               "투자심사 시 '이 회사가 얼마나 큰 사업을 하고 있는가'를 먼저 파악합니다.",
        "guide": "단독으로 좋고 나쁨을 판단하기보다, 전년 대비 성장률과 동종업계 대비 규모를 함께 봅니다.",
    },
    "영업이익률": {
        "what": "매출에서 원가와 판매관리비를 빼고 남은 비율입니다. 본업으로 얼마나 효율적으로 벌고 있는지를 나타냅니다.",
        "why": "투자심사 시 '이 회사가 본업만으로 돈을 벌 수 있는 구조인가'를 판단하는 핵심 지표입니다. "
               "일회성 이익이나 금융수익을 제외한 순수 사업 역량을 보여줍니다.",
        "guide": "10% 이상이면 일반적으로 양호합니다. 다만 업종마다 기준이 다릅니다 "
                 "(IT/소프트웨어는 20%+ 가능, 제조업은 5~10%도 괜찮은 수준).",
    },
    "부채비율": {
        "what": "회사가 가진 자본 대비 빚이 얼마나 되는지를 나타냅니다. (부채 ÷ 자본 × 100)",
        "why": "회사의 재무 안정성을 보여주는 대표 지표입니다. "
               "부채가 너무 많으면 이자 부담이 커지고, 경기 하락 시 위험해집니다.",
        "guide": "100% 이하면 안정적, 200% 이상이면 주의가 필요합니다. "
                 "업종 특성상 부채가 높은 경우(금융, 건설 등)도 있으니 업종 평균과 비교하세요.",
    },
    "유동비율": {
        "what": "1년 안에 현금화할 수 있는 자산이 1년 안에 갚아야 할 부채의 몇 배인지를 나타냅니다.",
        "why": "단기적으로 회사가 빚을 갚을 능력이 있는지를 보여줍니다. "
               "이 비율이 낮으면 당장 현금이 부족해 흑자도산할 수 있습니다.",
        "guide": "200% 이상이면 안정적, 100% 미만이면 단기 유동성 위험이 있습니다.",
    },
    "영업활동 현금흐름": {
        "what": "회사가 본업(영업)을 통해 실제로 벌어들인 현금입니다. 손익계산서의 이익과 다를 수 있습니다.",
        "why": "이익은 회계적 수치이지만, 현금흐름은 실제 돈의 흐름입니다. "
               "이익이 나도 현금이 안 들어오면 회사는 망할 수 있습니다. 투자심사에서 매우 중요합니다.",
        "guide": "양수(+)여야 정상입니다. 음수(-)가 지속되면 본업에서 현금을 못 벌고 있다는 뜻으로 위험 신호입니다.",
    },
}


def calculate_indicators(data: dict) -> dict:
    """핵심 재무 데이터로부터 5대 지표를 계산한다.

    Args:
        data: 재무 항목명 → 숫자 매핑. 예: {"매출액": 1000, "영업이익": 120, ...}

    Returns:
        지표명 → {"value": 계산값, "unit": 단위} 매핑
    """
    indicators = {}

    # 매출액
    revenue = data.get("매출액")
    indicators["매출액"] = {
        "value": revenue,
        "unit": "원",
    }

    # 영업이익률
    operating_income = data.get("영업이익")
    if revenue and operating_income:
        margin = round(operating_income / revenue * 100, 1)
    else:
        margin = None
    indicators["영업이익률"] = {
        "value": margin,
        "unit": "%",
    }

    # 부채비율
    total_debt = data.get("부채총계")
    total_equity = data.get("자본총계")
    if total_debt is not None and total_equity:
        debt_ratio = round(total_debt / total_equity * 100, 1)
    else:
        debt_ratio = None
    indicators["부채비율"] = {
        "value": debt_ratio,
        "unit": "%",
    }

    # 유동비율
    current_assets = data.get("유동자산")
    current_liabilities = data.get("유동부채")
    if current_assets is not None and current_liabilities:
        current_ratio = round(current_assets / current_liabilities * 100, 1)
    else:
        current_ratio = None
    indicators["유동비율"] = {
        "value": current_ratio,
        "unit": "%",
    }

    # 영업활동 현금흐름
    operating_cf = data.get("영업활동현금흐름")
    indicators["영업활동 현금흐름"] = {
        "value": operating_cf,
        "unit": "원",
    }

    return indicators


def get_explanation(indicator_name: str) -> dict | None:
    """지표에 대한 학습용 해설을 반환한다."""
    return EXPLANATIONS.get(indicator_name)
```

**Step 4: 테스트 실행 → 통과 확인**

```bash
pytest tests/test_financial.py -v
```

Expected: PASS

**Step 5: 커밋**

```bash
git add analyzer/financial.py tests/test_financial.py
git commit -m "feat: add financial indicator calculator with learning explanations"
```

---

### Task 5: 핵심 지표 요약 모듈

**Files:**
- Create: `analyzer/summary.py`
- Create: `tests/test_summary.py`

**Step 1: 실패하는 테스트 작성**

```python
# tests/test_summary.py
import pandas as pd
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
        """'매출액(수익)' 같은 변형도 매칭되어야 함"""
        df = pd.DataFrame({
            "항목": ["매출액(수익)", "영업이익(손실)"],
            "당기": [5000, 300],
        })
        result = extract_key_values([df])
        assert result.get("매출액") == 5000
        assert result.get("영업이익") == 300
```

**Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_summary.py -v
```

Expected: ImportError

**Step 3: 구현**

```python
# analyzer/summary.py
import pandas as pd

# 핵심 재무 항목 → 매칭 키워드 목록
KEY_ITEMS = {
    "매출액": ["매출액", "수익"],
    "영업이익": ["영업이익"],
    "당기순이익": ["당기순이익", "당기순손익"],
    "자산총계": ["자산총계"],
    "부채총계": ["부채총계"],
    "자본총계": ["자본총계"],
    "유동자산": ["유동자산"],
    "유동부채": ["유동부채"],
    "영업활동현금흐름": ["영업활동", "영업활동으로 인한"],
}


def extract_key_values(tables: list[pd.DataFrame]) -> dict:
    """여러 재무제표 DataFrame에서 핵심 항목의 값을 추출한다.

    첫 번째 컬럼을 항목명, 두 번째 숫자 컬럼을 당기 값으로 간주한다.

    Returns:
        항목명 → 숫자 매핑. 예: {"매출액": 1000000, "영업이익": 120000}
    """
    result = {}

    for df in tables:
        if df.empty or len(df.columns) < 2:
            continue

        item_col = df.columns[0]
        # 첫 번째 숫자 컬럼 찾기
        value_col = None
        for col in df.columns[1:]:
            if pd.api.types.is_numeric_dtype(df[col]):
                value_col = col
                break
        # 숫자 컬럼이 없으면 두 번째 컬럼 시도
        if value_col is None:
            value_col = df.columns[1]

        for _, row in df.iterrows():
            cell = str(row[item_col]).strip() if pd.notna(row[item_col]) else ""
            for key, keywords in KEY_ITEMS.items():
                if key in result:
                    continue
                for keyword in keywords:
                    if keyword in cell:
                        val = row[value_col]
                        if pd.notna(val):
                            result[key] = val
                        break

    return result
```

**Step 4: 테스트 실행 → 통과 확인**

```bash
pytest tests/test_summary.py -v
```

Expected: PASS

**Step 5: 커밋**

```bash
git add analyzer/summary.py tests/test_summary.py
git commit -m "feat: add key financial value extractor from parsed tables"
```

---

### Task 6: Streamlit 대시보드

**Files:**
- Create: `app.py`

**Step 1: 메인 앱 구현**

```python
# app.py
import streamlit as st
import pandas as pd
from parser.pdf_extractor import extract_tables, extract_text_by_section
from parser.data_cleaner import clean_financial_table
from analyzer.summary import extract_key_values
from analyzer.financial import calculate_indicators, get_explanation


st.set_page_config(page_title="DART 재무 분석기", layout="wide")
st.title("DART 사업보고서 재무 분석기")
st.caption("사업보고서 PDF를 업로드하면 재무제표를 분석하고, 핵심 지표를 학습할 수 있습니다.")

uploaded_file = st.file_uploader("사업보고서 PDF 업로드", type=["pdf"])

if uploaded_file is None:
    st.info("DART(dart.fss.or.kr)에서 사업보고서 PDF를 다운로드한 뒤 업로드해주세요.")
    st.stop()

# PDF를 임시 파일로 저장
import tempfile, os
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    tmp.write(uploaded_file.read())
    tmp_path = tmp.name

try:
    # 파싱
    with st.spinner("PDF를 분석하고 있습니다..."):
        raw_tables = extract_tables(tmp_path)
        sections = extract_text_by_section(tmp_path)

    if not raw_tables:
        st.warning("PDF에서 표를 찾지 못했습니다. 다른 사업보고서를 시도해보세요.")
        st.stop()

    # 정제
    cleaned_tables = [clean_financial_table(df) for df in raw_tables]

    # 탭 구성
    tab1, tab2, tab3 = st.tabs([
        "📋 재무제표 원문",
        "📊 핵심 5대 지표",
        "💰 현금흐름 요약",
    ])

    # ─── Tab 1: 재무제표 원문 ───
    with tab1:
        st.header("재무제표 원문")
        st.markdown(
            "> 아래는 사업보고서에서 추출한 표입니다. "
            "**재무상태표**는 회사의 재산 목록, "
            "**손익계산서**는 얼마 벌고 썼는지, "
            "**현금흐름표**는 실제 현금 흐름을 보여줍니다."
        )
        for i, df in enumerate(cleaned_tables):
            with st.expander(f"표 {i + 1} ({len(df)}행)", expanded=(i < 3)):
                st.dataframe(df, use_container_width=True)

        # 텍스트 섹션
        if sections:
            st.subheader("사업보고서 주요 섹션")
            for title, text in sections.items():
                with st.expander(title):
                    st.text(text[:3000])  # 너무 긴 텍스트는 잘라서 표시

    # ─── Tab 2: 핵심 5대 지표 ───
    with tab2:
        st.header("핵심 5대 지표")
        st.markdown(
            "> 투자심사역이 기업을 처음 볼 때 확인하는 5가지 핵심 지표입니다. "
            "각 카드를 펼쳐서 의미를 학습해보세요."
        )

        key_values = extract_key_values(cleaned_tables)
        indicators = calculate_indicators(key_values)

        for name, info in indicators.items():
            value = info["value"]
            unit = info["unit"]

            if value is not None:
                if unit == "원":
                    display = f"{value:,.0f} {unit}"
                else:
                    display = f"{value} {unit}"
            else:
                display = "데이터를 찾지 못했습니다"

            with st.expander(f"**{name}**: {display}"):
                exp = get_explanation(name)
                if exp:
                    st.markdown(f"**이게 뭔가요?**\n\n{exp['what']}")
                    st.markdown(f"**왜 중요한가요?**\n\n{exp['why']}")
                    st.markdown(f"**판단 기준**\n\n{exp['guide']}")

    # ─── Tab 3: 현금흐름 요약 ───
    with tab3:
        st.header("현금흐름 요약")
        st.markdown(
            "> 현금흐름표는 회사에 실제로 돈이 들어오고 나가는 흐름을 보여줍니다.\n\n"
            "- **영업활동**: 본업으로 번 현금 (양수가 정상)\n"
            "- **투자활동**: 설비·자산에 쓴 현금 (음수가 일반적 — 투자하고 있다는 뜻)\n"
            "- **재무활동**: 빌리거나 갚은 현금 (차입 vs 상환 패턴 확인)"
        )

        cf_items = {
            "영업활동현금흐름": key_values.get("영업활동현금흐름"),
        }

        if cf_items["영업활동현금흐름"] is not None:
            val = cf_items["영업활동현금흐름"]
            color = "green" if val > 0 else "red"
            sign = "+" if val > 0 else ""
            st.markdown(
                f"**영업활동 현금흐름**: "
                f":{color}[{sign}{val:,.0f} 원]"
            )
            if val > 0:
                st.success("본업에서 현금을 벌어들이고 있습니다. 긍정적 신호입니다.")
            else:
                st.error("본업에서 현금이 유출되고 있습니다. 원인 파악이 필요합니다.")
        else:
            st.info("현금흐름 데이터를 추출하지 못했습니다.")

finally:
    os.unlink(tmp_path)
```

**Step 2: 로컬에서 실행 테스트**

```bash
streamlit run app.py
```

Expected: 브라우저에서 대시보드가 열리고, PDF 업로드 UI가 표시됨

**Step 3: 실제 DART PDF 업로드하여 동작 확인**

- PDF 업로드 후 3개 탭 모두 정상 표시되는지 확인
- 지표 학습 카드가 펼쳐지는지 확인
- 표를 못 찾은 경우 경고 메시지가 나오는지 확인

**Step 4: 커밋**

```bash
git add app.py
git commit -m "feat: add Streamlit dashboard with learning-focused financial analysis"
```

---

### Task 7: 최종 정리 및 테스트

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: 테스트 설정 파일**

```python
# tests/__init__.py
# (빈 파일)
```

```python
# tests/conftest.py
import os
import pytest

@pytest.fixture
def sample_pdf_path():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "sample.pdf")
    if not os.path.exists(path):
        pytest.skip("data/sample.pdf not found")
    return path
```

**Step 2: conftest로 fixture 통합 후 test_pdf_extractor.py에서 중복 fixture 제거**

`tests/test_pdf_extractor.py`에서 `sample_pdf_path` fixture를 삭제 (conftest.py에서 공유).

**Step 3: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: 모든 테스트 PASS (sample.pdf 없으면 PDF 관련은 SKIP)

**Step 4: 커밋**

```bash
git add tests/
git commit -m "chore: add shared test fixtures and clean up test structure"
```
