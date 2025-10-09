# valideringar som skapar flaggade transaktioner
 
### 1) `Structuring band 9500–9999.99 SEK, High velocity ≥ 20 tx/24h`

**Förklaring:**
- **Structuring band 9500–9999.99 SEK** betyder att flera transaktioner ligger strax under 10 000 SEK-gränsen — ett klassiskt tecken på *“smurfing”* eller strukturerad insättning, där man försöker undvika rapporteringsgränser.  
- **High velocity ≥ 20 tx/24h** betyder att det gjorts **20 eller fler transaktioner inom 24 timmar**, vilket är ovanligt mycket.

**Tolkning:** Kunden gör många snabba transaktioner på belopp precis under rapporteringsgränsen — ett mönster som ofta används för att dölja större belopp.

---

### 2) `High amount vs p98 (per valuta), High-value cross-border (strict), New counterparty (>14d) + high amount`

**Förklaring:**
- **High amount vs p98** betyder att beloppet är bland de **2 % största** transaktionerna för den valutan (över 98:e percentilen).  
- **High-value cross-border (strict)** betyder att det är en **gränsöverskridande betalning** med ovanligt högt belopp.  
- **New counterparty (>14d)** betyder att mottagaren är **ny** — ingen tidigare transaktionshistorik de senaste 14 dagarna.

**Tolkning:** En mycket stor internationell betalning till en helt ny mottagare – en situation som ofta kräver manuell kontroll.

---

### 3) `Ping-pong (retur inom 7d)`

**Förklaring:**  
Transaktionen skickas ut, men **pengarna kommer tillbaka inom 7 dagar**.

**Tolkning:** Detta kan tyda på **test- eller täcktransaktioner** (för att testa konton) eller **försök att tvätta pengar** genom korta cirklar av pengar.

---

### 4) `Structuring band 950–999.99 USD`

**Förklaring:**  
Flera transaktioner **strax under 1 000 USD**, vilket ofta är en gräns för ökad rapportering eller kontroll i vissa system.

**Tolkning:** Samma typ av mönster som punkt 1 – **strukturerad aktivitet** för att undvika granskning.

---

### 5) `Structuring band 9500–9999.99 SEK`

**Förklaring:**  
Återigen transaktioner strax under **10 000 SEK**, vilket är en misstänkt uppdelning av belopp för att undvika flaggning eller rapportering.

**Tolkning:** Möjligen ett försök att **dela upp större summor** över flera transaktioner.

---

### 6) `High amount vs p98 (per valuta), New counterparty (>14d) + high amount`

**Förklaring:**  
- **High amount vs p98:** mycket stort belopp.  
- **New counterparty (>14d):** ny mottagare, ingen tidigare historik de senaste två veckorna.

**Tolkning:** En **ovanligt stor betalning till en ny mottagare**, vilket ofta flaggas som potentiell risk.

---

### 7) `High velocity ≥ 20 tx/24h`

**Förklaring:**  
**Mer än 20 transaktioner inom 24 timmar.**

**Tolkning:** Ovanligt hög aktivitet på kort tid — kan indikera **automatiserade transaktioner**, **bedrägeri** eller **försök att flytta pengar snabbt**.

---

## Sammanfattning (övergripande)

| Typ av flagga          | Betydelse                                   | Möjlig risk |
|------------------------|---------------------------------------------|-------------|
| **Structuring band**   | Många transaktioner precis under gräns      | Försök att undvika rapporteringsnivå |
| **High velocity**      | Väldigt många transaktioner snabbt          | Penningtvätt, bot-aktivitet, testning |
| **High amount vs p98** | Ovanligt högt belopp jämfört med historik   | Misstänkt stor transaktion |
| **Cross-border**       | Gränsöverskridande betalning                | Möjlig internationell risk |
| **New counterparty**   | Mottagare är ny                             | Potentiell risk för bedrägeri |
| **Ping-pong**          | Pengar skickas fram och tillbaka snabbt     | Test- eller täcktransaktioner |

---

## Riskprioriterad tabell

| Flagga / Regel                         | Enkel beskrivning                            | Vad det betyder i praktiken                                | Möjlig risk / tolkning                                  | **Risknivå** |
|----------------------------------------|----------------------------------------------|------------------------------------------------------------|---------------------------------------------------------|:-----------:|
| **Structuring band 9500–9999.99 SEK**  | Transaktioner strax under 10 000 SEK         | Kunden delar upp belopp för att undvika gräns              | Klassisk “smurfing”/strukturerad penningtvätt           | 🔴 **Hög** |
| **Structuring band 950–999.99 USD**    | Transaktioner strax under 1 000 USD          | Samma mönster som ovan, fast i USD                         | Försök att undvika kontrollgräns                        | 🔴 **Hög** |
| **High velocity ≥ 20 tx/24h**          | ≥ 20 transaktioner inom 24h                  | Extrem aktivitet på kort tid                               | Automatiserad aktivitet, bedrägeri, layering            | 🟠 **Medel–Hög** |
| **High amount vs p98 (per valuta)**    | Bland de 2 % största beloppen                | Ovanligt stort belopp jämfört med kundens norm             | Potentiellt misstänkt stor överföring                   | 🟠 **Medel–Hög** |
| **High-value cross-border (strict)**   | Stor internationell betalning                 | Gränsöverskridande betalning med hög summa                 | Ökad risk, särskilt vid okända mottagare                | 🔴 **Hög** |
| **New counterparty (>14d) + high amount** | Stort belopp till ny mottagare             | Ingen tidigare relation eller transaktionshistorik         | Misstänkt ovanlig betalning, risk för bedrägeri         | 🟠 **Medel–Hög** |
| **Ping-pong (retur inom 7d)**          | Retur inom 7 dagar                           | Pengar går A→B och tillbaka inom kort tid                  | Testtransaktioner eller försök att dölja spår           | 🔴 **Hög** |
