# Tester för SPBank (pytest)

## Snabbstart
1. Installera beroenden:
   ```bash
   pip install -r requirements.txt
   ```

2. Sätt `DATABASE_URL` (för att köra DB/integrationstester):
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://postgres:Viktoria2014@localhost:5432/bank"
   ```

3. Kör alla snabba enhetstester (ingen DB krävs):
   ```bash
   pytest -k "not db and not integration"
   ```

4. Kör ALLA tester (inkl. DB & integration) – kräver att Postgres är uppe:
   ```bash
   pytest
   ```

## Innehåll
- `test_db.py` – anslutning och tabellkontroll.
- `test_flow_utils.py` – parser för sammanfattning i `flow_main.py`.
- `test_validation.py` – kundstädning (nu med **giltiga personnummer**).
- `test_risk_rules.py` – riktade regeltester.
- `test_import_integration.py` – end-to-end import.

## Notiser
- DB-tester skippar automatiskt om anslutning misslyckas.
- Windows UTF-8: `set PYTHONUTF8=1` för snygg konsolutskrift.

- `test_validation_negative.py` – säkerställer att **ogiltiga personnummer** filtreras bort (0 rader kvar).
- `test_validation_phone_negative.py` – säkerställer att **ogiltiga telefonnummer** filtreras bort.
- `test_validation_duplicates_negative.py` – säkerställer att **dubbletter på BankAccount** droppas (1 rad kvar).