# RAPPORT — POWERFLOW V7.3 TOPDOWN_MARKET_READER

## Decision

V7.3 est valide comme passage de PowerFlow d'un moteur de signaux techniques vers un lecteur top-down du flux de marche.

Doctrine :

```text
HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS
```

## Probleme traite

V7.2.1 sait lire beaucoup de briques : data health, signal adaptive, ontology, cross-symbol, M1 context, node, energy. Mais la remontee reste trop technique et trop locale.

Le besoin trader est top-down :

1. Weekly / Daily / H4 : zones, rotations, correlations, coalitions, provenance, tendance nouvelle.
2. H1 / M30 / M15 : plan de jour.
3. M15 / M5 / M1 : conditions d'attention et entree trader.

## Solution V7.3

Creation d'une couche d'assemblage : `TOPDOWN_MARKET_READER`.

Elle ne cherche pas a prendre une decision. Elle produit une lecture exploitable :

- Flux HTF.
- Zone de reaction.
- Driver cross-symbol.
- Plan MTF.
- Condition LTF.
- Intention machine candidate.
- Fragilites techniques.
- Journal quotidien pre-rempli.

## Briques livrees

- `pf_price_schema_probe.py`
- `pf_htf_context_reader.py`
- `pf_zone_rotation_mapper.py`
- `pf_mtf_day_plan_builder.py`
- `pf_ltf_execution_condition_reader.py`
- `pf_daily_market_reader.py`
- `run_topdown_market_reader_once.py`
- `run_topdown_market_reader_all_once.py`
- `dashboard_normalize_topdown_reader.py`
- `dashboard_topdown_reader_card_patch.html`
- `dashboard_inject_topdown_reader_card.py`

## Outputs principaux

```text
output/dashboard_surface/{symbol}/topdown_market_reading.json
output/daily_journal/{symbol}/{date}_topdown_market_reading.json
output/daily_journal/{symbol}/{date}_topdown_market_reading.md
output/dashboard_surface/topdown_market_reader.json
output/dashboard_surface/topdown_reader.json
```

## Contraintes respectees

- DB read-only.
- Pas de BUY/SELL.
- Pas de decision de trade.
- M1 jamais censure, seulement qualifie.
- Si OHLC absent, PowerFlow qualifie la limite au lieu d'inventer des niveaux.
- Dashboard principal parle flux, pas maths brutes.

## Risques techniques connus

- Si la DB ne contient pas OHLC, les zones/sweeps/close position seront limites.
- Si Weekly/Daily/H4 sont trop fins, la lecture HTF sera immature.
- Si EURUSD/USDJPY viennent d'etre branches, la profondeur structurelle peut etre faible.
- La detection de zones V0 est volontairement simple et devra etre calibree apres observation.

## Suite recommandee

1. Installer V7.3.
2. Auditer `price_schema_probe.json`.
3. Comparer la fiche `.md` journaliere avec la lecture trader.
4. Corriger la logique de zones selon les vrais retours visuels.
5. Ajouter ensuite `CATALYST_PRECHECK`.
