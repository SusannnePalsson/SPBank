import csv
import pandas as pd
import pytest
import importlib

@pytest.fixture
def tmp_data_phone(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    clean_dir = data_dir / "clean"
    data_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)

    customers_csv = data_dir / "sebank_customers_with_accounts.csv"
    rows = [
        ["Customer","Address","Phone","Personnummer","BankAccount"],
        ["Alice","Gatan 1","abc","010101-1237","ACCP"],          # ogiltigt telefonnummer
        ["Bob","Gatan 2","+46701234567","020202-0004","ACCQ"],   # giltigt telefonnummer
    ]
    with customers_csv.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

    validation = importlib.import_module("validation")
    monkeypatch.setattr(validation, "CUSTOMERS_IN", customers_csv)
    monkeypatch.setattr(validation, "OUT_DIR", clean_dir)
    yield {"clean_dir": clean_dir, "validation": validation}

def test_clean_customers_filters_invalid_phone(tmp_data_phone):
    validation = tmp_data_phone["validation"]
    out_file = tmp_data_phone["clean_dir"] / "customers_clean.csv"

    validation.clean_customers()
    assert out_file.exists(), "customers_clean.csv skapades inte"

    df = pd.read_csv(out_file, dtype=str, keep_default_na=False)

    # Förväntan: raden med ogiltigt telefonnummer ('ACCP') filtreras bort,
    # den giltiga ('ACCQ') finns kvar.
    assert "ACCP" not in set(df["BankAccount"]), "Raden med ogiltigt telefonnummer borde ha filtrerats bort"
    assert "ACCQ" in set(df["BankAccount"]), "Raden med giltigt telefonnummer borde finnas kvar"