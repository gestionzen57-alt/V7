# T010.1 — MT5 Historical Date-Range Export

**Projet :** PowerFlow V7.6.7 / T009-B9 Raw Tick Validation  
**Branche cible :** `feat/t010-b9-mt5-raw-tick-recorder`  
**Objet :** permettre l'export MT5 raw tick sur une fenêtre historique précise.

## 1. Pourquoi ce patch existe

Le recorder T010 initial validait le pipeline :

```text
MT5 HISTORICAL_RAW CSV
→ Core/import_mt5_ticks_csv.py
→ Core/tick_archive.db
→ tick_stream
```

Mais il utilisait seulement :

```text
InpHistoryMinutes
```

Cela valide le flux technique, mais ne cible pas une journée de terrain précise. Lors du premier test, l'export obtenu couvrait :

```text
GBPUSD 2026-05-13 02:13:15 → 2026-05-13 17:24:24
```

Or la comparaison B9 attendue concerne :

```text
GBPUSD 2026-05-15 London 08:00–12:00
GBPUSD 2026-05-15 London 12:00–14:00
GBPUSD 2026-05-15 Day 14:00–23:00
```

## 2. Changement livré

Le fichier :

```text
MQL5/T009_TickRecorder_MT5.mq5
```

ajoute les inputs :

```text
InpEnableHistoricalDateRange
InpHistoricalStart
InpHistoricalEnd
```

Exemple MT5 :

```text
InpEnableOnTickRaw = false
InpEnableTimerSample = false
InpEnableHistoricalBackfill = false
InpEnableHistoricalDateRange = true
InpHistoricalStart = 2026.05.15 08:00
InpHistoricalEnd   = 2026.05.15 12:00
InpOutputFileName  = PowerFlow_T009_ticks_GBPUSD_20260515_0800_1200.csv
```

Le mode date-range a priorité sur `InpHistoryMinutes` quand il est activé.

## 3. Fenêtres à exporter pour B9 proxy vs raw

Créer trois CSV séparés :

```text
PowerFlow_T009_ticks_GBPUSD_20260515_0800_1200.csv
PowerFlow_T009_ticks_GBPUSD_20260515_1200_1400.csv
PowerFlow_T009_ticks_GBPUSD_20260515_1400_2300.csv
```

Paramètres :

```text
GBPUSD 2026.05.15 08:00 → 2026.05.15 12:00
GBPUSD 2026.05.15 12:00 → 2026.05.15 14:00
GBPUSD 2026.05.15 14:00 → 2026.05.15 23:00
```

## 4. Import attendu après export

Depuis `Core` :

```powershell
python .\import_mt5_ticks_csv.py --csv "$env:APPDATA\MetaQuotes\Terminal\Common\Files\PowerFlow_T009_ticks_GBPUSD_20260515_0800_1200.csv" --db ".\tick_archive.db"
python .\import_mt5_ticks_csv.py --csv "$env:APPDATA\MetaQuotes\Terminal\Common\Files\PowerFlow_T009_ticks_GBPUSD_20260515_1200_1400.csv" --db ".\tick_archive.db"
python .\import_mt5_ticks_csv.py --csv "$env:APPDATA\MetaQuotes\Terminal\Common\Files\PowerFlow_T009_ticks_GBPUSD_20260515_1400_2300.csv" --db ".\tick_archive.db"
```

## 5. Contrôle DB

```powershell
@'
import sqlite3
con = sqlite3.connect("file:tick_archive.db?mode=ro", uri=True)
cur = con.cursor()
cur.execute("""
SELECT symbol, source_mode, COUNT(*), MIN(ts_utc), MAX(ts_utc)
FROM tick_stream
WHERE symbol='GBPUSD'
GROUP BY symbol, source_mode
""")
for row in cur.fetchall():
    print(row)
con.close()
'@ | python -
```

## 6. Règles conservées

```text
- aucune écriture dans powerflow.db
- aucune modification dashboard
- aucun Telegram
- aucun BUY/SELL
- aucune fusion B8
- source_mode conservé : HISTORICAL_RAW
- rapport proxy/raw source-aware uniquement
```

## 7. Limite

Même avec MT5 raw tick, le rapport B9 doit rester source-aware. Tant que la fenêtre n'est pas importée et comparée, ne pas affirmer :

```text
footprint exact confirmé
micro-trap confirmé
ordre limite confirmé
participants piégés confirmés
```

Le premier résultat attendu est une qualification :

```text
raw confirme / proxy-only / raw-only / raw insufficient
```
