# RAPPORT COMPLET — Mission Multi-Symbol Extension
**PowerFlow V7.1 | 2026-05-10 | Mission architecture paramétrique**

---

## 1. Objet de la mission

Objectif : préparer PowerFlow V7.1 à percevoir plusieurs symboles sans duplication de code.

Symboles cibles :

```text
GBPUSD
EURUSD
USDJPY
XAUUSD
```

Principe central : un seul moteur, plusieurs symboles. Les briques `pf_*` restent des moteurs de perception. Les runners `run_*` reçoivent `--symbol` ou `--symbols`. La DB est lue en read-only. La décision reste hors machine.

---

## 2. Décision d'architecture

La mission ne doit pas produire quatre variantes de chaque fichier.

Anti-pattern explicitement rejeté :

```text
run_regime_gbpusd.py
run_regime_eurusd.py
run_regime_usdjpy.py
run_regime_xauusd.py
```

Pattern retenu :

```text
run_regime_engine_once.py --symbol EURUSD
run_fractal_resonance_once.py --symbol USDJPY
run_powerflow_cycle_once.py --symbols GBPUSD,EURUSD,USDJPY,XAUUSD
```

Le mapping symbole -> colonnes force devient centralisé dans `pf_symbol_mapper.py`.

---

## 3. Fichiers livrés

### 3.1 `Core/pf_symbol_mapper.py`

Nouveau module source de vérité pour le mapping symbolique.

Fonctions clés :

```text
normalize_symbol(symbol)
parse_symbols(raw)
get_force_columns(symbol, db_columns=None)
resolve_symbol_mapping(symbol, db_columns=None)
validate_symbol_against_db(db_path, symbol)
build_force_select_sql(...)
```

Mapping initial :

```python
SYMBOL_FORCE_MAP = {
    "GBPUSD": ("force_gbp", "force_usd"),
    "EURUSD": ("force_eur", "force_usd"),
    "USDJPY": ("force_usd", "force_jpy"),
    "XAUUSD": ("force_xau", "force_usd"),
}
```

Propriété importante : si une colonne requise manque dans `force_snapshots`, le module lève une erreur explicite. Il n'y a pas de fallback silencieux.

---

### 3.2 `Core/pf_multi_symbol_db.py`

Helper read-only pour éviter de recopier les mêmes requêtes SQL dans toutes les briques.

Fonctions clés :

```text
connect_readonly(db_path)
load_pair_force_series(conn, symbol, timeframe, limit=100)
load_force_matrix(db_path, symbol, timeframes, mode="base")
```

Modes supportés :

```text
base   = force de la devise base, ex: EUR dans EURUSD
quote  = force de la devise quote, ex: USD dans EURUSD
spread = force_base - force_quote, pression symbolique paire
```

Accès DB :

```python
sqlite3.connect(f"file:{path}?mode=ro", uri=True)
```

---

### 3.3 `Core/run_multi_symbol_smoke_tests.py`

Runner de validation schema/densité multi-symbol.

Commande :

```powershell
python Core\run_multi_symbol_smoke_tests.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --tfs 1,5,15 --pretty
```

Sortie :

```text
output/multi_symbol_smoke_test.json
```

Ce runner vérifie :

```text
- présence colonne symbol
- présence colonnes force requises
- densité par timeframe et par symbol
- statut OK / PARTIAL / FAIL par symbol
```

---

### 3.4 `Core/run_fractal_resonance_once.py`

Version multi-symbol aware du runner B7.

Ajouts :

```text
--symbol GBPUSD|EURUSD|USDJPY|XAUUSD
--force-mode base|quote|spread
--output output/fractal_resonance_{symbol}.json
```

Backward compatible :

```powershell
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --pretty
```

Utilisation multi-symbol :

```powershell
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol EURUSD --tfs 1,5,15 --pretty
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol USDJPY --tfs 1,5,15 --force-mode spread --pretty
```

---

### 3.5 `Core/run_powerflow_cycle_once.py`

Version orchestrateur multi-symbol non-bloquante.

Ajouts :

```text
--symbol GBPUSD
--symbols GBPUSD,EURUSD,USDJPY,XAUUSD
--sequential
--dry-run
--output output/cycle_report.json
```

Comportement :

```text
- exécute le cycle par symbol
- une failure ne bloque pas les autres symbols
- un script absent est SKIPPED si optionnel
- chaque step écrit un statut OK / FAIL / SKIPPED / DRY_RUN
```

Commande de validation sans exécution réelle :

```powershell
python Core\run_powerflow_cycle_once.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --dry-run --pretty
```

---

### 3.6 Tests unitaires

Fichier :

```text
Core/tests/test_pf_symbol_mapper.py
```

Couvre :

```text
- normalisation des symboles
- mapping GBPUSD/EURUSD/USDJPY/XAUUSD
- validation colonnes DB OK
- validation colonnes DB manquantes
- parsing CLI multi-symbol unique
```

---

## 4. Ce qui n'est pas modifié automatiquement

### 4.1 `capture_bridge.py`

Non modifié volontairement.

Raison : dans V7.1, `capture_bridge.py` est listé comme fichier stable / intouchable sans accord global. La mission multi-symbol côté acquisition demande un changement de contrat MT4 -> DB. Ce changement doit être fait comme mission dédiée avec test live séparé.

Le kit actuel prépare toute la couche lecture/moteur/runners pour consommer une DB multi-symbol quand l'acquisition est prête.

---

### 4.2 Tous les `pf_*` existants

Je n'ai pas inventé de patch aveugle sur des fichiers sources non fournis dans ce fil.

À la place, le kit fournit :

```text
- mapper central
- helper SQL read-only
- runner smoke test
- B7 runner refactorisé
- orchestrateur multi-symbol
- pattern exact à appliquer aux autres briques
```

Cela évite de casser B1/B3/B4/B5/Node avec des remplacements textuels non vérifiés.

---

## 5. Pattern de refactor universel pour les briques B1-B7

Avant :

```python
force_gbp = load_force_snapshots(db_path, "force_gbp")
force_usd = load_force_snapshots(db_path, "force_usd")
```

Après :

```python
from pf_symbol_mapper import get_force_columns

base_col, quote_col = get_force_columns(symbol, db_columns)
force_base = load_force_snapshots(db_path, base_col, symbol=symbol)
force_quote = load_force_snapshots(db_path, quote_col, symbol=symbol)
```

Output enrichi :

```python
result["symbol"] = symbol
result["source"] = {
    "force_columns": [base_col, quote_col],
    "timeframes": requested_tfs,
    "samples": samples,
}
```

---

## 6. Validation recommandée dans ton repo

### 6.1 Compilation

```powershell
python -m py_compile Core\pf_symbol_mapper.py Core\pf_multi_symbol_db.py Core\run_multi_symbol_smoke_tests.py
python -m py_compile Core\run_fractal_resonance_once.py Core\run_powerflow_cycle_once.py
```

### 6.2 Smoke test schema DB

```powershell
python Core\run_multi_symbol_smoke_tests.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --tfs 1,5,15,30,60 --pretty
python -m json.tool .\output\multi_symbol_smoke_test.json | Out-Null
```

### 6.3 B7 multi-symbol

```powershell
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol EURUSD --tfs 1,5,15 --pretty
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol USDJPY --tfs 1,5,15 --pretty
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol XAUUSD --tfs 1,5,15 --pretty
```

Si la DB n'a pas encore les colonnes `force_eur`, `force_jpy`, `force_xau` ou les lignes correspondantes, les résultats EURUSD/USDJPY/XAUUSD peuvent être `FAIL` ou `PARTIAL`. C'est un diagnostic attendu, pas une panne du mapper.

### 6.4 Orchestrateur dry-run

```powershell
python Core\run_powerflow_cycle_once.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --dry-run --pretty
```

---

## 7. Commits recommandés

### Commit 1 — Mapper et helpers

```powershell
.\scripts\commit_multi_symbol_mapper.ps1
```

Message :

```text
Multi-Symbol: add pf_symbol_mapper universal mapper
```

### Commit 2 — B7 + orchestrateur

```powershell
.\scripts\commit_multi_symbol_b7_orchestrator.ps1
```

Message :

```text
Multi-Symbol: refactor B7 and orchestrator for symbol parameter
```

Ne pas utiliser `git add .`.

---

## 8. Risques techniques identifiés

```text
DB_SCHEMA_NOT_READY
  La table force_snapshots peut ne pas encore contenir force_eur / force_jpy / force_xau.

CAPTURE_BRIDGE_CONTRACT_PENDING
  L'acquisition multi-symbol n'est pas modifiée dans cette livraison.

PARTIAL_SYMBOL_DENSITY
  Un symbol peut avoir des lignes M1 mais pas M15/M30/H1.

RUNNER_ARGUMENT_DRIFT
  Certains anciens runners peuvent ne pas accepter --symbol ou --output.
  L'orchestrateur les marque FAIL ou SKIPPED explicitement.

TIMESTAMP_ALIGNMENT_PENDING
  B7 reste une résonance par barres, pas encore alignée par fenêtre horloge.
```

---

## 9. Checkpoint mission

```text
Mission              : Multi-Symbol Extension — socle paramétrique
Statut               : Kit d'intégration livré
Nouveaux fichiers    : pf_symbol_mapper.py, pf_multi_symbol_db.py, smoke tests
Runners patchés      : run_fractal_resonance_once.py, run_powerflow_cycle_once.py
DB write             : aucune
capture_bridge       : non modifié volontairement
Backward compatible  : GBPUSD défaut conservé
Doctrine             : perception multi-symbol, aucune décision de trade
```

---

## 10. Suite naturelle

Ordre conseillé après P0 :

```text
1. Commit mapper central
2. Vérifier DB schema réelle multi-symbol
3. Brancher capture_bridge multi-symbol en mission dédiée
4. Refactor B1/B4/B5 un par un avec SymbolMapper
5. Étendre dashboard seulement quand outputs par symbol sont stables
```
