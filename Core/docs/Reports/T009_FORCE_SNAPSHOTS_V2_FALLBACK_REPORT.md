# T009_FORCE_SNAPSHOTS_V2_FALLBACK_REPORT

## Resume

Correctif propre apres reset clean.

Le clone propre et la DB auditee montrent que powerflow.db ne contient pas bars_m1, mais contient force_snapshots_v2 avec:

- symbol
- timeframe
- created_at
- bid/ask/mid/spread
- open/high/low/close
- tick_volume

Le fallback T009 doit donc accepter force_snapshots_v2 comme proxy M1 reconstruit quand timeframe=1.

## Decisions

- force_snapshots_v2 ajoute comme fallback apres les noms historiques bars_m1, m1_bars, ohlc_m1, candles_m1.
- Filtre timeframe = 1 applique si la colonne existe.
- Timestamp priorise created_at, puis autres colonnes temporelles.
- Les ticks reconstruits restent tagues:
  - source_mode = M1_BAR_PROXY
  - data_visibility = RECONSTRUCTED
  - confidence_cap = 0.35
  - live_telegram_allowed = False

## Fichiers modifies

- Core/pf_battlefield_flux.py
- Core/run_battlefield_flux_once.py
- Core/tests/test_t009_force_snapshots_v2_fallback.py

## Safety

- Aucun write DB.
- Aucun Telegram live.
- Aucun engine integration.
- No BUY/SELL.
- Fallback uniquement read-only.
