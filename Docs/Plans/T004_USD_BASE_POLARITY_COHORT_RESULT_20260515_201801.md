# T004-N USD Base Polarity Cohort Test

Date: 2026-05-15T18:18:01Z

## Question

Does the pipeline reject or under-route pairs where USD is the base currency, such as USDJPY and USDCAD, while accepting USD-quote pairs such as GBPUSD and EURUSD?

## Verdict

- Verdict: USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES
- DB: Core/powerflow.db
- Watch seconds: 120

## Symbol model

- USDJPY | base=USD | quote=JPY | polarity=USD_BASE | usd_strength_sign=1
- USDCAD | base=USD | quote=CAD | polarity=USD_BASE | usd_strength_sign=1
- GBPUSD | base=GBP | quote=USD | polarity=USD_QUOTE | usd_strength_sign=-1
- EURUSD | base=EUR | quote=USD | polarity=USD_QUOTE | usd_strength_sign=-1

## Live deltas

- USDJPY | delta=0 | total=4114 | latest=2026-05-15T21:15:00+00:00 | age_seconds=-10497.888843
- USDCAD | delta=0 | total=1024 | latest=2026-05-15T21:15:00+00:00 | age_seconds=-10497.883666
- GBPUSD | delta=4 | total=36279 | latest=2026-05-15T21:19:00+00:00 | age_seconds=-10737.877086
- EURUSD | delta=0 | total=5413 | latest=2026-05-15T21:15:00+00:00 | age_seconds=-10497.870063

## Active tables

- force_snapshots | row_delta=2 | symbol_col=symbol | per_symbol_delta={"USDJPY": 0, "USDCAD": 0, "GBPUSD": 2, "EURUSD": 0}
- force_snapshots_v2 | row_delta=2 | symbol_col=symbol | per_symbol_delta={"USDJPY": 0, "USDCAD": 0, "GBPUSD": 2, "EURUSD": 0}

## Polarity risk hits

- BASE_USD_PRESENT | Core/diagnose_usdjpy_thin_bottleneck.py:236 | # Ratios versus GBPUSD baseline
- BASE_USD_PRESENT | Core/diagnose_usdjpy_thin_bottleneck.py:237 | base = out["symbols"].get("GBPUSD", {}).get("timeframes", {})
- BASE_USD_PRESENT | Core/diagnose_usdjpy_thin_bottleneck.py:444 | "If tick rate truly low, add timer-based heartbeat bar generation for USDJPY without manual DB writes.",
- QUOTE_USD_ASSUMPTION | Core/pf_lab_engine.py:799 | quote = symbol[3:].upper() if len(symbol) >= 6 else "USD"
- BASE_USD_PRESENT | Core/pf_multi_symbol_db.py:104 | - base   : base currency force, backward-compatible with GBPUSD force_gbp
- STARTS_WITH_USD_PRESENT | Core/pf_trader_attention_packet_once.py:182 | elif risk.startswith("EURUSD") or risk.startswith("USDJPY"):
- BASE_USD_PRESENT | Core/RAPPORT_ETAT_LIEUX_POWERFLOW_V721_20260511.md:55 | Committer ce rebase documentaire, puis lancer audit USDJPY.
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:4 | [string[]]$UsdBaseSymbols = @("USDJPY", "USDCAD"),
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:5 | [string[]]$UsdQuoteSymbols = @("GBPUSD", "EURUSD"),
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:28 | Log "UsdBaseSymbols = $($UsdBaseSymbols -join ',')"
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:29 | Log "UsdQuoteSymbols = $($UsdQuoteSymbols -join ',')"
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:50 | $baseJson = ($UsdBaseSymbols | ConvertTo-Json -Compress)
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:51 | $quoteJson = ($UsdQuoteSymbols | ConvertTo-Json -Compress)
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:64 | USD_BASE_SYMBOLS = $baseJson
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:65 | USD_QUOTE_SYMBOLS = $quoteJson
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:68 | ALL_SYMBOLS = list(dict.fromkeys(list(USD_BASE_SYMBOLS) + list(USD_QUOTE_SYMBOLS)))
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:68 | ALL_SYMBOLS = list(dict.fromkeys(list(USD_BASE_SYMBOLS) + list(USD_QUOTE_SYMBOLS)))
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:100 | if base == "USD":
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:103 | elif quote == "USD":
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:277 | usd_base_deltas = {sym: symbol_deltas.get(sym, 0) for sym in USD_BASE_SYMBOLS}
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:278 | usd_quote_deltas = {sym: symbol_deltas.get(sym, 0) for sym in USD_QUOTE_SYMBOLS}
- ENDS_WITH_USD_ONLY | scripts/t004_usd_base_polarity_cohort.ps1:308 | "endswith('USD')",
- ENDS_WITH_USD_ONLY | scripts/t004_usd_base_polarity_cohort.ps1:310 | ".endswith('USD')",
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:312 | "quote == 'USD'",
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:314 | "quote != 'USD'",
- STARTS_WITH_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:316 | "startswith('USD')",
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:318 | "base == 'USD'",
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:320 | "base != 'USD'",
- ENDS_WITH_USD_ONLY | scripts/t004_usd_base_polarity_cohort.ps1:386 | recommendations.append("Search and audit any symbol.endswith('USD') / quote == 'USD' filters before changing engine logic.")
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:386 | recommendations.append("Search and audit any symbol.endswith('USD') / quote == 'USD' filters before changing engine logic.")
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:388 | recommendations.append("USDCAD advanced while USDJPY did not. USD-base polarity is not globally blocked; inspect USDJPY-specific feed/Market Watch/routing.")
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:392 | recommendations.append("Both USD-base and USD-quote cohorts advance. The prior USDJPY defect may be intermittent or symbol-specific.")
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:392 | recommendations.append("Both USD-base and USD-quote cohorts advance. The prior USDJPY defect may be intermittent or symbol-specific.")
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:406 | "usd_base_symbols": USD_BASE_SYMBOLS,
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:407 | "usd_quote_symbols": USD_QUOTE_SYMBOLS,
- QUOTE_USD_ASSUMPTION | scripts/t004_usd_base_polarity_cohort.ps1:434 | md.append("Does the pipeline reject or under-route pairs where USD is the base currency, such as USDJPY and USDCAD, while accepting USD-quote pairs such as GBPUSD and EURUSD?")
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:434 | md.append("Does the pipeline reject or under-route pairs where USD is the base currency, such as USDJPY and USDCAD, while accepting USD-quote pairs such as GBPUSD and EURUSD?")
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:523 | '    assert "USDJPY" in data["usd_base_symbols"]',
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:524 | '    assert "USDCAD" in data["usd_base_symbols"]',
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:610 | git commit -m "audit(t004): test USD base polarity routing with USDCAD"
- BASE_USD_PRESENT | scripts/t004_usd_base_polarity_cohort.ps1:634 | $content += "Focus: T004-N USD base polarity cohort using USDCAD"

## Near-symbol / suffix candidates

- none

## Recommendations

- Strong suspicion: capture/routing logic favors USD-quote pairs (XXXUSD) and does not pass USD-base pairs.
- Search and audit any symbol.endswith('USD') / quote == 'USD' filters before changing engine logic.
- Keep engine/scoring untouched. This test targets capture routing and USD base/quote normalization.

## Stop rule

Do not patch Core/engine.py, pf_engine_v6_core.py, dashboard, or scoring from this result. Patch only capture routing / symbol normalization if confirmed.

## Revalidation

After fixing feed/routing, rerun:

`powershell
.\scripts\t004_usd_base_polarity_cohort.ps1 -WatchSeconds 120 -IntervalSeconds 10
.\scripts\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10
`

