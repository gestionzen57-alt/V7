# T009 PHASE 2C.2 — GPT-8 REPORT — B8 DATA VISIBILITY

**Date :** 2026-05-16  
**Scope :** Data Visibility B8 multidevise  
**Statut :** Implémenté et testé localement dans `/mnt/data/Core`  

---

## 1. Livrables produits

```text
Core/pf_b8_data_visibility.py
Core/tests/test_t009_phase2c2_data_visibility.py
Core/docs/Reports/T009_PHASE2C2_GPT8_REPORT.md
```

Le module est autonome, read-only contre SQLite, et ne dépend pas du cockpit ou du dashboard.

---

## 2. Doctrine appliquée

B8 est traité comme **moteur de champ multidevise**, pas comme simple cross-symbol.

Le module ne décide pas du marché et ne bloque pas la perception. Il qualifie la preuve :

```text
PRIMARY       = preuve forte possible
CONTEXT_ONLY  = témoin contextuel / poids abaissé
EXCLUDED      = donnée absente ou structure critique
```

Les symboles THIN restent visibles, mais ne deviennent pas preuves primaires.

---

## 3. Fonctions livrées

### `B8DataVisibilityChecker.check_symbol_visibility(symbol, db_path)`

Retourne :

```json
{
  "symbol": "USDJPY",
  "source_table": "force_snapshots",
  "coverage_state": "THIN",
  "coverage_count": 20,
  "freshness_state": "STALE",
  "last_update_age_sec": 1200,
  "available_tfs": ["M5", "M15", "M30", "H1", "H4"],
  "missing_tfs": ["D1", "W1"],
  "role_allowed": "CONTEXT_ONLY",
  "technical_risks": ["KNOWN_SPARSE_SYMBOL", "LOW_SAMPLE_COUNT", "FEED_INTERMITTENT"],
  "b8_weight_cap": 0.25,
  "data_quality_score": 0.35
}
```

### `B8DataVisibilityChecker.check_b8_universe_visibility(symbols, db_path)`

Retourne un état du champ :

```json
{
  "universe": "B8_13_CURRENT",
  "symbols_expected": 13,
  "symbols_present": 5,
  "symbols_dense": 1,
  "symbols_normal": 2,
  "symbols_thin": 2,
  "symbols_missing": 8,
  "primary_symbols": ["GBPUSD"],
  "context_only_symbols": ["AUDUSD", "EURUSD", "USDCAD", "USDJPY"],
  "excluded_symbols": ["NZDUSD"],
  "field_visibility": "CRITICAL"
}
```

---

## 4. Source table detection

Le module détecte automatiquement :

```text
force_snapshots_v2
force_snapshots
```

Règle :

```text
1. Préférer force_snapshots_v2 si elle existe et contient des lignes pour le symbole.
2. Fallback force_snapshots si v2 est absente ou vide pour le symbole.
3. Exposer source_table dans chaque résultat.
```

Cela évite les faux `MISSING` pendant une migration partielle entre `force_snapshots` et `force_snapshots_v2`.

---

## 5. D1 / W1

D1/W1 sont intégrés comme cible HTF, mais non bloquants pour le B8 actuel.

```text
M5/M15/M30/H1/H4 = minimum requis actuel
D1/W1             = future HTF target
```

Si D1/W1 manquent :

```text
technical_risk = HTF_D1_W1_MISSING
```

Mais le symbole peut rester `PRIMARY` si M5-H4 sont présents, couverture dense, et fraîcheur live.

---

## 6. USDJPY THIN

USDJPY est traité comme cas connu, mais la logique reste générique.

Pour USDJPY THIN :

```text
role_allowed   = CONTEXT_ONLY
b8_weight_cap  = 0.25
risks          = KNOWN_SPARSE_SYMBOL, LOW_SAMPLE_COUNT, FEED_INTERMITTENT
```

Pour tout autre symbole THIN :

```text
role_allowed   = CONTEXT_ONLY si freshness utilisable et TF minimum présent
b8_weight_cap  = 0.35
risks          = LOW_SAMPLE_COUNT, SPARSE_SYMBOL
```

Donc la correction ne hardcode pas l’idée que seul USDJPY peut être sparse.

---

## 7. Universe handling

La méthode `check_b8_universe_visibility()` accepte une liste arbitraire :

```text
13 symboles exacts B8 actuel → B8_13_CURRENT
28 symboles exacts cible     → B8_28_TARGET
autre liste                  → B8_CUSTOM
```

Cela prépare l’extension future vers la matrice FX complète 28 paires.

---

## 8. Tests

Tests créés :

```text
test_checker_init
test_check_symbol_dense_live_primary
test_check_symbol_normal_live_context_or_primary
test_check_symbol_thin_stale_usdjpy_context_only
test_check_symbol_missing_data_excluded
test_source_table_detection_prefers_v2
test_d1_w1_missing_is_risk_not_blocker
test_incomplete_minimum_tf_excluded
test_b8_universe_visibility_current
test_b8_universe_custom_and_28_target
test_technical_risks_generic_thin_not_only_usdjpy
test_last_update_age_calculation
test_missing_db_path_returns_safe_state
```

Résultat local attendu :

```text
13 passed
```

---

## 9. Intégration Phase 2C.3

Phase 2C.3 cross-symbol / battlefield multidevise devra consommer cette visibilité :

```python
visibility = checker.check_b8_universe_visibility(symbols, db_path)
state = visibility["detail"][symbol]
weight = state["b8_weight_cap"]
role = state["role_allowed"]
```

Règle :

```text
PRIMARY peut contribuer fortement.
CONTEXT_ONLY contribue avec b8_weight_cap.
EXCLUDED ne doit pas peser dans coalition/leader/follower.
```

---

## 10. Risques techniques restants

```text
- Les schémas DB réels peuvent utiliser un nom de colonne timeframe différent.
- Si force_snapshots_v2 existe mais a des colonnes non standard, le fallback doit être validé sur DB réelle.
- Le seuil DENSE=200 peut être à calibrer selon cadence réelle par TF.
- D1/W1 restent non bloquants tant que l’EA n’est pas patché HTF complet.
```

---

## 11. Verdict

```text
T009 Phase 2C.2 est prêt comme garde de visibilité B8.
Il qualifie les preuves multidevises sans les censurer.
USDJPY THIN reste visible, mais son poids est plafonné.
Le module prépare B8_13 actuel et B8_28 cible.
```
