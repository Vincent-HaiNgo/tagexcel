import json

from PyQt6.QtCore import QUrl


def strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return t


def try_parse_json_plan(text: str) -> dict | None:
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        depth = 0
        end = -1
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end > i:
            try:
                obj = json.loads(text[i:end])
                if "plan" in obj and isinstance(obj["plan"], list):
                    return obj
            except (json.JSONDecodeError, ValueError):
                continue
    return None


def build_df_schema(df):
    columns_info = []
    for col in df.columns:
        col_data = df[col]
        null_count = int(col_data.isna().sum())
        unique_count = int(col_data.nunique())
        samples = col_data.dropna().head(3).astype(str).tolist()
        columns_info.append({
            "name": str(col),
            "dtype": str(col_data.dtype),
            "unique_count": unique_count,
            "null_count": null_count,
            "samples": samples,
        })
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": columns_info,
    }


BASE_URL = QUrl("about:blank")
