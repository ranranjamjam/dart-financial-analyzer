"""핵심 재무 지표 요약 모듈."""

from __future__ import annotations

import pandas as pd

KEY_ITEMS: dict[str, list[str]] = {
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
    """Scan multiple financial table DataFrames to find key financial items.

    The first column of each DataFrame is treated as item names.
    The first numeric column (or the second column if none is numeric)
    is used as the value column.

    Returns a dict mapping key item names to their first matched value.
    """
    result: dict[str, object] = {}

    for df in tables:
        if df.empty or len(df.columns) < 2:
            continue

        item_col = df.columns[0]

        # Find first numeric column (skip the item name column)
        value_col = None
        for col in df.columns[1:]:
            if pd.api.types.is_numeric_dtype(df[col]):
                value_col = col
                break
        if value_col is None:
            value_col = df.columns[1]

        for _, row in df.iterrows():
            item_name = str(row[item_col])
            for key, keywords in KEY_ITEMS.items():
                if key in result:
                    continue
                for kw in keywords:
                    if kw in item_name:
                        result[key] = row[value_col]
                        break

    return result
