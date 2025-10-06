import csv
import pandas as pd
import pytest
from pathlib import Path

import importlib

@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    # Skapa data/ och data/clean i en temp-mapp
    data_dir = tmp_path / "data"
    clean_dir = data_dir / "clean"
    data_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)

    # Skriv en minimal kundfil med giltiga personnummer (Luhn-kontroll) och några dubbletter
    customers_csv = data_dir / "sebank_customers_with_accounts.csv"
    rows = [
        ["Customer","Address","Phone","Personnummer","BankAccount"],
        ["Alice","Gatan 1","+4612345","010101-1237","ACC1"],  # giltigt pnr
        ["Bob","Gatan 2","not phone","990101-5678","ACC2"],   # giltigt pnr
        ["Charlie","Gatan 3","+46 555 555","010101-1237","ACC3"], # samma pnr som Alice
        ["Dora","Gatan 4","+46 777 777","020202-0004","ACC2"],    # giltigt pnr, samma konto som Bob
    ]
    with customers_csv.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

    # Importera validation och peka om filvägarna
    validation = importlib.import_module("validation")
    monkeypatch.setattr(validation, "CUSTOMERS_IN", customers_csv)
    monkeypatch.setattr(validation, "OUT_DIR", clean_dir)
    yield {"data_dir": data_dir, "clean_dir": clean_dir, "validation": validation}

def test_clean_customers_produces_unique_accounts(tmp_data):
    validation = tmp_data["validation"]
    out_file = tmp_data["clean_dir"] / "customers_clean.csv"

    validation.clean_customers()
    assert out_file.exists(), "customers_clean.csv skapades inte"

    df = pd.read_csv(out_file, dtype=str, keep_default_na=False)
    # Ska ha minst 1 rad kvar efter validering
    assert df.shape[0] >= 1
    # BankAccount ska vara unika (en kund per konto)
    assert df["BankAccount"].is_unique