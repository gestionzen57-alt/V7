# LEXIQUE PATCH V7.3.5b — Trader Cockpit Clarity

## WATCH_CONTEXT

Etat réservé aux paires de contexte.

Signifie : la paire apporte du contexte, mais ne doit pas voler l'attention principale du trader.

## CONFLIT DAILY/B6 vs LIVE

Daily et B6 pointent dans une direction, mais le live pousse dans le sens opposé.

Lecture : surveiller réintégration, piège inverse, second test ou bascule live.

## CONFLIT MULTI-LECTURE

Les briques ne sont pas alignées.

PowerFlow ne tranche pas. Il expose le conflit.

## CONTEXTE BAISSIER PARTIEL

Plusieurs lectures penchent vers pression PAIR_DOWN, mais l'alignement n'est pas complet.

## CONTEXTE HAUSSIER PARTIEL

Plusieurs lectures penchent vers pression PAIR_UP, mais l'alignement n'est pas complet.

## Risques traduits

- `DATA_HEALTH_STATUS_HTF_INCOMPLETE` -> HTF incomplet
- `GBPUSD_TEMPORAL_GAPS_PRESENT` -> Gaps temporels GBPUSD
- `DAILY_LOW_SAMPLE_FOR_ROTATION` -> Daily peu profond
- `WEEKLY_LOW_SAMPLE_FOR_ROTATION` -> Weekly peu profond
- `CURRENT_DAY_SAMPLE_THIN` -> Session du jour peu profonde

Les clés techniques restent dans l'audit, pas dans la lecture frontale.
