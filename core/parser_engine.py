import unicodedata
import warnings
from typing import Tuple, List

import pandas as pd
import numpy as np


def _to_datetime_safe(series, **kwargs):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Could not infer format",
            category=UserWarning,
        )
        return pd.to_datetime(series, **kwargs)

SENTINELS = ["N/A", "n/a", "-", "null", "NULL", "None", "none", "", "nan", "NaN"]


class ParserEngine:
    def parse(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        log = []
        df = df.copy()

        str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

        # Step 1: Strip whitespace
        for col in str_cols:
            df[col] = df[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        log.append("[Parser] Stripped whitespace from string columns")

        # Step 2: Detect and replace sentinel nulls
        null_before = df.isnull().sum().sum()
        for col in str_cols:
            df[col] = df[col].replace(SENTINELS, None)
        null_after = df.isnull().sum().sum()
        additional = null_after - null_before
        if additional > 0:
            log.append(
                f"[Parser] Identified {additional} additional null values from sentinel strings"
            )

        # Step 3: Remove duplicate rows
        n_before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        n_removed = n_before - len(df)
        if n_removed > 0:
            log.append(f"[Parser] Removed {n_removed} duplicate rows")

        # Step 4: Infer types
        for col in df.columns:
            if col in str_cols:
                df[col] = self._infer_type(df[col])

        # Step 5: Normalize Vietnamese diacritics
        df = self._normalize_str_columns(df)
        log.append("[Parser] Normalized Vietnamese diacritics (Unicode NFC)")

        # Step 6: Parse dates
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = self._parse_dates(df[col])

        return df, log

    def _normalize_str_columns(self, df):
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].apply(
                lambda x: self._normalize_vn(x) if isinstance(x, str) else x
            )
        return df

    def _infer_type(self, series):
        non_null = series.dropna()
        if len(non_null) == 0:
            return series
        try:
            numeric = pd.to_numeric(non_null, errors="coerce")
            if numeric.notna().sum() / len(non_null) >= 0.8:
                return pd.to_numeric(series, errors="coerce")
        except Exception:
            pass
        return series

    def _normalize_vn(self, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        nfd = unicodedata.normalize("NFD", text)
        chars = list(nfd)
        vowels_set = set("aeiouyAEIOUY")
        tone_cps = {0x0300, 0x0301, 0x0303, 0x0309, 0x0323}
        quality_cps = {0x0302, 0x0306, 0x031B}
        all_combining = tone_cps | quality_cps

        i = 0
        result = []
        while i < len(chars):
            c = chars[i]
            cp = ord(c) if len(c) == 1 else 0

            if c in vowels_set:
                cluster = []
                while i < len(chars):
                    nc = chars[i]
                    ncp = ord(nc) if len(nc) == 1 else 0
                    if nc in vowels_set or ncp in all_combining:
                        cluster.append(nc)
                        i += 1
                    else:
                        break

                vowel_pos = [
                    j for j, ch in enumerate(cluster) if ch in vowels_set
                ]
                tone_pos = [
                    j for j, ch in enumerate(cluster) if ord(ch) in tone_cps
                ]
                quality_pos = [
                    j
                    for j, ch in enumerate(cluster)
                    if ord(ch) in quality_cps
                ]

                if tone_pos and len(vowel_pos) >= 2:
                    tone_idx = tone_pos[0]

                    if quality_pos:
                        target = max(quality_pos) + 1
                    elif len(vowel_pos) == 2:
                        target = vowel_pos[0] + 1
                    elif len(vowel_pos) == 3:
                        target = vowel_pos[1] + 1
                    else:
                        target = tone_idx

                    if target != tone_idx and 0 <= target <= len(cluster):
                        tone_char = cluster.pop(tone_idx)
                        if tone_idx < target:
                            target -= 1
                        cluster.insert(target, tone_char)

                result.extend(cluster)
            else:
                result.append(c)
                i += 1

        nfd = "".join(result)
        return unicodedata.normalize("NFC", nfd)

    def _parse_dates(self, series):
        try:
            dates = _to_datetime_safe(series, errors="coerce")
            if dates.notna().sum() > 0:
                return dates
        except Exception:
            pass
        return series

    def execute_plan(
        self, df: pd.DataFrame, plan: List[dict]
    ) -> Tuple[pd.DataFrame, List[str]]:
        df = df.copy()
        log = []
        for step in plan:
            op = step.get("operation")
            col = step.get("column")
            params = step.get("params", {})

            if op == "drop_nulls":
                before = len(df)
                subset = [col] if col else None
                df = df.dropna(subset=subset)
                df = df.reset_index(drop=True)
                log.append(
                    f"[AI Plan] Dropped {before - len(df)} rows with nulls (subset={subset})"
                )

            elif op == "fill_nulls":
                value = params.get("value", "")
                df[col] = df[col].fillna(value)
                log.append(
                    f"[AI Plan] Filled nulls in '{col}' with '{value}'"
                )

            elif op == "drop_duplicates":
                subset = [col] if col else None
                before = len(df)
                df = df.drop_duplicates(subset=subset)
                df = df.reset_index(drop=True)
                log.append(
                    f"[AI Plan] Dropped {before - len(df)} duplicate rows (subset={subset})"
                )

            elif op == "coerce_type":
                dtype = params.get("dtype", "str")
                if dtype in ("int", "float", "numeric"):
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif dtype == "datetime":
                    df[col] = _to_datetime_safe(df[col], errors="coerce")
                log.append(f"[AI Plan] Coerced '{col}' to {dtype}")

            elif op == "normalize_text":
                df[col] = df[col].apply(
                    lambda x: self._normalize_vn(x) if isinstance(x, str) else x
                )
                log.append(f"[AI Plan] Normalized text in '{col}'")

            elif op == "parse_dates":
                df[col] = _to_datetime_safe(df[col], errors="coerce")
                log.append(f"[AI Plan] Parsed dates in '{col}'")

            elif op == "drop_column":
                df = df.drop(columns=[col])
                log.append(f"[AI Plan] Dropped column '{col}'")

            elif op == "rename_column":
                new_name = params.get("new_name", col)
                df = df.rename(columns={col: new_name})
                log.append(f"[AI Plan] Renamed column '{col}' -> '{new_name}'")

        df = self._normalize_str_columns(df)
        str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        if str_cols:
            log.append("[AI Plan] Normalized Vietnamese diacritics in all text columns")

        return df, log
