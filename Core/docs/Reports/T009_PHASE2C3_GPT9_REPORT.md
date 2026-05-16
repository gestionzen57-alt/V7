# T009_PHASE2C3_GPT9_REPORT

## Résumé

- [x] Cross-symbol battlefield coalition detector
- [x] Pair driver context integration
- [x] Data visibility qualification integration
- [x] USDJPY THIN handled as context-only when visibility reports it
- [x] CLI runner
- [x] 17 tests

## Livrables

- `Core/pf_battlefield_flux_cross_symbol.py`
- `Core/run_battlefield_cross_symbol_once.py`
- `Core/tests/test_t009_phase2c3_cross_symbol.py`
- `Core/docs/Reports/T009_PHASE2C3_GPT9_REPORT.md`

## Architecture

`CrossSymbolCoalitionDetector` combines:

1. `BattlefieldFlux` states per symbol.
2. `PairDriverAnalyzer` from Phase 2C.1.
3. `B8DataVisibilityChecker` from Phase 2C.2 when present.

A compatibility fallback is included for `B8DataVisibilityChecker` so the module remains testable if Phase 2C.2 has not yet been merged locally. When Phase 2C.2 is present, the real checker is used automatically.

## Pair driver integration

For each symbol:

- split pair into base / quote
- estimate base force from battle scores
- estimate quote force from absorption scores
- compute pair driver using:
  - `pair_pressure = base_force - quote_force`
  - `pair_momentum = base_delta - quote_delta`

## Data visibility qualification

Each symbol receives:

- `coverage_state`
- `role_allowed`
- `visibility_quality`
- `technical_risks`

`PRIMARY` symbols keep full weight. `CONTEXT_ONLY` symbols are downweighted. `EXCLUDED` symbols do not contribute to leadership.

## USDJPY THIN handling

If Phase 2C.2 returns `USDJPY` as `THIN`, this module keeps it as contextual information and does not allow it to dominate the PRIMARY coalition role.

The fallback checker also labels `USDJPY` as:

```json
{
  "coverage_state": "THIN",
  "role_allowed": "CONTEXT_ONLY",
  "technical_risks": ["THIN_SYMBOL_CONTEXT_ONLY"]
}
```

## Confidence factors

Coalition strength combines:

```text
0.30 * leadership_confidence
0.30 * convergence_ratio
0.20 * divergence_resistance
0.20 * driver_clarity
```

Then confidence is qualified by data visibility.

## Tests

Command:

```powershell
python -m pytest Core/tests/test_t009_phase2c3_cross_symbol.py -q
```

Expected:

```text
17 passed
```

## CLI validation

Command:

```powershell
python Core/run_battlefield_cross_symbol_once.py --symbols GBPUSD,EURUSD,USDJPY --lookback-min 5 --output Core/output
```

Expected output file:

```text
Core/output/battlefield_cross_symbol_coalition.json
```

## Safety

- No write to `powerflow.db`
- No Telegram live
- No dashboard mutation
- No engine hook
- Read-only perception layer

## Next

Phase 3:

- DB writes
- Full LIVE orchestration
- Scheduler integration
- Dashboard final integration
