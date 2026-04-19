"""DART 사업보고서 재무 분석 Streamlit 대시보드."""

import tempfile
import os

import streamlit as st

from parser.pdf_extractor import extract_tables, extract_text_by_section
from parser.data_cleaner import clean_financial_table
from analyzer.summary import extract_key_values
from analyzer.financial import calculate_indicators, get_explanation

st.set_page_config(page_title="DART 재무 분석기", layout="wide")

st.title("DART 사업보고서 재무 분석기")
st.caption("DART에서 다운로드한 사업보고서 PDF를 업로드하면, 재무제표를 자동으로 추출하고 핵심 지표를 분석해 드립니다.")

uploaded_file = st.file_uploader("사업보고서 PDF 파일을 업로드하세요", type="pdf")

if uploaded_file is None:
    st.info("📂 DART(https://dart.fss.or.kr)에서 원하는 기업의 사업보고서를 PDF로 다운로드한 뒤 업로드해 주세요.")
else:
    tmp_path = None
    try:
        # Save uploaded PDF to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Extract and clean data
        raw_tables = extract_tables(tmp_path)
        sections = extract_text_by_section(tmp_path)
        cleaned_tables = [clean_financial_table(df) for df in raw_tables]

        if not cleaned_tables:
            st.warning("⚠️ PDF에서 표를 찾을 수 없습니다. DART 사업보고서 PDF인지 확인해 주세요.")
        else:
            tab1, tab2, tab3 = st.tabs(["📋 재무제표 원문", "📊 핵심 5대 지표", "💰 현금흐름 요약"])

            # ── Tab 1: 재무제표 원문 ──
            with tab1:
                st.header("재무제표 원문")
                st.markdown(
                    "사업보고서에서 추출한 재무제표 원문입니다.\n\n"
                    "- **재무상태표**: 특정 시점의 자산, 부채, 자본 현황\n"
                    "- **손익계산서**: 일정 기간의 수익과 비용, 이익 현황\n"
                    "- **현금흐름표**: 일정 기간의 현금 유입과 유출 현황"
                )

                for i, df in enumerate(cleaned_tables):
                    with st.expander(f"표 {i + 1}", expanded=(i < 3)):
                        st.dataframe(df, use_container_width=True)

                if sections:
                    st.subheader("본문 섹션")
                    for title, body in sections.items():
                        with st.expander(title):
                            display_text = body[:3000]
                            if len(body) > 3000:
                                display_text += "\n\n... (이하 생략)"
                            st.markdown(display_text)

            # ── Tab 2: 핵심 5대 지표 ──
            with tab2:
                st.header("핵심 5대 지표")

                key_values = extract_key_values(cleaned_tables)
                indicators = calculate_indicators(key_values)

                for name, info in indicators.items():
                    explanation = get_explanation(name)
                    with st.expander(f"📌 {name}", expanded=True):
                        value = info["value"]
                        unit = info["unit"]
                        if value is not None:
                            if unit == "원":
                                st.metric(label=name, value=f"{value:,.0f} {unit}")
                            else:
                                st.metric(label=name, value=f"{value} {unit}")
                        else:
                            st.metric(label=name, value="데이터 없음")

                        if explanation:
                            st.markdown(f"**🔍 이게 뭔가요?**\n\n{explanation['what']}")
                            st.markdown(f"**❗ 왜 중요한가요?**\n\n{explanation['why']}")
                            st.markdown(f"**📏 판단 기준**\n\n{explanation['guide']}")

            # ── Tab 3: 현금흐름 요약 ──
            with tab3:
                st.header("현금흐름 요약")
                st.markdown(
                    "현금흐름표는 기업의 현금이 어디서 들어오고 어디로 나가는지를 보여줍니다.\n\n"
                    "- **영업활동 현금흐름**: 본업에서 실제로 벌어들인 현금\n"
                    "- **투자활동 현금흐름**: 설비투자, 자산매각 등에 사용된 현금\n"
                    "- **재무활동 현금흐름**: 차입, 상환, 배당 등 자금조달 관련 현금"
                )

                ocf = indicators.get("영업활동 현금흐름", {}).get("value")
                if ocf is not None:
                    if ocf >= 0:
                        st.markdown(f"### 영업활동 현금흐름: :green[{ocf:,.0f} 원]")
                        st.success("✅ 영업활동 현금흐름이 양수입니다. 본업에서 현금을 창출하고 있습니다.")
                    else:
                        st.markdown(f"### 영업활동 현금흐름: :red[{ocf:,.0f} 원]")
                        st.error("⚠️ 영업활동 현금흐름이 음수입니다. 본업에서 현금이 유출되고 있어 주의가 필요합니다.")
                else:
                    st.info("영업활동 현금흐름 데이터를 찾을 수 없습니다.")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
