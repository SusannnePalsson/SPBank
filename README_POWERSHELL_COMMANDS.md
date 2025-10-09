# README – PowerShell-kommandon för SPBank

Liten guid med **bra att ha-kommandon** i PowerShell för att köra SPBank, validera/flagga transaktioner, importera data till DB och köra tester.

> Kör kommandon **från projektroten** (t.ex. `C:\Grupparbete\SPBank`) i en aktiverad virtuell miljö `(.venv)`.

---

## 1) Grundsetup

### Skapa/aktivera virtuell miljö och installera beroenden
```powershell
# Skapa venv (första gången)
python -m venv .venv

# Aktivera venv
.\.venv\Scripts\Activate.ps1

# Installera beroenden
pip install -r requirements.txt
```

### Sätt databas-URL (PostgreSQL)
```powershell
# Sätt (endast för aktuell session)
$env:DATABASE_URL = "postgresql+psycopg://postgres:Viktoria2014@localhost:5432/bank"

# Verifiera att värdet är satt
$env:DATABASE_URL
```
---

## 2) Kör **full flaggning/validering** utan att hämta data

Det finns två färdiga skript för när datan redan finns:
- **Från CSV**: `scripts/run_flagging_from_clean.py`
- **Direkt från DB**: `scripts/run_flagging_from_db.py`

### A) Flaggning från redan städad CSV
```powershell
# Om data\clean\transactions_clean.csv redan finns
.\.venv\Scripts\python scripts\run_flagging_from_clean.py --in data\clean\transactions_clean.csv --out data\clean\flagged_transactions.csv
```

**Argument (frivilliga):**
- `--in`  – sökväg till indata-CSV (default `data\clean\transactions_clean.csv`)
- `--out` – var resultat ska sparas (default `data\clean\flagged_transactions.csv`)
- `--tz`  – tidszon för flagged_date (default `Europe/Stockholm`)

### B) Flaggning direkt från databas
```powershell
# Om tabellen bank.transactions redan är fylld
$env:DATABASE_URL = "postgresql+psycopg://postgres:Viktoria2014@localhost:5432/bank"
.\.venv\Scripts\python scripts\run_flagging_from_db.py --out data\clean\flagged_transactions.csv
```

**Argument (frivilliga):**
- `--db`  – DATABASE_URL (default: värdet i $env:DATABASE_URL)
- `--out` – var resultat ska sparas (default `data\clean\flagged_transactions.csv`)
- `--tz`  – tidszon för flagged_date (default `Europe/Stockholm`)

> Bägge skripten skriver ut en sammanfattning och producerar CSV med kolumnerna: `transaction_id,reason,flagged_date,amount` (kompatibelt med import-skriptet).

---

## 3) Importera flaggade transaktioner till DB
```powershell
# Förutsätter att data\clean\flagged_transactions.csv finns
$env:DATABASE_URL = "postgresql+psycopg://postgres:Viktoria2014@localhost:5432/bank"
.\.venv\Scripts\python import_flagged_transactions.py
```

---

## 4) Köra hela ETL-flödet (Prefect)
```powershell
# Startar temporär Prefect server automatiskt och kör hela flödet
.\.venv\Scripts\python .\flow_main.py
```
> Loggen visar respektive steg (validering, import, rapporter).

---

## 5) Testsvit (pytest)

### Kör ALLA tester
```powershell
# Kräver DB för db/integrationstester
$env:DATABASE_URL = "postgresql+psycopg://postgres:Viktoria2014@localhost:5432/bank"
python -m pytest
```

### Kör snabba enhetstester (utan DB/integration)
```powershell
python -m pytest -k "not db and not integration"
```

### Kör endast DB-tester / endast integration
```powershell
# Endast db-tester
python -m pytest -m db

# Endast integrationstester
python -m pytest -m integration
```

### Kör endast flaggnings-reglerna
```powershell
# Alla tester i filen
python -m pytest tests\test_risk_rules.py -q

# Enstaka testfall (node-id)
python -m pytest tests\test_risk_rules.py::test_velocity_rule_triggers -q
```

### För tydlig sammanfattning
```powershell
# Mer output & visa sammanfattning (överstyr -q från pytest.ini)
python -m pytest -v -o addopts=
```

### Vanliga pytest-flaggor
```powershell
# Visa utskrifter (print)
python -m pytest -s

# Kör tills första fel
python -m pytest -x

# Kör endast senaste fallerade
python -m pytest --lf

# Samla tester utan att köra
python -m pytest --collect-only

# Visa långsammaste 10 tester (om många)
python -m pytest --durations=10
```

---

## 6) Kodtäckning (coverage)
```powershell
pip install coverage
coverage run -m pytest
coverage html
# Öppna htmlcov\index.html i webbläsaren
```

---

## 7) Kodstil (valfritt men bra)
```powershell
# Installera
pip install ruff black

# Lint
ruff check .

# Auto-formatera
black .
```

---

## 8) Nyttiga PowerShell-knep

### Visa första/sista rader i CSV
```powershell
Get-Content data\clean\flagged_transactions.csv -Head 10
Get-Content data\clean\flagged_transactions.csv -Tail 10
```

### Räkna rader i fil
```powershell
(Get-Content data\clean\flagged_transactions.csv).Count
```

### Rensa en mapp (t.ex. gamla outputs/loggar)
```powershell
Remove-Item -Recurse -Force .\data\clean\old\
```

### Tvinga UTF-8-utskrift i terminalen (minskar mojibake)
```powershell
$env:PYTHONUTF8 = "1"
```

---

## 9) Databas – snabbkontroller via SQLAlchemy (från Python REPL)
```powershell
# Starta Python
python
```
```python
# Inuti Python (exempel)
import os
from sqlalchemy import create_engine, text

db = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/bank")
if "options=" not in db:
    sep = "&" if "?" in db else "?"
    db = f"{db}{sep}options=-csearch_path%3Dbank%2Cpublic"

engine = create_engine(db, future=True)
with engine.connect() as c:
    print(c.execute(text("SELECT 1")).scalar_one())
    print(c.execute(text("SELECT COUNT(*) FROM bank.transactions")).scalar_one())
```
> Bra när du vill kontrollera snabbt att anslutningen fungerar och att tabellerna innehåller data.

---

## 10) Vanliga fel & lösningar

- **Alla kunder filtreras bort i validering**  
  Kontrollera att personnummerformatet matchar din validering (t.ex. `YYMMDD-XXXX`).

- **TypeError i rapporteringen (SQLAlchemy `Row`)**  
  Använd `row._mapping["kolumn"]` eller `result.mappings()` istället för `row["kolumn"]` i SQLAlchemy 2.x.

- **Mojibake (åäö → pÃ¥)**  
  Sätt `PYTHONUTF8=1` i PowerShell och säkerställ `encoding="utf-8"` vid filskrivning.

---

