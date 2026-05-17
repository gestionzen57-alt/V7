# T009 / B9 Force Snapshot Scene Generation V0

## Mission

Generate deterministic historical B9 proxy summaries from `powerflow.db / force_snapshots_v2` when explicit `t009_sequence_summary.json` files are missing.

## Doctrine

Raw MT5 donne la texture. B9 summaries donnent les scènes. This patch creates source-aware proxy summaries from an explicit proxy source. It does not recover existing summaries and does not invent scenes from raw MT5 alone.

## Source

- DB: `powerflow.db`
- Table: `force_snapshots_v2`
- Access: SQLite read-only mode
- Symbol default: `GBPUSD`
- Output: JSON/MD/ZIP only

## Provenance fields

Every generated summary/moment contains:

```text
summary_recovery_type = FORCE_SNAPSHOT_DERIVED
summary_recovery_version = T009_FORCE_SNAPSHOT_SCENE_GENERATOR_V0
data_visibility = RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED
source_mode = M1_BAR_PROXY or TF{n}_BAR_PROXY
confidence_cap = 0.35 for M1, 0.25 for higher timeframe fallback
```

## Deterministic rules

1. Select rows from `force_snapshots_v2` for symbol/date/timeframe.
2. Prefer M1, then TF5/TF15/TF30/TF60 when M1 is absent or sparse.
3. Split contiguous bars into windows of at most 60 minutes or on large time gaps.
4. Classify each window using OHLC displacement, range, displacement efficiency, tick_volume proxy, and GBP/USD force variation.
5. Keep retest fields as NOT_VISIBLE in V0. Native retest proof is not inferred.

## Constraints

- No write to `powerflow.db`.
- No write to `tick_archive.db`.
- No dashboard mutation.
- No Telegram.
- No BUY/SELL.
- No footprint exact claim.
- No participant identification.
- No central orderbook claim.

## Commands

```powershell
python -m py_compile .\pf_t009_force_snapshot_scene_generator.py .\run_t009_force_snapshot_scene_generation.py
python -m pytest .\tests\test_t009_force_snapshot_scene_generator.py -v
powershell -ExecutionPolicy Bypass -File .\scripts\RUN_T009_FORCE_SNAPSHOT_SCENE_GENERATION.ps1
```

## Next step

Feed the generated `force_snapshot_derived_summaries` folder to the weekly raw calibration runner, then keep the outputs labelled as `FORCE_SNAPSHOT_DERIVED`, not recovered summaries.
