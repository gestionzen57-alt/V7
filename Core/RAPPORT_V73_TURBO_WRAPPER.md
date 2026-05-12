# RAPPORT — V7.3 TURBO WRAPPER

## Mission

Integrer la lecture top-down V7.3 dans le cycle automatique PowerFlow.

## Etat avant patch

Le scheduler turbo executait deja :

- moteur multi-symboles,
- data health,
- flow ontology,
- signal adaptive.

Mais V7.3 TOPDOWN_MARKET_READER restait une couche installee et testable manuellement, pas encore appelee a chaque cycle.

## Etat apres patch

Le wrapper `scheduler_powerflow_turbo_wrapper.py` execute maintenant :

1. cycle moteur multi-symboles,
2. controle sante data,
3. normalisation data health,
4. cycle ontologie,
5. signal adaptive profile,
6. normalisation signal adaptive,
7. audit schema prix / OHLC,
8. topdown market reader,
9. normalisation topdown reader.

## Effet attendu

A chaque cycle planifie, PowerFlow met a jour :

- la perception technique,
- la perception organique,
- la permission perceptive,
- le contexte top-down HTF / MTF / LTF,
- les surfaces dashboard contractuelles.

## Risques techniques

- Cycle plus long car le wrapper ajoute des couches apres le scheduler principal.
- Si une brique aval echoue, le wrapper retourne FAIL.
- Les fichiers runtime `dashboard_data.json` et les outputs JSON ne doivent pas etre commites.

## Decision

V7.3 passe du mode installe/testable au mode integre dans la boucle automatique.
