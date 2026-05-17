# T009/B9 — Raw Calibration V3.2 à V3.5

## Mission

Ajouter une couche de calibration read-only entre B9 `M1_BAR_PROXY / RECONSTRUCTED` et MT5 `HISTORICAL_RAW / MT5_RAW_ALIGNED`.

Phrase de cap :

```text
B9 ne doit pas devenir raw-only. B9 doit apprendre quand le raw confirme, nuance ou corrige sa lecture proxy.
```

## Livrables

```text
Core/pf_t009_raw_calibration.py
Core/run_t009_raw_calibration_once.py
Core/tests/test_t009_raw_calibration_v32_v35.py
Core/docs/Reports/T009_B9_RAW_CALIBRATION_V32_V35_REPORT.md
```

## B9 V3.2 — raw coverage aware

Chaque moment calibré reçoit :

```json
{
  "raw_coverage": "FULL | PARTIAL | MISSING",
  "raw_source_mode": "HISTORICAL_RAW",
  "raw_data_visibility": "MT5_RAW_ALIGNED",
  "broker": "OneFunded Capital Ltd.",
  "broker_time_shift_min": 180,
  "raw_confidence_cap": 0.55,
  "raw_limits": [
    "broker-relative",
    "not central orderbook",
    "no participant identification"
  ]
}
```

## B9 V3.3 — raw texture adapter read-only

Chaque moment reçoit des métriques raw :

```json
{
  "raw_tick_count": 966,
  "raw_delta_pips": 9.7,
  "raw_range_pips": 11.4,
  "raw_spread_avg_pips": 0.26,
  "raw_gap_max_ms": 17778,
  "raw_texture_role": "RAW_PROGRESS_CONFIRMED",
  "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW"
}
```

Rôles gérés :

```text
RAW_PROGRESS_CONFIRMED
RAW_DWELL_CONFIRMED
RAW_ROTATION_CONFIRMED
RAW_FRICTION_CONFIRMED
RAW_PROXY_DIVERGENCE
RAW_UNAVAILABLE
ZERO_DURATION_MOMENT
```

## B9 V3.4 — cleanup moments zéro durée

Les moments `time_start == time_end` ne deviennent pas de faux `RAW_UNAVAILABLE`.

Traitement minimal :

```json
{
  "zero_duration_status": "ZERO_DURATION_MOMENT",
  "raw_texture_role": "ZERO_DURATION_MOMENT",
  "proxy_vs_raw_verdict": "ZERO_DURATION_MOMENT"
}
```

## B9 V3.5 — recalibrage Progressive Wave

Sous-états :

```text
PROGRESSIVE_WAVE_CONFIRMED
PROGRESSIVE_WAVE_WEAK_RAW
PROGRESSIVE_WAVE_ROTATIONAL
PROGRESSIVE_WAVE_PROXY_ONLY
PROJECTION_DECAY
```

Règle : une vague progressive proxy ne disparaît pas automatiquement si le raw nuance. B9 conserve la lecture proxy, mais ajoute le verdict raw.

## Usage CLI

```powershell
python .\run_t009_raw_calibration_once.py `
  --summary-json ".\output\t009_sequence_summary.json" `
  --tick-db ".\tick_archive.db" `
  --output ".\output\b9_raw_calibrated" `
  --broker-time-shift-min 180
```

Sorties :

```text
output/b9_raw_calibrated/t009_sequence_summary_raw_calibrated.json
output/b9_raw_calibrated/t009_sequence_summary_raw_calibrated.md
```

## Contraintes respectées

```text
read-only
aucune écriture powerflow.db
aucune modification dashboard
aucun Telegram
aucun BUY/SELL
pas de footprint exact affirmé
M1_BAR_PROXY / RECONSTRUCTED visible
MT5 HISTORICAL_RAW / MT5_RAW_ALIGNED visible
confidence_cap visible
```
