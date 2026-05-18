import sys
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.parser_engine import ParserEngine


@pytest.fixture
def engine():
    return ParserEngine()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Name": ["  Alice  ", "Bob", "Charlie", "  Bob  ", "  ", None],
        "Age": ["25", "30", "35", "30", "n/a", "28"],
        "City": [
            "H\u00e0 N\u1ed9i",
            "H\u1ed3 Ch\u00ed Minh",
            "\u0110\u00e0 N\u1eb5ng",
            "H\u1ed3 Ch\u00ed Minh",
            "N/A",
            "C\u1ea7n Th\u01a1",
        ],
    })


@pytest.fixture
def vietnamese_df():
    return pd.DataFrame({
        "text": ["ho\u00e0 b\u00ecnh", "h\u00f2a b\u00ecnh", "Ho\u00e0 B\u00ecnh", "HO\u00c0 B\u00ccNH"],
    })


def test_parse_strips_whitespace(engine, sample_df):
    result, log = engine.parse(sample_df)
    assert result["Name"].iloc[0] == "Alice"


def test_parse_detects_null_sentinels(engine, sample_df):
    result, log = engine.parse(sample_df)
    null_names = result[result["Name"].isna()]
    null_ages = result[result["Age"].isna()]
    null_cities = result[result["City"].isna()]
    assert len(null_names) >= 1
    assert len(null_ages) >= 1
    assert len(null_cities) >= 1


def test_parse_removes_duplicates(engine, sample_df):
    result, log = engine.parse(sample_df)
    assert len(result) < len(sample_df)


def test_parse_normalizes_vietnamese(engine, vietnamese_df):
    result, log = engine.parse(vietnamese_df)
    assert result["text"].iloc[0] == result["text"].iloc[1]


def test_normalize_vn_tone_on_main_vowel_uyen(engine):
    df = pd.DataFrame({"name": ["Nguy\u1ec5n", "Ngu\u1ef9\u00ean"]})
    result, log = engine.parse(df)
    assert result["name"].iloc[0] == result["name"].iloc[1]


def test_normalize_vn_tone_on_main_vowel_oai(engine):
    df = pd.DataFrame({"name": ["Tho\u1ea1i", "Th\u1ecda\u0069"]})
    result, log = engine.parse(df)
    assert result["name"].iloc[0] == result["name"].iloc[1]


def test_normalize_vn_tone_on_quality_vowel_ieu(engine):
    df = pd.DataFrame({"name": ["Chi\u1ec3u", "Ch\u1ec9\u00eau"]})
    result, log = engine.parse(df)
    assert result["name"].iloc[0] == result["name"].iloc[1]


def test_parse_returns_log(engine, sample_df):
    result, log = engine.parse(sample_df)
    assert isinstance(log, list)
    assert len(log) > 0
    assert all(isinstance(entry, str) for entry in log)


def test_parse_infers_numeric(engine):
    df = pd.DataFrame({"num": ["1", "2", "3", "4", "5"]})
    result, log = engine.parse(df)
    assert pd.api.types.is_numeric_dtype(result["num"])


def test_parse_preserves_mixed_column(engine):
    df = pd.DataFrame({"mixed": ["hello", "world", "123", np.nan, "abc"]})
    result, log = engine.parse(df)
    assert pd.api.types.is_object_dtype(result["mixed"]) or pd.api.types.is_string_dtype(
        result["mixed"]
    )


def test_parse_empty_dataframe(engine):
    df = pd.DataFrame({"A": []})
    result, log = engine.parse(df)
    assert len(result) == 0


def test_execute_plan_drop_nulls(engine):
    df = pd.DataFrame({"A": [1, None, 3], "B": ["x", "y", "z"]})
    plan = [{"operation": "drop_nulls", "column": "A"}]
    result, log = engine.execute_plan(df, plan)
    assert len(result) == 2
    assert "Dropped" in log[0]


def test_execute_plan_drop_nulls_all_columns(engine):
    df = pd.DataFrame({"A": [1, None, 3], "B": ["x", None, "z"]})
    plan = [{"operation": "drop_nulls"}]
    result, log = engine.execute_plan(df, plan)
    assert len(result) == 2


def test_execute_plan_fill_nulls(engine):
    df = pd.DataFrame({"A": [1, None, 3]})
    plan = [{"operation": "fill_nulls", "column": "A", "params": {"value": "0"}}]
    result, log = engine.execute_plan(df, plan)
    assert result["A"].iloc[1] == "0"


def test_execute_plan_drop_duplicates(engine):
    df = pd.DataFrame({"A": [1, 2, 2, 3], "B": ["a", "b", "b", "c"]})
    plan = [{"operation": "drop_duplicates"}]
    result, log = engine.execute_plan(df, plan)
    assert len(result) == 3


def test_execute_plan_coerce_type_numeric(engine):
    df = pd.DataFrame({"A": ["1", "2", "3"]})
    plan = [{"operation": "coerce_type", "column": "A", "params": {"dtype": "numeric"}}]
    result, log = engine.execute_plan(df, plan)
    assert pd.api.types.is_numeric_dtype(result["A"])


def test_execute_plan_coerce_type_datetime(engine):
    df = pd.DataFrame({"A": ["2024-01-01", "2024-02-01"]})
    plan = [{"operation": "coerce_type", "column": "A", "params": {"dtype": "datetime"}}]
    result, log = engine.execute_plan(df, plan)
    assert pd.api.types.is_datetime64_any_dtype(result["A"])


def test_execute_plan_normalize_text(engine):
    df = pd.DataFrame({"A": ["ho\u00e0", "h\u00f2a"]})
    plan = [{"operation": "normalize_text", "column": "A"}]
    result, log = engine.execute_plan(df, plan)
    assert result["A"].iloc[0] == result["A"].iloc[1]


def test_execute_plan_drop_column(engine):
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    plan = [{"operation": "drop_column", "column": "B"}]
    result, log = engine.execute_plan(df, plan)
    assert "B" not in result.columns
    assert "A" in result.columns


def test_execute_plan_rename_column(engine):
    df = pd.DataFrame({"A": [1, 2]})
    plan = [{"operation": "rename_column", "column": "A", "params": {"new_name": "Alpha"}}]
    result, log = engine.execute_plan(df, plan)
    assert "Alpha" in result.columns
    assert "A" not in result.columns


def test_execute_plan_parse_dates(engine):
    df = pd.DataFrame({"A": ["2024/01/01", "2024-02-15", "March 3, 2024"]})
    plan = [{"operation": "parse_dates", "column": "A"}]
    result, log = engine.execute_plan(df, plan)
    assert "Parsed dates" in log[0]


def test_execute_plan_multiple_steps(engine):
    df = pd.DataFrame({
        "A": [1, None, 2, 2],
        "B": ["x", "y", None, None],
    })
    plan = [
        {"operation": "drop_nulls"},
        {"operation": "drop_duplicates"},
    ]
    result, log = engine.execute_plan(df, plan)
    assert len(result) == 1
    assert len(log) == 3
