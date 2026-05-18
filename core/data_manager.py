from pathlib import Path
from typing import Optional

import pandas as pd


class DataManager:
    @staticmethod
    def load_file(path: str) -> pd.DataFrame:
        ext = Path(path).suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext == ".xlsx":
            try:
                return pd.read_excel(path, engine="calamine")
            except Exception:
                return pd.read_excel(path, engine="openpyxl")
        else:
            return pd.read_excel(path, engine="xlrd")

    def __init__(self):
        self._files: dict = {}
        self._active_file: Optional[str] = None
        self._df_original: Optional[pd.DataFrame] = None
        self._df_working: Optional[pd.DataFrame] = None

    def add_file(self, path: str):
        p = Path(path)
        df = DataManager.load_file(path)
        filename = p.name
        self._files[filename] = df
        self._active_file = filename
        self._df_original = df.copy()
        self._df_working = df.copy()

    def remove_files(self, filenames: list):
        for fn in filenames:
            if fn in self._files:
                del self._files[fn]
        if self._active_file in filenames:
            self._active_file = next(iter(self._files), None)
            if self._active_file:
                self._df_original = self._files[self._active_file].copy()
                self._df_working = self._df_original.copy()
            else:
                self._df_original = None
                self._df_working = None

    def set_active(self, filename: str):
        if filename in self._files:
            self._active_file = filename
            self._df_original = self._files[filename].copy()
            self._df_working = self._df_original.copy()

    def get_loaded_files(self) -> list:
        return list(self._files.keys())

    def reset_working(self):
        if self._df_original is not None:
            self._df_working = self._df_original.copy()

    def update_working(self, df):
        self._df_working = df

    def get_summary(self) -> dict:
        if self._df_working is None:
            return {"filename": None, "columns": 0, "rows": 0}
        return {
            "filename": self._active_file,
            "columns": len(self._df_working.columns),
            "rows": len(self._df_working),
        }

    @property
    def df_working(self):
        return self._df_working

    @property
    def active_file(self):
        return self._active_file
