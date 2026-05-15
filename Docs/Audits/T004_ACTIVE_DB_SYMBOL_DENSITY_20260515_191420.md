# T004-D Active DB Symbol Density

Date: 2026-05-15T17:14:20Z

## Result

- Status: USDJPY_THIN_RELATIVE
- Active DB: Core/powerflow.db
- Symbols: USDJPY, GBPUSD, EURUSD
- Tables inspected: 8
- Populated tables: 8
- Symbol-indexed tables: 6

## Symbol totals

- USDJPY: 4060
- GBPUSD: 36059
- EURUSD: 5361

## Recommendations

- USDJPY exists but is thin relative to reference symbols. Investigate stream sparsity or filtering.

## Table density

### context_htf

- rows: 9881
- symbol_col: None
- time_col: None

sample:
`json
{
  "id": 1,
  "signal_id": 1,
  "bias": "GBP",
  "bias_state": "MIXTE",
  "scenario": "RETOURNEMENT",
  "aligned_count": 1,
  "fractal_rank": 1,
  "leader_tf": "M5",
  "htf_bonus": 0,
  "details_json": "[\"M5 ✅\", \"M15 ⬜\", \"M30 ⬜\", \"H1 ⬜\", \"H4 ⬜\"]"
}
`

### flow_packets

- rows: 820
- symbol_col: symbol
- time_col: created_at
- USDJPY | count=0 | min=None | max=None | ratio=0.0
- GBPUSD | count=820 | min=2026-05-12T12:05:17.751846+00:00 | max=2026-05-15T17:09:45.136528+00:00 | ratio=1.0
- EURUSD | count=0 | min=None | max=None | ratio=0.0

sample:
`json
{
  "id": 1,
  "created_at": "2026-05-12T12:05:17.751846+00:00",
  "symbol": "GBPUSD",
  "timeframe": 5,
  "packet_type": "CROSS_PACKET",
  "packet_level": "INFO",
  "pair_bias": "PAIR_DOWN",
  "strong": "usd",
  "weak": "gbp",
  "score": 2.7,
  "event_count": 1,
  "first_signal_at": "2026-05-12T12:00:17.567352+00:00"
}
`

### force_snapshots

- rows: 19812
- symbol_col: symbol
- time_col: created_at
- USDJPY | count=1623 | min=2026-05-04T12:20:00+00:00 | max=2026-05-15T20:10:00+00:00 | ratio=0.08192004845548152
- GBPUSD | count=14842 | min=2026-04-26T00:00:00+00:00 | max=2026-05-15T20:14:00+00:00 | ratio=0.7491419341813043
- EURUSD | count=2186 | min=2026-05-11T01:25:00+00:00 | max=2026-05-15T20:10:00+00:00 | ratio=0.1103371693922875

sample:
`json
{
  "id": 1,
  "created_at": "2026-04-29T11:46:00+00:00",
  "symbol": "GBPUSD",
  "timeframe": 1,
  "bid": null,
  "spread": null,
  "force_gbp": 50.7587,
  "force_usd": 43.3369,
  "force_eur": 67.434,
  "force_jpy": 56.7175,
  "force_cad": 35.8763,
  "force_chf": 23.1361
}
`

### force_snapshots_v2

- rows: 16372
- symbol_col: symbol
- time_col: created_at
- USDJPY | count=1599 | min=2026-05-12T12:00:00+00:00 | max=2026-05-15T20:10:00+00:00 | ratio=0.09766674810652333
- GBPUSD | count=11452 | min=2026-04-26T00:00:00+00:00 | max=2026-05-15T20:14:00+00:00 | ratio=0.6994869289030051
- EURUSD | count=2163 | min=2026-05-11T01:25:00+00:00 | max=2026-05-15T20:10:00+00:00 | ratio=0.13211580747617885

sample:
`json
{
  "id": 1,
  "created_at": "2026-05-04T12:00:00+00:00",
  "symbol": "GBPUSD",
  "timeframe": 240,
  "bar_time": 1777896000.0,
  "bar_close_time": 1777910400.0,
  "server_time": 1777920353.0,
  "capture_time": 1777920353.0,
  "is_closed_bar": 1,
  "bid": 1.35571,
  "ask": 1.35356,
  "mid": 1.35355
}
`

### nodes_v6

- rows: 34
- symbol_col: symbol
- time_col: detected_at
- USDJPY | count=0 | min=None | max=None | ratio=0.0
- GBPUSD | count=34 | min=2026-04-29T12:06:00 | max=2026-04-29T15:40:00 | ratio=1.0
- EURUSD | count=0 | min=None | max=None | ratio=0.0

sample:
`json
{
  "id": 1,
  "detected_at": "2026-04-29T13:00:00",
  "symbol": "GBPUSD",
  "timeframe": 15,
  "node_type": "CROISEMENT_TRIPLE",
  "dev_a": "gbp",
  "dev_b": "eur",
  "dev_c": "usd",
  "ecart_max": null,
  "delta": null,
  "direction": null,
  "pente": null
}
`

### signals

- rows: 9881
- symbol_col: symbol
- time_col: created_at
- USDJPY | count=838 | min=2026-05-12T10:39:07.674012+00:00 | max=2026-05-15T17:05:15.320676+00:00 | ratio=0.08480922983503694
- GBPUSD | count=7543 | min=2026-04-29T08:52:18.965306+00:00 | max=2026-05-15T17:11:15.433073+00:00 | ratio=0.7633842728468778
- EURUSD | count=1012 | min=2026-05-10T22:28:13.759605+00:00 | max=2026-05-15T17:05:15.333421+00:00 | ratio=0.10241878352393483

sample:
`json
{
  "id": 1,
  "created_at": "2026-04-29T08:52:18.965306+00:00",
  "symbol": "GBPUSD",
  "timeframe": 1,
  "signal_type": "COMPRESSION",
  "dev_strong": "usd",
  "dev_weak": "gbp",
  "score": 3,
  "level": "STANDARD",
  "spread_ok": 1,
  "volume_badge": "",
  "note": "🔒 COMPRESSION — USD en palier\nGBPUSD M1\nUSD stagne autour de 42.3 depuis 5 bougies\nCouloir ±5.0 pts | GBP=45.2\n⚡ Break ou rejet imminent\nHTF: GBP | MIXTE | RETOURNEMENT"
}
`

### sqlite_sequence

- rows: 7
- symbol_col: None
- time_col: None

sample:
`json
{
  "name": "force_snapshots",
  "seq": 19812
}
`

### zone_diagnostics

- rows: 1368
- symbol_col: symbol
- time_col: logged_at
- USDJPY | count=0 | min=None | max=None | ratio=0.0
- GBPUSD | count=1368 | min=2026-05-02T17:01:00+00:00 | max=2026-05-02T17:01:09+00:00 | ratio=1.0
- EURUSD | count=0 | min=None | max=None | ratio=0.0

sample:
`json
{
  "id": 2952,
  "logged_at": "2026-05-02T17:01:00+00:00",
  "source_created_at": "2026-05-01T23:07:00+00:00",
  "source_snapshot_id": 2755,
  "symbol": "GBPUSD",
  "timeframe": 1,
  "currency": "GBP",
  "state": "NEUTRAL",
  "zone_level": "NORMAL",
  "z_current": 0.3321,
  "z_extreme_dir": "NONE",
  "bars_in_extreme": 0
}
`


## Runtime behavior

- DB opened read-only.
- No runtime wiring.
- No dashboard files touched.

## Next action

If USDJPY is zero while references are present, inspect symbol routing/filter and MT4 Market Watch for USDJPY.
If no symbol-indexed table exists, map the populated schema before symbol debugging.

