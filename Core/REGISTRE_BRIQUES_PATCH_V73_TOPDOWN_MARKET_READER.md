# REGISTRE BRIQUES PATCH — V7.3 TOPDOWN_MARKET_READER

## Brique : PRICE_SCHEMA_PROBE_V73

- Fichier : `pf_price_schema_probe.py`
- Type : audit schema read-only
- Entree : `powerflow.db`
- Sortie : `output/dashboard_surface/price_schema_probe.json`
- Role : verifier si la DB permet une lecture de niveaux OHLC ou seulement une lecture force-only.
- Ecrit DB : non

## Brique : HTF_CONTEXT_READER_V73

- Fichier : `pf_htf_context_reader.py`
- Type : moteur de lecture HTF
- Timeframes : Weekly / Daily / H4
- Role : zones, rotation, close position, angle, vitesse, provenance.
- Limite : si OHLC absent, retourne `HTF_CONTEXT_NOT_READABLE_NO_OHLC`.
- Ecrit DB : non

## Brique : ZONE_ROTATION_MAPPER_V73

- Fichier : `pf_zone_rotation_mapper.py`
- Type : moteur zones / rotation
- Timeframes : Daily / H4 / H1 / M30 / M15
- Role : `ZONE_TESTED`, `ZONE_REJECTED`, `BREAK_AND_HOLD`, `BREAK_AND_REINTEGRATE`, `ROTATION_BUILDING`.
- Ecrit DB : non

## Brique : MTF_DAY_PLAN_BUILDER_V73

- Fichier : `pf_mtf_day_plan_builder.py`
- Type : preparation de plan MTF
- Timeframes : H1 / M30 / M15
- Role : scenario A, scenario B, invalidation analytique.
- Dependances lues : data_health, signal_adaptive, cross_validation.
- Ecrit DB : non

## Brique : LTF_EXECUTION_CONDITION_READER_V73

- Fichier : `pf_ltf_execution_condition_reader.py`
- Type : qualification LTF
- Timeframes : M15 / M5 / M1
- Role : M1 microfilm, M5 relay, M15 condition, sweep candidate.
- Pas d'ordre, pas de BUY/SELL.
- Ecrit DB : non

## Brique : TOPDOWN_MARKET_READER_V73

- Fichier : `pf_daily_market_reader.py`
- Type : assembleur top-down + journal quotidien
- Role : assemble HTF -> MTF -> LTF + cross-symbol + ontology + day profile.
- Sorties : JSON dashboard + Markdown journal.
- Ecrit DB : non

## Brique : TOPDOWN_MARKET_READER_NORMALIZED_V73

- Fichier : `dashboard_normalize_topdown_reader.py`
- Type : normalizer dashboard
- Role : produire `output/dashboard_surface/topdown_reader.json`.
- Ecrit DB : non

## Brique UI : dashboard_topdown_reader_card_patch

- Fichier : `dashboard_topdown_reader_card_patch.html`
- Role : carte dashboard principale avec flux, zone, driver, condition, intention machine.
- Attributs : `data-brick`, `data-symbol`.
