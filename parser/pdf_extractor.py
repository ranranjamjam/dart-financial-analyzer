"""Extract tables and section text from DART business report PDFs."""

from __future__ import annotations

import re

import pandas as pd
import pdfplumber

SECTION_KEYWORDS: list[str] = [
    "I. 회사의 개요",
    "II. 사업의 내용",
    "III. 재무에 관한 사항",
    "IV. 이사의 경영진단 및 분석의견",
    "V. 감사인의 감사의견",
]


def extract_tables(pdf_path: str) -> list[pd.DataFrame]:
    """Open a PDF with pdfplumber, extract all tables, and return as DataFrames.

    Each table's first row is used as the column header.
    All-NA rows are dropped, and empty DataFrames are excluded.
    """
    dataframes: list[pd.DataFrame] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                if not table or len(table) < 2:
                    continue
                header = table[0]
                rows = table[1:]
                df = pd.DataFrame(rows, columns=header)
                df.dropna(how="all", inplace=True)
                if not df.empty:
                    dataframes.append(df)

    return dataframes


def extract_text_by_section(pdf_path: str) -> dict[str, str]:
    """Extract full text from a PDF and split it by DART section keywords.

    Returns a dict mapping each found section title to its body text.
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

    if not full_text.strip():
        return {}

    # Build a regex pattern that splits on any of the section keywords.
    escaped = [re.escape(kw) for kw in SECTION_KEYWORDS]
    pattern = "(" + "|".join(escaped) + ")"

    parts = re.split(pattern, full_text)

    sections: dict[str, str] = {}
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if part in SECTION_KEYWORDS:
            title = part
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections[title] = body
            i += 2
        else:
            i += 1

    return sections
