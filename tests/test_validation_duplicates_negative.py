import csv
import pandas as pd
import pytest
import importlib

@pytest.fixture
def tmp_data_duplicates(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    clean_dir = data_dir / "clean"
    data_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)

    customers_csv = data_dir / "sebank_customers_with_accounts.csv"
    rows = [
        ["Customer","Address","Phone","Personnummer","BankAccount"],
        ["Eva","Gatan 5","+46700000001","010101-1237","ACCX"],
        ["Fred","Gatan 6","+46700000002","020202-0004","ACCX"],  # dubblettkonto
    ]
    with customers_csv.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

    validation = importlib.import_module("validation")
    monkeypatch.setattr(validation, "CUSTOMERS_IN", customers_csv)
    monkeypatch.setattr(validation, "OUT_DIR", clean_dir)
    yield {"clean_dir": clean_dir, "validation": validation}

def test_clean_customers_drops_duplicate_accounts(tmp_data_duplicates):
    validation = tmp_data_duplicates["validation"]
    out_file = tmp_data_duplicates["clean_dir"] / "customers_clean.csv"

    validation.clean_customers()
    assert out_file.exists(), "customers_clean.csv skapades inte"
    df = pd.read_csv(out_file, dtype=str, keep_default_na=False)

    # Exakt en rad med ACCX ska återstå (dubbletten borttagen)
    df_accx = df[df["BankAccount"] == "ACCX"]
    assert len(df_accx) == 1, "Dubbletter på BankAccount borde ha droppats så att 1 rad återstår"
    assert df["BankAccount"].is_unique, "BankAccount ska vara unika efter städning"