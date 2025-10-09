
# PyCharm run-konfigurationer & setup-skript

## Alternativ 1 – Snabbstart med PowerShell
I projektroten:
```powershell
scripts\setup.ps1 -WithDocker   # startar även Postgres + pgAdmin via Docker
# eller
scripts\setup.ps1               # utan Docker
scripts\run_all.ps1             # kör hela ETL
```

## Alternativ 2 – PyCharm Run Configurations
1. Stäng PyCharm om projektet redan är öppet.
2. Kopiera mappen `.idea/runConfigurations/` från den här zippen till **SPBank**-roten i ditt repo/projekt.
   - Slutlig sökväg: `SPBank/.idea/runConfigurations/*.xml`
3. Öppna projektet i PyCharm igen → alla run-configs dyker upp i droplistan:
   - **ETL – Full Pipeline** → `flow_main.py`
   - **ETL – Validation only** → `validation.py`
   - **ETL – Import Customers**
   - **ETL – Import Transactions**
   - **ETL – Import Flagged`
4. Se till att PyCharm använder rätt venv: `Settings → Project → Python Interpreter` peka på `.venv`.


