# ============================================================
# tests/test_data.py
# ============================================================
"""
Tests unitaires pour core/data.py
"""

import io

import pandas as pd
import pytest

from core.data import (
    load_data,
    detect_spectral_columns,
    sort_columns_preserve_logic,
    missing_report,
    quality_overview,
)


class FakeUploadedFile(io.BytesIO):
    """Simule un fichier uploadé par Streamlit (a un attribut .name)."""

    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


# ============================================================
# detect_spectral_columns
# ============================================================
def test_detect_spectral_columns_basic():
    df = pd.DataFrame(columns=["800.5", "1450", "DATE", "1000,2", "ECHANTILLON"])
    spectral_cols, value_map = detect_spectral_columns(df)

    assert spectral_cols == ["800.5", "1000,2", "1450"]
    assert value_map["800.5"] == 800.5
    assert value_map["1000,2"] == 1000.2
    assert "DATE" not in value_map
    assert "ECHANTILLON" not in value_map


def test_detect_spectral_columns_none_numeric():
    df = pd.DataFrame(columns=["DATE", "LOT", "OPERATEUR"])
    spectral_cols, value_map = detect_spectral_columns(df)

    assert spectral_cols == []
    assert value_map == {}


# ============================================================
# sort_columns_preserve_logic
# ============================================================
def test_sort_columns_preserve_logic_orders_spectral_then_alpha():
    all_cols = ["1450", "DATE", "800.5", "LOT", "1000"]
    spectral_map = {"1450": 1450.0, "800.5": 800.5, "1000": 1000.0}

    result = sort_columns_preserve_logic(all_cols, all_cols, spectral_map)

    # Spectrales triées par valeur croissante, puis non-spectrales par ordre alpha
    assert result == ["800.5", "1000", "1450", "DATE", "LOT"]


def test_sort_columns_preserve_logic_removes_duplicates_and_unknown():
    all_cols = ["800.5", "1450"]
    selected = ["800.5", "800.5", "UNKNOWN_COL", "1450"]
    spectral_map = {"800.5": 800.5, "1450": 1450.0}

    result = sort_columns_preserve_logic(selected, all_cols, spectral_map)

    assert result == ["800.5", "1450"]


# ============================================================
# missing_report
# ============================================================
def test_missing_report_counts_and_percentages():
    df = pd.DataFrame({
        "a": [1, None, 3, None],
        "b": [1, 2, 3, 4],
    })

    report = missing_report(df)

    assert report.loc["a", "Missing"] == 2
    assert report.loc["a", "%"] == 50.0
    assert report.loc["b", "Missing"] == 0
    assert report.loc["b", "%"] == 0.0
    # Trié par % décroissant
    assert report.index[0] == "a"


def test_missing_report_empty_dataframe():
    df = pd.DataFrame()
    report = missing_report(df)

    assert list(report.columns) == ["Missing", "%"]
    assert report.empty


# ============================================================
# quality_overview
# ============================================================
def test_quality_overview_basic_counts():
    df = pd.DataFrame({
        "a": [1, None, 3, None],
        "b": [1, 2, 3, 4],
        "c": [None, None, None, None],
    })

    overview = quality_overview(df)

    assert overview["total_na"] == 6
    assert overview["pct_na"] == pytest.approx((6 / 12) * 100)
    assert overview["n_empty_cols"] == 1
    # La colonne "c" est entièrement vide : elle rend TOUTES les lignes
    # impactées, pas seulement celles où "a" a un NA.
    assert overview["n_rows_with_na"] == 4
    assert overview["n_duplicates"] == 0
    assert list(overview["report"].columns) == ["Missing", "%"]


def test_quality_overview_counts_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 1, 2]})

    overview = quality_overview(df)

    assert overview["n_duplicates"] == 1


def test_quality_overview_empty_dataframe():
    df = pd.DataFrame()
    overview = quality_overview(df)

    assert overview["total_na"] == 0
    assert overview["pct_na"] == 0.0
    assert overview["n_empty_cols"] == 0
    assert overview["n_rows_with_na"] == 0
    assert overview["n_duplicates"] == 0


# ============================================================
# load_data
# ============================================================
def test_load_data_csv_comma():
    content = b"800.5,1450,DATE\n0.1,0.2,2024-01-01\n0.3,0.4,2024-01-02\n"
    fake_file = FakeUploadedFile(content, "spectres.csv")

    df = load_data.__wrapped__(fake_file)

    assert list(df.columns) == ["800.5", "1450", "DATE"]
    assert df.shape == (2, 3)


def test_load_data_csv_semicolon():
    content = b"800.5;1450;DATE\n0.1;0.2;2024-01-01\n0.3;0.4;2024-01-02\n"
    fake_file = FakeUploadedFile(content, "spectres.csv")

    df = load_data.__wrapped__(fake_file)

    assert list(df.columns) == ["800.5", "1450", "DATE"]
    assert df.shape == (2, 3)


def test_load_data_excel():
    original = pd.DataFrame({"800.5": [0.1, 0.3], "1450": [0.2, 0.4]})
    buffer = io.BytesIO()
    original.to_excel(buffer, index=False)
    buffer.seek(0)

    fake_file = FakeUploadedFile(buffer.read(), "spectres.xlsx")
    df = load_data.__wrapped__(fake_file)

    assert list(df.columns) == ["800.5", "1450"]
    assert df.shape == (2, 2)


def test_load_data_unsupported_format():
    fake_file = FakeUploadedFile(b"n'importe quoi", "spectres.txt")

    with pytest.raises(ValueError):
        load_data.__wrapped__(fake_file)
