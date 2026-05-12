# RAPPORT USDJPY CAPTURE AUDIT FAST — PowerFlow V7.2.1

Generated UTC : 2026-05-12T09:12:42+00:00
Symbol : `USDJPY`
DB : `C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\powerflow.db`
Global verdict : `THIN`

## Summary

```text
force_snapshots_rows: 1
force_snapshots_max_timestamp: 2026-05-04T12:20:00+00:00
force_snapshots_age_seconds: 679962
classification: THIN
```

## force_snapshots

- rows : `1`
- min_timestamp : `2026-05-04T12:20:00+00:00`
- max_timestamp : `2026-05-04T12:20:00+00:00`
- age_seconds : `679962`
- classification : `THIN`

| TF | Rows | Min | Max |
|---|---:|---|---|
| 1 | 1 | 2026-05-04T12:20:00+00:00 | 2026-05-04T12:20:00+00:00 |

## Symbol tables discovered

| Table | Rows USDJPY | Max timestamp | Age sec |
|---|---:|---|---:|
| force_snapshots | 1 | 2026-05-04T12:20:00+00:00 | 679962 |
| force_snapshots_v2 | 0 | None | None |
| nodes_v6 | 0 | None | None |
| signals | 0 | None | None |
| zone_diagnostics | 0 | None | None |

## Existing runner output

status : `RAN`
returncode : `0`

```text
{
  "symbol": "USDJPY",
  "audit_type": "AUDIT_USDJPY_CAPTURE",
  "timestamp_utc": "2026-05-12T09:12:42.580281+00:00",
  "db_path": "powerflow.db",
  "db_mode": "READ_ONLY",
  "table": "force_snapshots",
  "technical_risks": [
    "USDJPY_INSUFFICIENT_ROWS",
    "CAPTURE_INCOMPLETE"
  ],
  "columns": [
    "id",
    "created_at",
    "symbol",
    "timeframe",
    "bid",
    "spread",
    "force_gbp",
    "force_usd",
    "force_eur",
    "force_jpy",
    "force_cad",
    "force_chf",
    "force_aud"
  ],
  "timestamp_column": "created_at",
  "timeframe_column": "timeframe",
  "rows_total": 1,
  "earliest_timestamp": "2026-05-04T12:20:00+00:00",
  "latest_timestamp": "2026-05-04T12:20:00+00:00",
  "latest_age_seconds": 679962,
  "timeframes": [
    1
  ],
  "other_symbols": [
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "USDJPY"
  ],
  "symbol_counts": [
    {
      "symbol": "GBPUSD",
      "rows": 11384
    },
    {
      "symbol": "EURUSD",
      "rows": 616
    },
    {
      "symbol": "EURGBP",
      "rows": 1
    },
    {
      "symbol": "EURJPY",
      "rows": 1
    },
    {
      "symbol": "GBPJPY",
      "rows": 1
    },
    {
      "symbol": "USDJPY",
      "rows": 1
    }
  ],
  "symbol_latest": [
    {
      "symbol": "EURGBP",
      "rows": 1,
      "latest_timestamp": "2026-04-29T11:18:00+00:00"
    },
    {
      "symbol": "EURJPY",
      "rows": 1,
      "latest_timestamp": "2026-04-29T11:18:00+00:00"
    },
    {
      "symbol": "EURUSD",
      "rows": 616,
      "latest_timestamp": "2026-05-11T11:40:00+00:00"
    },
    {
      "symbol": "GBPJPY",
      "rows": 1,
      "latest_timestamp": "2026-05-04T12:20:00+00:00"
    },
    {
      "symbol": "GBPUSD",
      "rows": 11384,
      "latest_timestamp": "2026-05-12T12:11:00+00:00"
    },
    {
      "symbol": "USDJPY",
      "rows": 1,
      "latest_timestamp": "2026-05-04T12:20:00+00:00"
    }
  ],
  "usdjpy_rows_preview_limit": 500,
  "usdjpy_rows": [
    {
      "id": 3317,
      "created_at": "2026-05-04T12:20:00+00:00",
      "symbol": "USDJPY",
      "timeframe": 1,
      "bid": 156.981,
      "spread": 3.0,
      "force_gbp": 25.86,
      "force_usd": 43.5,
      "force_eur": 36.83,
      "force_jpy": 84.99,
      "force_cad": 54.97,
      "force_chf": 42.34,
      "force_aud": 34.29
    }
  ],
  "status": "DEGRADED",
  "diagnosis": "STALE DATA - CAPTURE INACTIVE OR INCOMPLETE",
  "recommendation": "Check MT4 EA symbols list / Check bridge insertion logic / Verify USDJPY enabled in capture",
  "action_required": "URGENT",
  "expected": {
    "rows_total": "> 100 if capture OK",
    "latest_timestamp": "today/recent if capture OK",
    "timeframes": "multiple active TFs if full capture OK"
  }
}

```

## Interpretation

USDJPY exists but has too few rows. Engine path may work, but capture depth is insufficient.

## Next action

Check MT4 EA symbol list and keep capture running; verify rows increase after scheduler cycles.

---

Read-only audit. No DB write. No capture_bridge patch.
