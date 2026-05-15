# T004-E USDJPY Thin Root-Cause Map

Date: 2026-05-15T17:18:48Z

## Verdict

- Active DB: Core/powerflow.db
- Thin symbol: USDJPY
- Reference symbols: GBPUSD, EURUSD
- Likely cause: relative_sparsity

## Vote counts

- relative_sparsity: 3
- symbol_absent_in_symbol_table: 3

## Recommendations

- USDJPY is present but materially sparse versus references. Inspect upstream symbol stream/filter, not DB path.
- Check capture bridge symbol allowlist and MT4 Market Watch subscription for USDJPY.
- Do not change engine logic. This is capture/routing/data-density territory.

## Table details

### context_htf

- rows: 9881
- symbol_col: None
- time_col: None
- thin_status: NO_SYMBOL_COLUMN
- thin_ratio_vs_ref_avg: None
- latest_gap_seconds_vs_ref_best: None

### flow_packets

- rows: 820
- symbol_col: symbol
- time_col: created_at
- thin_status: ZERO_WHILE_REFERENCES_PRESENT
- thin_ratio_vs_ref_avg: 0.0
- latest_gap_seconds_vs_ref_best: None

per symbol:
- USDJPY | count=0 | min=None | max=None | age_seconds=None
- GBPUSD | count=821 | min=2026-05-12T12:05:17.751846+00:00 | max=2026-05-15T17:14:31.694106+00:00 | age_seconds=257.061937
- EURUSD | count=0 | min=None | max=None | age_seconds=None

top symbols:
- GBPUSD: 821

### force_snapshots

- rows: 19812
- symbol_col: symbol
- time_col: created_at
- thin_status: THIN_UNDER_25_PERCENT_REF_AVG
- thin_ratio_vs_ref_avg: 0.1907724818032402
- latest_gap_seconds_vs_ref_best: 179.9985770000003

per symbol:
- USDJPY | count=1625 | min=2026-05-04T12:20:00+00:00 | max=2026-05-15T20:15:00+00:00 | age_seconds=-10571.241913
- GBPUSD | count=14848 | min=2026-04-26T00:00:00+00:00 | max=2026-05-15T20:18:00+00:00 | age_seconds=-10751.24049
- EURUSD | count=2188 | min=2026-05-11T01:25:00+00:00 | max=2026-05-15T20:15:00+00:00 | age_seconds=-10571.240273

top symbols:
- GBPUSD: 14848
- EURUSD: 2188
- USDJPY: 1625
- AUDUSD: 388
- USDCAD: 388
- USDCHF: 388
- EURGBP: 1
- EURJPY: 1
- GBPJPY: 1

### force_snapshots_v2

- rows: 16372
- symbol_col: symbol
- time_col: created_at
- thin_status: THIN_UNDER_25_PERCENT_REF_AVG
- thin_ratio_vs_ref_avg: 0.23504367613594657
- latest_gap_seconds_vs_ref_best: 179.99817299999995

per symbol:
- USDJPY | count=1601 | min=2026-05-12T12:00:00+00:00 | max=2026-05-15T20:15:00+00:00 | age_seconds=-10571.238829
- GBPUSD | count=11458 | min=2026-04-26T00:00:00+00:00 | max=2026-05-15T20:18:00+00:00 | age_seconds=-10751.237002
- EURUSD | count=2165 | min=2026-05-11T01:25:00+00:00 | max=2026-05-15T20:15:00+00:00 | age_seconds=-10571.236666

top symbols:
- GBPUSD: 11458
- EURUSD: 2165
- USDJPY: 1601
- AUDUSD: 388
- USDCAD: 388
- USDCHF: 388

### nodes_v6

- rows: 34
- symbol_col: symbol
- time_col: detected_at
- thin_status: ZERO_WHILE_REFERENCES_PRESENT
- thin_ratio_vs_ref_avg: 0.0
- latest_gap_seconds_vs_ref_best: None

per symbol:
- USDJPY | count=0 | min=None | max=None | age_seconds=None
- GBPUSD | count=34 | min=2026-04-29T12:06:00 | max=2026-04-29T15:40:00 | age_seconds=1388328.763501
- EURUSD | count=0 | min=None | max=None | age_seconds=None

top symbols:
- GBPUSD: 34

### signals

- rows: 9881
- symbol_col: symbol
- time_col: created_at
- thin_status: THIN_UNDER_25_PERCENT_REF_AVG
- thin_ratio_vs_ref_avg: 0.19623875715453803
- latest_gap_seconds_vs_ref_best: 186.83942

per symbol:
- USDJPY | count=840 | min=2026-05-12T10:39:07.674012+00:00 | max=2026-05-15T17:15:15.461249+00:00 | age_seconds=213.30378
- GBPUSD | count=7547 | min=2026-04-29T08:52:18.965306+00:00 | max=2026-05-15T17:18:22.304321+00:00 | age_seconds=26.46436
- EURUSD | count=1014 | min=2026-05-10T22:28:13.759605+00:00 | max=2026-05-15T17:15:20.340556+00:00 | age_seconds=208.428609

top symbols:
- GBPUSD: 7547
- EURUSD: 1014
- USDJPY: 840
- USDCAD: 201
- AUDUSD: 147
- USDCHF: 144

### sqlite_sequence

- rows: 7
- symbol_col: None
- time_col: None
- thin_status: NO_SYMBOL_COLUMN
- thin_ratio_vs_ref_avg: None
- latest_gap_seconds_vs_ref_best: None

### zone_diagnostics

- rows: 1368
- symbol_col: symbol
- time_col: logged_at
- thin_status: ZERO_WHILE_REFERENCES_PRESENT
- thin_ratio_vs_ref_avg: 0.0
- latest_gap_seconds_vs_ref_best: None

per symbol:
- USDJPY | count=0 | min=None | max=None | age_seconds=None
- GBPUSD | count=1368 | min=2026-05-02T17:01:00+00:00 | max=2026-05-02T17:01:09+00:00 | age_seconds=1124259.771761
- EURUSD | count=0 | min=None | max=None | age_seconds=None

top symbols:
- GBPUSD: 1368

## Stop rule

Do not patch Core/engine.py. Do not patch pf_engine_v6_core.py. T004 is a data capture/routing diagnosis.

## Next action

T004-F should inspect capture bridge symbol filters / MT4 symbol subscription references and produce a minimal operator checklist.

