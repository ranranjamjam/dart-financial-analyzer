"""Financial table data cleaner for DART filings."""

from __future__ import annotations

import re

import pandas as pd

# Characters treated as "no value"
_EMPTY_MARKERS = {"", "-", "―", "–"}


def parse_number(value: str) -> int | float | None:
    """Parse a Korean financial table number string.

    Rules:
    - Commas are removed: "1,234,567" -> 1234567
    - Parentheses mean negative: "(1,234)" -> -1234
    - Minus sign: "-1,234" -> -1234
    - Empty / dash variants -> None
    - Returns int when possible, float otherwise
    """
    text = value.strip()
    if text in _EMPTY_MARKERS:
        return None

    # Detect parenthesised negatives: (1,234)
    negative = False
    paren_match = re.fullmatch(r"\((.+)\)", text)
    if paren_match:
        text = paren_match.group(1)
        negative = True

    # Remove commas
    text = text.replace(",", "")

    try:
        num = float(text)
    except ValueError:
        return None

    if negative:
        num = -num

    # Return int when the value has no fractional part
    if num == int(num):
        return int(num)
    return num


def clean_financial_table(df: pd.DataFrame) -> pd.DataFrame:
    """Clean an extracted financial table DataFrame.

    Steps:
    1. Remove columns whose name is an empty string.
    2. Treat the first column as item names (preserve as-is).
    3. Apply ``parse_number`` to every cell in remaining columns.
    4. Drop rows where all numeric columns are None.
    5. Reset index.
    """
    # 1. Drop columns with empty-string names or None
    valid_cols = [c for c in df.columns if c is not None and str(c).strip() != ""]
    df = df[valid_cols].copy()

    # Deduplicate column names (PDF tables often have duplicate headers)
    seen: dict[str, int] = {}
    new_cols = []
    for c in df.columns:
        name = str(c)
        if name in seen:
            seen[name] += 1
            new_cols.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            new_cols.append(name)
    df.columns = new_cols

    # 2. Identify columns
    item_col = df.columns[0]
    numeric_cols = list(df.columns[1:])

    # 3. Convert numeric columns
    def _safe_parse(v):
        if v is None:
            return None
        s = str(v).strip()
        if s == "" or s == "nan" or s == "None":
            return None
        return parse_number(s)

    for col in numeric_cols:
        df[col] = df[col].apply(_safe_parse)

    # 4. Drop rows where every numeric column is None
    df = df.dropna(subset=numeric_cols, how="all")

    # 5. Reset index
    df = df.reset_index(drop=True)

    return df
