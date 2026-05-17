# T0103 — B9 Weekly Raw Calibration Replay Pack

Status: READY_FOR_INSTALL

Purpose: run B9 Raw Calibration V3.6 across weekly B9 summaries, then aggregate calibrated moments for the B9/B6 Lab.

Doctrine:
- B9 raconte la scène.
- Raw vérifie la texture.
- B6 mémorise les films et les pièges.

Inputs:
- tick_archive.db with GBPUSD MT5 HISTORICAL_RAW.
- B9 `t009_sequence_summary.json` files.
- `run_t009_raw_calibration_once.py`.
- V3.6 dedup read-only calibrator.

Raw alignment:
`raw_ts_mt5 + 180 minutes = proxy_ts_mt4_approx`

Dedup rule:
`SELECT DISTINCT ts_utc, bid, ask, mid, spread`

Main outputs:
- `B9_WEEK_CALIBRATION_RESULTS_20260504_20260515.md`
- `B9_WEEK_CALIBRATION_RESULTS_20260504_20260515.csv`
- `B9_RAW_CALIBRATION_OUTPUTS_20260504_20260515_V36.zip`

Scene families to watch:
- PROGRESSIVE_WAVE_CONFIRMED
- PROGRESSIVE_WAVE_ROTATIONAL
- PROGRESSIVE_WAVE_WEAK_RAW
- CENTER_MIGRATION_CONFIRMED
- EFFORT_WITHOUT_RESULT
- HIGH_ZONE_EXHAUSTION
- LOWER_LOCK
- COUNTER_BREATH
- COUNTER_BREATH_REJECTED
- SECOND_LEG
- READING_PARTIAL
- RAW_PROXY_DIVERGENCE
- MEMORY_SHIFTED
- ZERO_DURATION_ARTIFACT

Constraints:
- read-only
- no powerflow.db write
- no tick_archive.db write
- no dashboard mutation
- no Telegram
- no BUY/SELL
- no B8 fusion
- no footprint exact beyond broker-relative raw evidence

Phrase de cap:
Une journée valide la lecture. Une semaine révèle les films. Le mois montre le changement de cycle.
