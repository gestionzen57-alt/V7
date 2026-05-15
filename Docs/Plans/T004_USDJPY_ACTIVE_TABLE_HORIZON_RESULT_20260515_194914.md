# T004-K USDJPY Active-Table Horizon Audit

Date: 2026-05-15T17:49:14Z

## Verdict

- Verdict: USDJPY_ABSENT_FROM_ACTIVE_INSERTION_TABLES
- DB: Core/powerflow.db
- Thin symbol: USDJPY
- Reference symbols: GBPUSD, EURUSD
- Source active tables: flow_packets, force_snapshots, force_snapshots_v2

## Vote counts

- historically_sparse: 2
- absent_in_active_tables: 1

## Recommendations

- USDJPY is absent from at least one active insertion table while references exist. Focus capture routing/allowlist/source feed.
- Do not patch PowerFlow engine/scoring modules; T004 remains capture/routing/feed normalization.

## Suffix / near-symbol candidates

- none

## Table horizons

### flow_packets

- rows: 827
- symbol_col: symbol
- time_col: created_at
- horizon_status: THIN_SYMBOL_ABSENT_REFERENCES_PRESENT
- thin_latest_gap_seconds_vs_best_ref: None

per symbol:
- USDJPY | count=0 | max_time=None | age_seconds=None
- GBPUSD | count=827 | max_time=2026-05-15T17:44:34.136486+00:00 | age_seconds=280.646783
- EURUSD | count=0 | max_time=None | age_seconds=None

top symbols:
- GBPUSD: 827

recent rows by symbol:
- USDJPY: 0 row(s) sampled
- GBPUSD: 5 row(s) sampled
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
    "first_signal_at": "2026-05-15T17:29:15.649988+00:00",
    "last_signal_at": "2026-05-15T17:30:19.423018+00:00",
    "payload_json": "{\"symbol\": \"GBPUSD\", \"timeframe\": 1, \"pair_bias\": \"PAIR_DOWN\", \"strong\": \"usd\", \"weak\": \"gbp\", \"first_signal_at\": \"2026-05-15T17:29:15.649988+00:00\", \"last_signal_at\": \"2026-05-15T17:30:19.423018+00:00\", \"events\": [{\"rowid\": 9907, \"created_at\": \"2026-05-15T17:29:15.649988+00:00\", \"symbol\": \"GBPUSD\", \"timeframe\": 1, \"signal_type\": \"FAKEOUT\", \"dev_strong\": \"usd\", \"dev_weak\": \"gbp\", \"score\": 6, \"level\": \"CONFIRM\", \"note\": \"⚠️ Croisement précédent était un piège\\nHTF: GBP | MIXTE | 3 TF alignés | RANGE\\nLeader: M5 | Rang fractal: 3/5\\nM5 ✅ M15 ❌ M30 ✅ H1 ✅ H4 ❌\"}, {\"rowid\": 9909, \"created_at\": \"2026-05-15T17:30:15.507527+00:00\", \"symbol\": \"GBPUSD\", \"timeframe\": 1, \"signal_type\": \"COMPRESSION_BREAK\", \"dev_strong\": \"usd\", \"dev_weak\": \"gbp\", \"score\": 6, \"level\": \"CONFIRM\", \"note\": \"🚀 SORTIE PALIER — USD Rupture haussière\\nGBPUSD M1\\nUSD quitte le palier 55.3 → 61.8\\nDirection : HAUT | Bande ±5.0 pts\"}, {\"rowid\": 9914, \"created_at\": \"2026-05-15T17:30:19.423018+00:00\", \"symbol\": \"GBPUSD\", \"timeframe\": 1, \"signal_type\": \"COMPRESSION\", \"dev_strong\": \"usd\", \"dev_weak\": \"gbp\", \"score\": 5, \"level\": \"CONFIRM\", \"note\": \"🔒 COMPRESSION — USD en palier\\nGBPUSD M1\\nUSD stagne autour de 61.8 depuis 5 bougies\\nCouloir ±5.0 pts | GBP=50.4\\n⚡ Break ou rejet imminent\\nHTF: GBP | MIXTE | RANGE\"}], \"packet_type\": \"TRAP_REVERSAL_PACKET\", \"packet_level\": \"HOT\", \"score\": 15.25, \"event_count\": 3, \"types\": [\"FAKEOUT\", \"COMPRESSION_BREAK\", \"COMPRESSION\"], \"notes\": [\"⚠️ Croisement précédent était un piège | HTF: GBP | MIXTE | 3 TF alignés | RANGE | Leader: M5 | Rang fractal: 3/5 | M5 ✅ M15 ❌ M30 ✅ H1 ✅ H4 ❌\", \"🚀 SORTIE PALIER — USD Rupture haussière | GBPUSD M1 | USD quitte le palier 55.3 → 61.8 | Direction : HAUT | Bande ±5.0 pts\", \"🔒 COMPRESSION — USD en palier | GBPUSD M1 | USD stagne autour de 61.8 depuis 5 bougies | Couloir ±5.0 pts | GBP=50.4 | ⚡ Break ou rejet imminent | HTF: GBP | MIXTE | RANGE\"]}"
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
    "first_signal_at": "2026-05-15T17:29:15.649988+00:00",
    "last_signal_at": "2026-05-15T17:30:19.423018+00:00",
    "payload_json": "{\"symbol\": \"GBPUSD\", \"timeframe\": 1, \"pair_bias\": \"PAIR_DOWN\", \"strong\": \"usd\", \"weak\": \"gbp\", \"first_signal_at\": \"2026-05-15T17:29:15.649988+00:00\", \"last_signal_at\": \"2026-05-15T17:30:19.423018+00:00\", \"events\": [{\"rowid\": 9907, \"created_at\": \"2026-05-15T17:29:15.649988+00:00\", \"symbol\": \"GBPUSD\", \"timeframe\": 1, \"signal_type\": \"FAKEOUT\", \"dev_strong\": \"usd\", \"dev_weak\": \"gbp\", \"score\": 6, \"level\": \"CONFIRM\", \"note\": \"⚠️ Croisement précédent était un piège\\nHTF: GBP | MIXTE | 3 TF alignés | RANGE\\nLeader: M5 | Rang fractal: 3/5\\nM5 ✅ M15 ❌ M30 ✅ H1 ✅ H4 ❌\"}, {\"rowid\": 9909, \"created_at\": \"2026-05-15T17:30:15.507527+00:00\", \"symbol\": \"GBPUSD\", \"timeframe\": 1, \"signal_type\": \"COMPRESSION_BREAK\", \"dev_strong\": \"usd\", \"dev_weak\": \"gbp\", \"score\": 6, \"level\": \"CONFIRM\", \"note\": \"🚀 SORTIE PALIER — USD Rupture haussière\\nGBPUSD M1\\nUSD quitte le palier 55.3 → 61.8\\nDirection : HAUT | Bande ±5.0 pts\"}, {\"rowid\": 9914, \"created_at\": \"2026-05-15T17:30:19.423018+00:00\", \"symbol\": \"GBPUSD\", \"timeframe\": 1, \"signal_type\": \"COMPRESSION\", \"dev_strong\": \"usd\", \"dev_weak\": \"gbp\", \"score\": 5, \"level\": \"CONFIRM\", \"note\": \"🔒 COMPRESSION — USD en palier\\nGBPUSD M1\\nUSD stagne autour de 61.8 depuis 5 bougies\\nCouloir ±5.0 pts | GBP=50.4\\n⚡ Break ou rejet imminent\\nHTF: GBP | MIXTE | RANGE\"}], \"packet_type\": \"TRAP_REVERSAL_PACKET\", \"packet_level\": \"HOT\", \"score\": 15.25, \"event_count\": 3, \"types\": [\"FAKEOUT\", \"COMPRESSION_BREAK\", \"COMPRESSION\"], \"notes\": [\"⚠️ Croisement précédent était un piège | HTF: GBP | MIXTE | 3 TF alignés | RANGE | Leader: M5 | Rang fractal: 3/5 | M5 ✅ M15 ❌ M30 ✅ H1 ✅ H4 ❌\", \"🚀 SORTIE PALIER — USD Rupture haussière | GBPUSD M1 | USD quitte le palier 55.3 → 61.8 | Direction : HAUT | Bande ±5.0 pts\", \"🔒 COMPRESSION — USD en palier | GBPUSD M1 | USD stagne autour de 61.8 depuis 5 bougies | Couloir ±5.0 pts | GBP=50.4 | ⚡ Break ou rejet imminent | HTF: GBP | MIXTE | RANGE\"]}"
  }
]
`
- EURUSD: 0 row(s) sampled

### force_snapshots

- rows: 19912
- symbol_col: symbol
- time_col: created_at
- horizon_status: THIN_SYMBOL_HISTORICALLY_SPARSE
- thin_latest_gap_seconds_vs_best_ref: 179.99250399999983

per symbol:
- USDJPY | count=1634 | max_time=2026-05-15T20:45:00+00:00 | age_seconds=-10545.205888
- GBPUSD | count=14887 | max_time=2026-05-15T20:48:00+00:00 | age_seconds=-10725.198392
- EURUSD | count=2197 | max_time=2026-05-15T20:45:00+00:00 | age_seconds=-10545.183287

top symbols:
- GBPUSD: 14887
- EURUSD: 2197
- USDJPY: 1634
- AUDUSD: 397
- USDCAD: 397
- USDCHF: 397
- EURGBP: 1
- EURJPY: 1
- GBPJPY: 1

recent rows by symbol:
- USDJPY: 5 row(s) sampled
`json
[
  {
    "id": 19899,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "USDJPY",
    "timeframe": 5,
    "bid": 158.694,
    "spread": null,
    "force_gbp": 68.1481,
    "force_usd": 40.98,
    "force_eur": 39.7645,
    "force_jpy": 49.0898,
    "force_cad": 35.6197,
    "force_chf": 57.086,
    "force_aud": 58.9607
  },
  {
    "id": 19902,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "USDJPY",
    "timeframe": 15,
    "bid": 158.694,
    "spread": null,
    "force_gbp": 32.5077,
    "force_usd": 33.9911,
    "force_eur": 54.9546,
    "force_jpy": 27.0368,
    "force_cad": 72.9456,
    "force_chf": 60.2784,
    "force_aud": 76.244
  }
]
`
- GBPUSD: 5 row(s) sampled
`json
[
  {
    "id": 19912,
    "created_at": "2026-05-15T20:48:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bid": 1.33333,
    "spread": null,
    "force_gbp": 52.9852,
    "force_usd": 73.8382,
    "force_eur": 43.9718,
    "force_jpy": 55.2576,
    "force_cad": 41.0238,
    "force_chf": 42.4206,
    "force_aud": 33.5097
  },
  {
    "id": 19911,
    "created_at": "2026-05-15T20:47:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bid": 1.33323,
    "spread": null,
    "force_gbp": 49.1808,
    "force_usd": 80.7676,
    "force_eur": 41.5824,
    "force_jpy": 62.4835,
    "force_cad": 41.1396,
    "force_chf": 37.8451,
    "force_aud": 29.0323
  }
]
`
- EURUSD: 5 row(s) sampled
`json
[
  {
    "id": 19898,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "EURUSD",
    "timeframe": 5,
    "bid": 1.16288,
    "spread": null,
    "force_gbp": 68.1384,
    "force_usd": 40.98,
    "force_eur": 39.8293,
    "force_jpy": 49.0645,
    "force_cad": 35.6078,
    "force_chf": 57.086,
    "force_aud": 58.9607
  },
  {
    "id": 19903,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "EURUSD",
    "timeframe": 15,
    "bid": 1.16288,
    "spread": null,
    "force_gbp": 32.6402,
    "force_usd": 33.9911,
    "force_eur": 53.6635,
    "force_jpy": 27.3571,
    "force_cad": 72.947,
    "force_chf": 60.2784,
    "force_aud": 76.1356
  }
]
`

### force_snapshots_v2

- rows: 16472
- symbol_col: symbol
- time_col: created_at
- horizon_status: THIN_SYMBOL_HISTORICALLY_SPARSE
- thin_latest_gap_seconds_vs_best_ref: 179.99297800000022

per symbol:
- USDJPY | count=1610 | max_time=2026-05-15T20:45:00+00:00 | age_seconds=-10545.174519
- GBPUSD | count=11497 | max_time=2026-05-15T20:48:00+00:00 | age_seconds=-10725.167497
- EURUSD | count=2174 | max_time=2026-05-15T20:45:00+00:00 | age_seconds=-10545.149972

top symbols:
- GBPUSD: 11497
- EURUSD: 2174
- USDJPY: 1610
- AUDUSD: 397
- USDCAD: 397
- USDCHF: 397

recent rows by symbol:
- USDJPY: 5 row(s) sampled
`json
[
  {
    "id": 16556,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "USDJPY",
    "timeframe": 5,
    "bar_time": 1778877900.0,
    "bar_close_time": 1778878200.0,
    "server_time": 1778877901.0,
    "capture_time": 1778877901.0,
    "is_closed_bar": 0,
    "bid": 158.694,
    "ask": 158.697,
    "mid": 158.6955,
    "spread": null,
    "spread_points": 3.0
  },
  {
    "id": 16559,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "USDJPY",
    "timeframe": 15,
    "bar_time": 1778877900.0,
    "bar_close_time": 1778878800.0,
    "server_time": 1778877901.0,
    "capture_time": 1778877901.0,
    "is_closed_bar": 0,
    "bid": 158.694,
    "ask": 158.697,
    "mid": 158.6955,
    "spread": null,
    "spread_points": 3.0
  }
]
`
- GBPUSD: 5 row(s) sampled
`json
[
  {
    "id": 16569,
    "created_at": "2026-05-15T20:48:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bar_time": 1778878080.0,
    "bar_close_time": 1778878140.0,
    "server_time": 1778878082.0,
    "capture_time": 1778878082.0,
    "is_closed_bar": 0,
    "bid": 1.33333,
    "ask": 1.33334,
    "mid": 1.33333,
    "spread": null,
    "spread_points": 1.0
  },
  {
    "id": 16568,
    "created_at": "2026-05-15T20:47:00+00:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "bar_time": 1778878020.0,
    "bar_close_time": 1778878080.0,
    "server_time": 1778878021.0,
    "capture_time": 1778878021.0,
    "is_closed_bar": 0,
    "bid": 1.33323,
    "ask": 1.33323,
    "mid": 1.33323,
    "spread": null,
    "spread_points": 0.0
  }
]
`
- EURUSD: 5 row(s) sampled
`json
[
  {
    "id": 16555,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "EURUSD",
    "timeframe": 5,
    "bar_time": 1778877900.0,
    "bar_close_time": 1778878200.0,
    "server_time": 1778877901.0,
    "capture_time": 1778877901.0,
    "is_closed_bar": 0,
    "bid": 1.16288,
    "ask": 1.16288,
    "mid": 1.16288,
    "spread": null,
    "spread_points": 0.0
  },
  {
    "id": 16560,
    "created_at": "2026-05-15T20:45:00+00:00",
    "symbol": "EURUSD",
    "timeframe": 15,
    "bar_time": 1778877900.0,
    "bar_close_time": 1778878800.0,
    "server_time": 1778877901.0,
    "capture_time": 1778877901.0,
    "is_closed_bar": 0,
    "bid": 1.16288,
    "ask": 1.16288,
    "mid": 1.16288,
    "spread": null,
    "spread_points": 0.0
  }
]
`

## Stop rule

Do not patch engine/scoring modules. If USDJPY is absent/stale in active insertion tables, fix feed/routing/normalization upstream.

## Next action

T004-L should either close T004 with an operator action checklist, or create a minimal capture-health monitor if live diagnosis must continue.

