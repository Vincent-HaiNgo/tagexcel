import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.data_manager import DataManager


@pytest.fixture
def sample_csv():
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25, 30, 35],
        "City": ["H\u00e0 N\u1ed9i", "H\u1ed3 Ch\u00ed Minh", "\u0110\u00e0 N\u1eb5ng"],
    })
    with tempfile.NamedTemporaryFile(
        suffix=".csv", mode="w", delete=False, encoding="utf-8"
    ) as f:
        df.to_csv(f.name, index=False)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_excel():
    df = pd.DataFrame({
        "Product": ["Widget", "Gadget", "Doohickey"],
        "Price": [9.99, 15.50, 3.75],
        "Qty": [100, 50, 200],
    })
    with tempfile.NamedTemporaryFile(suffix=".xlsx", mode="wb", delete=False) as f:
        df.to_excel(f.name, index=False, engine="openpyxl")
        yield f.name
    Path(f.name).unlink(missing_ok=True)


def test_add_csv_file(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    assert dm.active_file is not None
    assert dm.df_working is not None
    assert len(dm.df_working) == 3
    assert list(dm.df_working.columns) == ["Name", "Age", "City"]


def test_add_excel_file(sample_excel):
    dm = DataManager()
    dm.add_file(sample_excel)
    assert dm.active_file is not None
    assert dm.df_working is not None
    assert len(dm.df_working) == 3


def test_add_multiple_files(sample_csv, sample_excel):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.add_file(sample_excel)
    files = dm.get_loaded_files()
    assert len(files) == 2
    assert dm.active_file == Path(sample_excel).name


def test_set_active(sample_csv, sample_excel):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.add_file(sample_excel)
    dm.set_active(Path(sample_csv).name)
    assert dm.active_file == Path(sample_csv).name
    assert len(dm.df_working) == 3


def test_remove_active_file(sample_csv, sample_excel):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.add_file(sample_excel)
    first_active = dm.active_file
    dm.remove_files([first_active])
    remaining = dm.get_loaded_files()
    assert len(remaining) == 1
    assert dm.active_file in remaining


def test_remove_non_active_file(sample_csv, sample_excel):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.add_file(sample_excel)
    dm.set_active(Path(sample_csv).name)
    dm.remove_files([Path(sample_excel).name])
    assert dm.active_file == Path(sample_csv).name
    assert len(dm.get_loaded_files()) == 1


def test_remove_all_files(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.remove_files(dm.get_loaded_files())
    assert dm.get_loaded_files() == []
    assert dm.active_file is None
    assert dm.df_working is None


def test_reset_working(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    original = dm.df_working.copy()
    dm.update_working(original.drop(columns=["City"]))
    assert len(dm.df_working.columns) == 2
    dm.reset_working()
    assert len(dm.df_working.columns) == 3
    assert list(dm.df_working.columns) == ["Name", "Age", "City"]


def test_update_working(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    new_df = dm.df_working.drop(columns=["City"])
    dm.update_working(new_df)
    assert len(dm.df_working.columns) == 2


def test_get_summary(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    summary = dm.get_summary()
    assert summary["columns"] == 3
    assert summary["rows"] == 3
    assert summary["filename"] is not None


def test_get_summary_empty():
    dm = DataManager()
    summary = dm.get_summary()
    assert summary["filename"] is None
    assert summary["columns"] == 0
    assert summary["rows"] == 0


def test_df_original_immutable_after_add(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.update_working(dm.df_working.drop(columns=["City"]))
    assert len(dm.df_working.columns) == 2
    dm.reset_working()
    assert len(dm.df_working.columns) == 3


def test_set_active_nonexistent(sample_csv):
    dm = DataManager()
    dm.add_file(sample_csv)
    dm.set_active("nonexistent.csv")
    assert dm.active_file == Path(sample_csv).name
