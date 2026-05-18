# T0162B — B9 Market Compare Board V0.1 Hardening

## Mission

Durcir T0162 — B9 Market Compare Board V0 sans changer sa doctrine.

Le board reste une couche de comparaison read-only. Il ne cherche pas un signal, ne produit aucune direction, aucune probabilité de succès et ne transforme jamais un film proche en prédiction.

## Optimisations livrées

1. Résolution d'entrées plus robuste :
   - chemins candidats exacts conservés ;
   - fallback récursif par nom de fichier ;
   - préférence aux fichiers sous `outputs/` et `Docs/Reports/` ;
   - exclusion de `.git`, `_extract`, `__pycache__`, caches de tests.

2. Noms de sorties alignés avec la mission T0162 :
   - `B9_MARKET_COMPARE_BOARD_MATCHES_V0.csv` ;
   - `B9_MARKET_COMPARE_BOARD_DIFFERENCES_V0.csv` ;
   - `B9_MARKET_COMPARE_BOARD_TECHNICAL_RISKS_V0.csv`.

3. Alias backward-compatible conservés :
   - `B9_MARKET_COMPARE_BOARD_V0_MATCHES_V0.csv` ;
   - `B9_MARKET_COMPARE_BOARD_V0_DIFFERENCES_V0.csv` ;
   - `B9_MARKET_COMPARE_BOARD_V0_TECHNICAL_RISKS_V0.csv`.

4. Ajout de `source_quality_summary` dans le JSON :
   - verdict de lisibilité ;
   - entrées trouvées/manquantes ;
   - marqueurs PROXY / RAW / PARTIAL / STALE / DEGRADED / UNKNOWN / MISSING ;
   - frontière doctrine : qualité source ≠ prédiction.

5. CLI non cassant par défaut :
   - `--strict-exit` ajouté pour forcer un code non-zéro si `board_state != PASS` ;
   - sans `--strict-exit`, un runtime incomplet produit un board `BLOCKED_MISSING_INPUTS` exploitable sans casser l'orchestration.

## Fichiers modifiés / ajoutés

```text
tools/build_t0162_b9_market_compare_board.py
tests/test_t0162_b9_market_compare_board.py
scripts/RUN_T0162_B9_MARKET_COMPARE_BOARD_FROM_DOWNLOADS.ps1
samples/b9_market_compare_board_v0/*
Docs/Reports/T0162B_B9_MARKET_COMPARE_BOARD_HARDENING_REPORT.md
Docs/Reports/COMMANDES_T0162B_B9_MARKET_COMPARE_BOARD_HARDENING.md
Docs/Reports/MESSAGE_CLAUDE_T0162B_B9_MARKET_COMPARE_BOARD_HARDENING.md
Docs/Reports/T0162B_B9_MARKET_COMPARE_BOARD_HARDENING_MANIFEST.json
```

## Tests sandbox

```powershell
python -m py_compile tools/build_t0162_b9_market_compare_board.py
python -m pytest -q tests/test_t0162_b9_market_compare_board.py
python tools\build_t0162_b9_market_compare_board.py --mode sample --core-root . --sample-dir samples\b9_market_compare_board_v0 --output-dir outputs\b9_market_compare_board_v0_sample --top-k 8
```

Résultat sandbox :

```text
3 passed
CLI sample PASS
```

## Contraintes respectées

```text
Read-only.
Aucune DB.
Aucun dashboard live direct.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
Comparer n'est pas prédire.
```

## Limite

Cette optimisation ne corrige pas le problème repo externe déjà observé sur `pf_behavioral_alert_mapper`. Les scripts T0162B utilisent donc un pytest ciblé T0162B au lieu d'un pytest global susceptible d'être bloqué par un test hors mission.
