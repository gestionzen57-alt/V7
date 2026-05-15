# T004-J Active Insertion Table and Symbol Delta

Date: 2026-05-15T17:42:52Z

## Verdict

- Status: REFERENCES_ADVANCED_THIN_SYMBOL_ZERO
- DB: Core/powerflow.db
- Watch seconds: 120
- Sample count: 13

## Symbol deltas

- USDJPY: 0
- GBPUSD: 5
- EURUSD: 0

## Active tables

- flow_packets | row_delta=1 | symbol_col=symbol | time_col=created_at | max_time_before=2026-05-15T17:39:25.051855+00:00 | max_time_after=2026-05-15T17:44:34.136486+00:00
  - GBPUSD: 1
- force_snapshots | row_delta=2 | symbol_col=symbol | time_col=created_at | max_time_before=2026-05-15T20:42:00+00:00 | max_time_after=2026-05-15T20:44:00+00:00
  - GBPUSD: 2
- force_snapshots_v2 | row_delta=2 | symbol_col=symbol | time_col=created_at | max_time_before=2026-05-15T20:42:00+00:00 | max_time_after=2026-05-15T20:44:00+00:00
  - GBPUSD: 2

## Recommendations

- References advanced but USDJPY did not. Focus on USDJPY feed/routing/allowlist.
- Do not patch engine/scoring logic; use this to target capture/feed checks.

## Table deltas

### context_htf

- row_delta: 0
- symbol_col: None
- time_col: None
- max_time_before: None
- max_time_after: None

symbol deltas:
- EURUSD: 0
- GBPUSD: 0
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 9924,
    "signal_id": 9924,
    "bias": "USD",
    "bias_state": "VALIDE",
    "scenario": "TENDANCE",
    "aligned_count": 4,
    "fractal_rank": 5,
    "leader_tf": "M15",
    "htf_bonus": 3,
    "details_json": "[\"M15 ✅\", \"M30 ✅\", \"H1 ✅\", \"H4 ✅\"]"
  },
  {
    "id": 9923,
    "signal_id": 9923,
    "bias": "EUR",
    "bias_state": "MIXTE",
    "scenario": "TENDANCE",
    "aligned_count": 3,
    "fractal_rank": 4,
    "leader_tf": "M15",
    "htf_bonus": 2,
    "details_json": "[\"M15 ✅\", \"M30 ✅\", \"H1 ✅\", \"H4 ❌\"]"
  },
  {
    "id": 9922,
    "signal_id": 9922,
    "bias": "EUR",
    "bias_state": "MIXTE",
    "scenario": "TENDANCE",
    "aligned_count": 3,
    "fractal_rank": 4,
    "leader_tf": "M15",
    "htf_bonus": 2,
    "details_json": "[\"M15 ✅\", \"M30 ✅\", \"H1 ✅\", \"H4 ❌\"]"
  }
]
`

### flow_packets

- row_delta: 1
- symbol_col: symbol
- time_col: created_at
- max_time_before: 2026-05-15T17:39:25.051855+00:00
- max_time_after: 2026-05-15T17:44:34.136486+00:00

symbol deltas:
- EURUSD: 0
- GBPUSD: 1
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 827,
    "created_at": "2026-05-15T17:44:34.136486+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "packet_type": "TRAP_REVERSAL_PACKET",
    "packet_level": "HOT",
    "pair_bias": "PAIR_DOWN",
    "strong": "usd",
    "weak": "gbp",
    "score": 15.25,
    "event_count": 3,
    "first_signal_at": "2026-05-15T17:29:15.649988+00:00"
  },
  {
    "id": 826,
    "created_at": "2026-05-15T17:39:25.051855+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "packet_type": "TRAP_REVERSAL_PACKET",
    "packet_level": "HOT",
    "pair_bias": "PAIR_DOWN",
    "strong": "usd",
    "weak": "gbp",
    "score": 15.25,
    "event_count": 3,
    "first_signal_at": "2026-05-15T17:29:15.649988+00:00"
  },
  {
    "id": 825,
    "created_at": "2026-05-15T17:34:29.188361+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "packet_type": "TRAP_REVERSAL_PACKET",
    "packet_level": "HOT",
    "pair_bias": "PAIR_DOWN",
    "strong": "usd",
    "weak": "gbp",
    "score": 15.25,
    "event_count": 3,
    "first_signal_at": "2026-05-15T17:29:15.649988+00:00"
  }
]
`

### force_snapshots

- row_delta: 2
- symbol_col: symbol
- time_col: created_at
- max_time_before: 2026-05-15T20:42:00+00:00
- max_time_after: 2026-05-15T20:44:00+00:00

symbol deltas:
- EURUSD: 0
- GBPUSD: 2
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 19896,
    "created_at": "2026-05-15T20:44:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bid": 1.33316,
    "spread": null,
    "force_gbp": 44.5061,
    "force_usd": 81.1553,
    "force_eur": 32.646,
    "force_jpy": 74.7398,
    "force_cad": 45.7742,
    "force_chf": 27.3355
  },
  {
    "id": 19895,
    "created_at": "2026-05-15T20:43:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bid": 1.3332,
    "spread": null,
    "force_gbp": 42.6252,
    "force_usd": 80.1536,
    "force_eur": 30.9015,
    "force_jpy": 73.9096,
    "force_cad": 50.5706,
    "force_chf": 26.3628
  },
  {
    "id": 19894,
    "created_at": "2026-05-15T20:42:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bid": 1.33314,
    "spread": null,
    "force_gbp": 42.321,
    "force_usd": 79.6591,
    "force_eur": 27.6534,
    "force_jpy": 74.8423,
    "force_cad": 54.3192,
    "force_chf": 25.2212
  }
]
`

### force_snapshots_v2

- row_delta: 2
- symbol_col: symbol
- time_col: created_at
- max_time_before: 2026-05-15T20:42:00+00:00
- max_time_after: 2026-05-15T20:44:00+00:00

symbol deltas:
- EURUSD: 0
- GBPUSD: 2
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 16553,
    "created_at": "2026-05-15T20:44:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bar_time": 1778877840.0,
    "bar_close_time": 1778877900.0,
    "server_time": 1778877841.0,
    "capture_time": 1778877841.0,
    "is_closed_bar": 0,
    "bid": 1.33316,
    "ask": 1.33318,
    "mid": 1.33317
  },
  {
    "id": 16552,
    "created_at": "2026-05-15T20:43:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bar_time": 1778877780.0,
    "bar_close_time": 1778877840.0,
    "server_time": 1778877781.0,
    "capture_time": 1778877781.0,
    "is_closed_bar": 0,
    "bid": 1.3332,
    "ask": 1.33321,
    "mid": 1.3332
  },
  {
    "id": 16551,
    "created_at": "2026-05-15T20:42:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bar_time": 1778877720.0,
    "bar_close_time": 1778877780.0,
    "server_time": 1778877721.0,
    "capture_time": 1778877721.0,
    "is_closed_bar": 0,
    "bid": 1.33314,
    "ask": 1.33316,
    "mid": 1.33315
  }
]
`

### nodes_v6

- row_delta: 0
- symbol_col: symbol
- time_col: detected_at
- max_time_before: 2026-04-29T15:40:00
- max_time_after: 2026-04-29T15:40:00

symbol deltas:
- EURUSD: 0
- GBPUSD: 0
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 34,
    "detected_at": "2026-04-29T13:00:00",
    "symbol": "GBPUSD",
    "timeframe": 60,
    "node_type": "COMPRESSION",
    "dev_a": "gbp/usd/eur",
    "dev_b": null,
    "dev_c": null,
    "ecart_max": 4.88,
    "delta": null,
    "direction": null,
    "pente": "PLATE"
  },
  {
    "id": 33,
    "detected_at": "2026-04-29T14:30:00",
    "symbol": "GBPUSD",
    "timeframe": 30,
    "node_type": "COMPRESSION",
    "dev_a": "gbp/usd/eur",
    "dev_b": null,
    "dev_c": null,
    "ecart_max": 2.41,
    "delta": null,
    "direction": null,
    "pente": "PLATE"
  },
  {
    "id": 32,
    "detected_at": "2026-04-29T15:40:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "node_type": "LIBERATION",
    "dev_a": "eur",
    "dev_b": null,
    "dev_c": null,
    "ecart_max": null,
    "delta": 15.48,
    "direction": "BAISSE",
    "pente": "MONTANTE"
  }
]
`

### signals

- row_delta: 0
- symbol_col: symbol
- time_col: created_at
- max_time_before: 2026-05-15T17:40:20.375981+00:00
- max_time_after: 2026-05-15T17:40:20.375981+00:00

symbol deltas:
- EURUSD: 0
- GBPUSD: 0
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 9924,
    "created_at": "2026-05-15T17:40:20.375981+00:00",
    "symbol": "USDJPY",
    "timeframe": 5,
    "signal_type": "APPROACH",
    "dev_strong": "jpy",
    "dev_weak": "usd",
    "score": 5,
    "level": "CONFIRM",
    "spread_ok": 1,
    "volume_badge": "",
    "note": "⏳ APPROCHE IMMINENTE — USDJPY M5\nUSD remonte vers JPY — écart 11.3 pts\nUSD=34.2 → JPY=45.5\nMomentum +6.39/tick | Depuis zone SURVENTE\nPrépare-toi : CROSS ou REJET imminent"
  },
  {
    "id": 9923,
    "created_at": "2026-05-15T17:40:20.355161+00:00",
    "symbol": "EURUSD",
    "timeframe": 5,
    "signal_type": "SLINGSHOT",
    "dev_strong": "usd",
    "dev_weak": "eur",
    "score": 6,
    "level": "CONFIRM",
    "spread_ok": 1,
    "volume_badge": "",
    "note": "🎯 USD explose après repli conjoint"
  },
  {
    "id": 9922,
    "created_at": "2026-05-15T17:40:20.349941+00:00",
    "symbol": "EURUSD",
    "timeframe": 5,
    "signal_type": "APPROACH",
    "dev_strong": "eur",
    "dev_weak": "usd",
    "score": 4,
    "level": "STANDARD",
    "spread_ok": 1,
    "volume_badge": "",
    "note": "⏳ APPROCHE IMMINENTE — EURUSD M5\nUSD remonte vers EUR — écart 9.0 pts\nUSD=34.2 → EUR=43.3\nMomentum +5.38/tick | Depuis zone BAS\nPrépare-toi : CROSS ou REJET imminent"
  }
]
`

### sqlite_sequence

- row_delta: 0
- symbol_col: None
- time_col: None
- max_time_before: None
- max_time_after: None

symbol deltas:
- EURUSD: 0
- GBPUSD: 0
- USDJPY: 0

recent rows after:
`json
[
  {
    "name": "force_snapshots",
    "seq": 19896
  },
  {
    "name": "signals",
    "seq": 9924
  },
  {
    "name": "context_htf",
    "seq": 9924
  }
]
`

### zone_diagnostics

- row_delta: 0
- symbol_col: symbol
- time_col: logged_at
- max_time_before: 2026-05-02T17:01:09+00:00
- max_time_after: 2026-05-02T17:01:09+00:00

symbol deltas:
- EURUSD: 0
- GBPUSD: 0
- USDJPY: 0

recent rows after:
`json
[
  {
    "id": 4319,
    "logged_at": "2026-05-02T17:01:09+00:00",
    "source_created_at": "2026-05-01T22:00:00+00:00",
    "source_snapshot_id": 2746,
    "symbol": "GBPUSD",
    "timeframe": 60,
    "currency": "AUD",
    "state": "NEUTRAL",
    "zone_level": "NORMAL",
    "z_current": -0.8715,
    "z_extreme_dir": "NONE",
    "bars_in_extreme": 0
  },
  {
    "id": 4318,
    "logged_at": "2026-05-02T17:01:09+00:00",
    "source_created_at": "2026-05-01T22:00:00+00:00",
    "source_snapshot_id": 2746,
    "symbol": "GBPUSD",
    "timeframe": 60,
    "currency": "CHF",
    "state": "NEUTRAL",
    "zone_level": "NORMAL",
    "z_current": -0.9349,
    "z_extreme_dir": "NONE",
    "bars_in_extreme": 0
  },
  {
    "id": 4317,
    "logged_at": "2026-05-02T17:01:09+00:00",
    "source_created_at": "2026-05-01T22:00:00+00:00",
    "source_snapshot_id": 2746,
    "symbol": "GBPUSD",
    "timeframe": 60,
    "currency": "CAD",
    "state": "PRE_EXTREME",
    "zone_level": "PRE_EXTREME",
    "z_current": -1.7744,
    "z_extreme_dir": "LOW",
    "bars_in_extreme": 8
  }
]
`

## Stop rule

Do not change engine/scoring modules. This is an active insertion and symbol routing diagnostic.

## Next action

If rows advanced without tracked symbol deltas, inspect active table schema and recent rows. If references advanced and USDJPY did not, inspect source feed/allowlist for USDJPY.

