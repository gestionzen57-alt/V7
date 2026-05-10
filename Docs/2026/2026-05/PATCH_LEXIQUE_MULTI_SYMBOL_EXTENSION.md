# PATCH LEXIQUE — Multi-Symbol Extension
**PowerFlow V7.1 | 2026-05-10 | Section proposée : 23**

---

## 23. MULTI-SYMBOL EXTENSION

### MULTI_SYMBOL_EXTENSION
Extension paramétrique de PowerFlow permettant au moteur de percevoir plusieurs symboles (`GBPUSD`, `EURUSD`, `USDJPY`, `XAUUSD`) sans duplication de code. Le moteur reste non-prédictif : il mesure les flux par symbol, les nomme, les expose, et laisse le trader décider.

### SYMBOL_MAPPER
Module central `pf_symbol_mapper.py` qui traduit un symbol de marché vers les colonnes de force nécessaires dans `force_snapshots`.

Exemples :

```text
GBPUSD -> force_gbp, force_usd
EURUSD -> force_eur, force_usd
USDJPY -> force_usd, force_jpy
XAUUSD -> force_xau, force_usd
```

Le `SYMBOL_MAPPER` évite le hardcoding dispersé dans les briques `pf_*`.

### SYMBOL_FORCE_MAP
Dictionnaire source de vérité liant chaque symbol supporté à son couple de colonnes force.

```python
SYMBOL_FORCE_MAP = {
    "GBPUSD": ("force_gbp", "force_usd"),
    "EURUSD": ("force_eur", "force_usd"),
    "USDJPY": ("force_usd", "force_jpy"),
    "XAUUSD": ("force_xau", "force_usd"),
}
```

### FORCE_BASE_COLUMN
Colonne de force correspondant à la devise ou actif base du symbol.

Exemples :

```text
EURUSD -> force_eur
USDJPY -> force_usd
XAUUSD -> force_xau
```

### FORCE_QUOTE_COLUMN
Colonne de force correspondant à la devise quote du symbol.

Exemples :

```text
EURUSD -> force_usd
USDJPY -> force_jpy
XAUUSD -> force_usd
```

### FORCE_SPREAD_MODE
Mode de lecture où la série utilisée par une brique est calculée comme :

```text
force_base - force_quote
```

Ce mode mesure la pression relative du symbol plutôt que la force isolée de la devise base. Il est utile pour les lectures trans-symboles, notamment B7 Fractal Resonance.

### SYMBOL_AWARE_RUNNER
Runner `run_*` acceptant un argument `--symbol` avec `GBPUSD` comme valeur par défaut pour compatibilité arrière.

Exemple :

```powershell
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol EURUSD --pretty
```

### MULTI_SYMBOL_RUNNER
Runner acceptant `--symbols` pour exécuter une même brique ou un cycle complet sur plusieurs symbols.

Exemple :

```powershell
python Core\run_powerflow_cycle_once.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --pretty
```

### SYMBOL_ISOLATED_OUTPUT
Convention de sortie JSON isolée par symbol afin d'éviter les collisions entre résultats.

Exemples :

```text
output/regime_result_GBPUSD.json
output/regime_result_EURUSD.json
output/fractal_resonance_USDJPY.json
output/cycle_report.json
```

### MULTI_SYMBOL_CYCLE_REPORT
Rapport agrégé produit par l'orchestrateur multi-symbol. Il contient un bloc `symbol_results` avec le statut de chaque symbol.

Structure :

```json
{
  "timestamp": "2026-05-10T...Z",
  "symbols": ["GBPUSD", "EURUSD", "USDJPY", "XAUUSD"],
  "overall_status": "OK|PARTIAL|FAIL",
  "symbol_results": {
    "GBPUSD": {"status": "OK"},
    "EURUSD": {"status": "PARTIAL"}
  }
}
```

### PARTIAL_SYMBOL_DENSITY
État technique où un symbol possède des données sur certains timeframes mais pas sur toute la stack attendue. Exemple : `EURUSD` disponible en M1/M5 mais absent en M15/M30.

Ce n'est pas une décision de marché. C'est une information de qualité de perception.

### DB_SCHEMA_NOT_READY
Risque technique indiquant que la DB ne contient pas encore les colonnes nécessaires au multi-symbol (`force_eur`, `force_jpy`, `force_xau`) ou la colonne `symbol`.

### CAPTURE_BRIDGE_CONTRACT_PENDING
Risque technique indiquant que la couche acquisition n'a pas encore été étendue pour insérer plusieurs symbols dans `force_snapshots`. Tant que ce contrat n'est pas validé, les briques multi-symbol peuvent être prêtes côté lecture mais manquer de données réelles.

### RUNNER_ARGUMENT_DRIFT
Risque technique où certains anciens runners n'acceptent pas encore `--symbol`, `--output`, ou une autre option standard. L'orchestrateur doit exposer ce drift par step au lieu de masquer l'échec.

### SCHEMA_AWARE_SYMBOL_MAPPING
Principe selon lequel le mapping symbolique ne se contente pas d'inférer les colonnes : il valide leur présence réelle dans la DB avant de lancer une analyse. Si une colonne manque, l'erreur est explicite.

### ZERO_DUPLICATION_SYMBOL_EXTENSION
Règle d'architecture : ajouter un symbol ne doit jamais créer un clone de brique ou de runner. Le symbol est un paramètre, pas un fichier.

---

## PHRASE LEXIQUE

```text
Multi-Symbol ne multiplie pas les moteurs.
Multi-Symbol multiplie les champs de perception.
Un seul moteur, plusieurs symbols, même doctrine.
La machine perçoit. Le trader décide.
```
