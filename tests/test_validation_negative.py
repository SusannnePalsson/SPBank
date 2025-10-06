import csv
import pandas as pd
import pytest
from pathlib import Path
import importlib

@pytest.fixture
def tmp_data_invalid_pnr(tmp_path, monkeypatch):
    # Setup temp data dirs
    data_dir = tmp_path / "data"
    clean_dir = data_dir / "clean"
    data_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)

    # Create customers CSV with ONLY invalid personnummer (so they should be filtered out)
    customers_csv = data_dir / "sebank_customers_with_accounts.csv"
    rows = [
        ["Customer","Address","Phone","Personnummer","BankAccount"],
        ["Ivan","Gatan 10","+4611111","20010101-1234","ACC10"],  # ogiltigt pnr
        ["Julia","Gatan 11","+4622222","19990101-5670","ACC11"], # ogiltigt pnr
    ]
    with customers_csv.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

    # Import module and patch paths
    validation = importlib.import_module("validation")
    monkeypatch.setattr(validation, "CUSTOMERS_IN", customers_csv)
    monkeypatch.setattr(validation, "OUT_DIR", clean_dir)
    yield {"clean_dir": clean_dir, "validation": validation}

def test_clean_customers_filters_invalid_personnummer(tmp_data_invalid_pnr):
    validation = tmp_data_invalid_pnr["validation"]
    out_file = tmp_data_invalid_pnr["clean_dir"] / "customers_clean.csv"

    validation.clean_customers()
    assert out_file.exists(), "customers_clean.csv skapades inte"
    df = pd.read_csv(out_file, dtype=str, keep_default_na=False)

    # Alla rader ska vara bortfiltrerade p.g.a. ogiltiga personnummer
    assert df.shape[0] == 0