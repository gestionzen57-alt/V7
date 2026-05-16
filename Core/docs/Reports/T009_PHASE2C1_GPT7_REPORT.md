# T009_PHASE2C1_GPT7_REPORT

## Resume

- [x] `pf_pair_driver_context.py` cree
- [x] `PairDriverAnalyzer` implemente
- [x] Formules `pair_pressure = base_force - quote_force`
- [x] Formules `pair_momentum = base_delta - quote_delta`
- [x] Labels FR trader
- [x] Tests Phase 2C.1 ajoutes
- [x] Aucun write `powerflow.db`

## Livrables

- `Core/pf_pair_driver_context.py`
- `Core/tests/test_t009_phase2c1_pair_driver.py`
- `Core/docs/Reports/T009_PHASE2C1_GPT7_REPORT.md`

## Architecture

Le module est volontairement pur et read-only.

`PairDriverAnalyzer` qualifie le driver d'une paire FX en comparant la force base vs quote :

```text
pair_pressure = base_force - quote_force
pair_momentum = base_delta - quote_delta
```

Doctrine appliquee :

```text
Une paire ne bouge pas parce que la base bouge.
Une paire bouge parce que la base surperforme la cotation.
Une paire baisse parce que la cotation surperforme la base.
```

## Driver types implementes

- `BASE_OUTRUNS_QUOTE`
- `QUOTE_OUTRUNS_BASE`
- `BASE_STRENGTH_DOMINANT`
- `QUOTE_STRENGTH_DOMINANT`
- `BASE_WEAKNESS_DOMINANT`
- `QUOTE_WEAKNESS_DOMINANT`
- `BOTH_UP_BASE_STRONGER`
- `BOTH_UP_QUOTE_STRONGER`
- `BOTH_DOWN_BASE_WEAKER`
- `BOTH_DOWN_QUOTE_WEAKER`
- `BASE_MOMENTUM_DOMINANT`
- `QUOTE_MOMENTUM_DOMINANT`
- `MIXED_DRIVER`

## Labels FR trader

Exemples :

```text
Base surperforme cotation (pression 0.50)
Cotation surperforme base (pression -0.50)
Les deux montent, base plus forte
Les deux baissent, cotation plus faible
Cotation tres faible (driver par faiblesse quote)
Driver mixte ou peu clair
```

## Tests

Commande :

```powershell
python -m pytest Core/tests/test_t009_phase2c1_pair_driver.py -q
```

Resultat attendu :

```text
17 passed
```

Tests couverts :

- `test_analyzer_init`
- `test_result_dataclass_available`
- `test_base_outruns_quote`
- `test_quote_outruns_base`
- `test_both_up_base_stronger`
- `test_both_up_quote_stronger`
- `test_both_down_quote_weaker`
- `test_both_down_base_weaker`
- `test_quote_weakness_dominant`
- `test_pair_pressure_calculation`
- `test_pair_momentum_calculation`
- `test_base_momentum_dominant`
- `test_quote_momentum_dominant`
- `test_driver_label_fr_correct`
- `test_handles_zero_forces`
- `test_confidence_score`
- `test_clamps_contributions_but_preserves_pressure`

## Safety validation

- Pas d'import Telegram
- Pas d'import dashboard
- Pas d'import engine
- Pas de DB write
- Pas de BUY/SELL
- Sortie = contexte de lecture uniquement

## Integration points

Phase 2C.1 est une brique de contexte.

Dependances futures probables :

- Phase 2C.2 Data Visibility B8
- Phase 2C.3 integration Battlefield/Telegram/Dashboard
- B8 multidevise : clarification base vs quote driver
- Reality Board : affichage du role reel du mouvement

## Blockers

Aucun blocker technique.

## Next

Phase 2C.2 : Data Visibility B8.
