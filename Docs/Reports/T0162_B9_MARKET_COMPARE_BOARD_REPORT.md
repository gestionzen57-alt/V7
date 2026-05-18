# T0162 - B9 Market Compare Board V0 - Rapport

## Mission

Creer un board de comparaison marche pour afficher la scene actuelle face aux anciens films B6 et aux golden terrain cases.

## Livrables

- `tools/build_t0162_b9_market_compare_board.py`
- `scripts/RUN_T0162_B9_MARKET_COMPARE_BOARD_FROM_DOWNLOADS.ps1`
- `tests/test_t0162_b9_market_compare_board.py`
- `samples/b9_market_compare_board_v0/*`
- `outputs/b9_market_compare_board_v0/B9_MARKET_COMPARE_BOARD_V0.json`
- `outputs/b9_market_compare_board_v0/B9_MARKET_COMPARE_BOARD_V0.md`
- `outputs/b9_market_compare_board_v0/B9_MARKET_COMPARE_BOARD_V0_MATCHES_V0.csv`
- `outputs/b9_market_compare_board_v0/B9_MARKET_COMPARE_BOARD_V0_DIFFERENCES_V0.csv`
- `outputs/b9_market_compare_board_v0/B9_MARKET_COMPARE_BOARD_V0_TECHNICAL_RISKS_V0.csv`

## Doctrine respectee

- Read-only.
- Aucune DB.
- Aucun dashboard live direct.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilite de succes.
- Comparer n est pas predire.

## Fonctionnement

Le moteur lit les entrees runtime si elles existent, sinon le test utilise les fixtures sample. Il extrait la scene actuelle, compare par marqueurs terrain avec les films memoire et les golden cases, puis sort les similarites, differences, source quality, retest, session, center path et pieges techniques.

## Limite volontaire

Le score `compare_score` est un score de proximite documentaire/terrain. Ce n est pas un signal, pas une direction et pas une probabilite d outcome.
