# RAPPORT MISSION — PowerFlow V7.1 Phase 1  
## Infra & Qualité — Data Quality Guard + Market Open Validator

**Date :** 2026-05-09  
**Mission :** Génération et validation des modules Phase 1 pour contrôle qualité DB + validation marché ouvert B4/B5/EIE  
**Destinataire :** Architecte PowerFlow / IA de validation  
**Statut global :** LIVRÉ — À valider côté architecture avant suite sprint

---

## 1. Objectif demandé

Produire 4 fichiers finaux, complets et exploitables :

1. `pf_data_quality_guard.py`  
2. `run_data_quality_guard_once.py`  
3. `pf_market_open_validator.py`  
4. `run_market_open_validator_once.py`

Contraintes strictes respectées :

- connexion SQLite uniquement en read-only ;
- aucune écriture DB ;
- aucun import `cockpit_*` ;
- séparation `pf_*` moteur / `run_*` CLI ;
- code typé, modulaire, compatible production ;
- sortie JSON exploitable ;
- risques uniquement techniques : stale data, gaps, insuffisance données, output figé.

---

## 2. Fichiers livrés

### 2.1 `pf_data_quality_guard.py`

Rôle : scanner `powerflow.db` depuis une date donnée sur les timeframes :

```text
1, 5, 15, 30, 60, 240, 1440
```

Fonctions principales :

- ouverture DB via :

```python
sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

- détection dynamique :
  - table `force_snapshots` ;
  - colonne temporelle (`created_at`, `timestamp`, etc.) ;
  - colonne `symbol` si présente ;
- calcul par TF :
  - nombre de lignes ;
  - premier timestamp ;
  - dernier timestamp ;
  - âge de la dernière donnée ;
  - stale data ;
  - gaps temporels supérieurs au TF attendu ;
  - échantillon de gaps ;
  - statut `PASS`, `WARN`, `FAIL`.

Sortie JSON structurée :

```json
{
  "overall_status": "PASS/WARN/FAIL",
  "technical_risks": [],
  "timeframe_reports": {
    "1": {},
    "5": {},
    "15": {},
    "30": {},
    "60": {},
    "240": {},
    "1440": {}
  }
}
```

---

### 2.2 `run_data_quality_guard_once.py`

Rôle : runner CLI pour lancer le guard qualité.

Options principales :

```powershell
--db
--since
--tfs
--pretty
--output
--stale-multiplier
--gap-tolerance
--max-gaps-sample
```

Exemple :

```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-06 --pretty
```

Exemple sortie fichier :

```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-06 --pretty --output .\output\data_quality_guard.json
```

---

### 2.3 `pf_market_open_validator.py`

Rôle : valider que les sorties ou proxies B4/B5/EIE ne sont pas figés en marché ouvert.

Blocs validés :

```json
{
  "b4": {},
  "b5": {},
  "eie": {}
}
```

Logique B4 :

- vérifie que `dominant_period_bars` n’est pas 100 % statique ;
- détecte la signature week-end/statique `dominant_period_bars = 1` ;
- mode JSON possible ;
- mode DB proxy possible via autocorrélation légère.

Logique B5 :

- vérifie que `rho`, `spearman_rho` ou `avg_rho` fluctuent ;
- mode JSON possible ;
- mode DB proxy possible via Spearman rolling entre colonnes force.

Logique EIE :

- vérifie que l’état / score EIE n’est pas figé ;
- détecte `all neutral static` ;
- mode JSON possible ;
- mode DB proxy possible via approximation :
  - zone TF15 ;
  - ratio micro TF1 / macro TF5.

Important : le validator est volontairement strict en marché ouvert.  
S’il n’y a pas de données récentes, il retourne `FAIL`, ce qui est correct.

---

### 2.4 `run_market_open_validator_once.py`

Rôle : runner CLI pour validation marché ouvert.

Options principales :

```powershell
--db
--since
--tfs
--symbol
--recent-minutes
--max-market-stale-minutes
--b4-json
--b5-json
--eie-json
--pretty
--output
```

Mode DB proxy :

```powershell
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --pretty
```

Mode avec outputs JSON existants :

```powershell
python .\run_market_open_validator_once.py `
  --db .\powerflow.db `
  --b4-json .\output\temporal_density.json `
  --b5-json .\output\spearman_gravity.json `
  --eie-json .\output\eie_snapshot.json `
  --pretty
```

---

## 3. Validation effectuée côté utilisateur

### 3.1 Compilation Python

Commande recommandée :

```powershell
python -m py_compile .\pf_data_quality_guard.py .\run_data_quality_guard_once.py .\pf_market_open_validator.py .\run_market_open_validator_once.py
```

Résultat annoncé : compilation OK.

---

### 3.2 Test `run_data_quality_guard_once.py`

Commande exécutée :

```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-06 --pretty
```

Résultat observé :

```json
{
  "overall_status": "FAIL",
  "timestamp_column": "created_at",
  "symbol_column": "symbol",
  "technical_risks": [
    "TF1440_NO_ROWS",
    "TF15_STALE_DATA",
    "TF1_STALE_DATA",
    "TF1_TEMPORAL_GAPS",
    "TF240_STALE_DATA",
    "TF30_STALE_DATA",
    "TF5_STALE_DATA",
    "TF60_STALE_DATA"
  ]
}
```

Densité lue :

```text
TF1    : 4304 rows
TF5    : 857 rows
TF15   : 286 rows
TF30   : 143 rows
TF60   : 71 rows
TF240  : 17 rows
TF1440 : 0 rows depuis 2026-05-06
```

Dernière donnée DB :

```text
2026-05-08T23:56:00+00:00
```

Interprétation technique :

- le module fonctionne ;
- `STALE_DATA` est attendu car la DB s’arrête au vendredi 8 mai 2026 23:56 UTC ;
- le test a été lancé samedi 9 mai 2026 ;
- le marché est fermé / la capture ne bouge plus ;
- `TF1440_NO_ROWS` indique qu’aucune bougie daily n’existe depuis `2026-05-06` ;
- les 9 gaps M1 sont correctement remontés.

Gaps M1 détectés :

```text
gaps_count = 9
max_gap_seconds = 300
max_gap_multiple = 5.0
```

Risque technique identifié :

```text
TEMPORAL_GAPS_M1
STALE_DATA_WEEKEND_OR_CAPTURE_STOPPED
TF1440_ABSENT_IN_SCAN_WINDOW
```

---

### 3.3 Test `run_market_open_validator_once.py`

Commande exécutée :

```powershell
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --pretty
```

Résultat observé :

```json
{
  "overall_status": "FAIL",
  "b4": {
    "status": "FAIL",
    "technical_risks": ["B4_INSUFFICIENT_DATA"]
  },
  "b5": {
    "status": "FAIL",
    "technical_risks": ["B5_INSUFFICIENT_DATA"]
  },
  "eie": {
    "status": "FAIL",
    "technical_risks": ["EIE_INSUFFICIENT_DATA"]
  },
  "technical_risks": [
    "B4_INSUFFICIENT_DATA",
    "B5_INSUFFICIENT_DATA",
    "EIE_INSUFFICIENT_DATA",
    "MARKET_DATA_STALE_OR_UNAVAILABLE"
  ]
}
```

Interprétation technique :

- comportement correct ;
- `--since 2026-05-12` est une date future au moment du test ;
- aucune ligne DB ne peut exister après cette date ;
- le validator retourne donc `FAIL`, ce qui est attendu ;
- le module refuse de valider un marché ouvert sans données fraîches.

---

### 3.4 Écriture JSON output

Commandes exécutées :

```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-06 --pretty --output .\output\data_quality_guard.json
```

```powershell
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --pretty --output .\output\market_open_validator.json
```

Résultat :

- fichiers JSON écrits ;
- aucun retour d’erreur PowerShell ;
- runners opérationnels en mode output.

---

## 4. Commandes recommandées pour validation architecte

### 4.1 Vérifier la compilation

```powershell
python -m py_compile .\pf_data_quality_guard.py .\run_data_quality_guard_once.py .\pf_market_open_validator.py .\run_market_open_validator_once.py
```

### 4.2 Vérifier la densité DB brute

```powershell
python -c "import sqlite3; c=sqlite3.connect('file:powerflow.db?mode=ro', uri=True); [print(r) for r in c.execute('SELECT timeframe, COUNT(*), MIN(created_at), MAX(created_at) FROM force_snapshots GROUP BY timeframe ORDER BY timeframe')]"
```

### 4.3 Test qualité données actuel

```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-06 --pretty
```

### 4.4 Test market validator en mode week-end / historique

À utiliser avant reprise marché pour vérifier les calculs proxy :

```powershell
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-06 --recent-minutes 6000 --max-market-stale-minutes 10080 --pretty
```

### 4.5 Test marché ouvert réel

À lancer quand MT4 / capture_bridge recommence à insérer des snapshots :

```powershell
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty --output .\output\market_open_validator.json
```

---

## 5. Verdict technique

### Ce qui est validé

- les 4 fichiers sont livrés ;
- architecture `pf_*` / `run_*` respectée ;
- read-only DB respecté ;
- pas d’import cockpit ;
- sorties JSON fonctionnelles ;
- `--pretty` fonctionnel ;
- `--output` fonctionnel ;
- détection dynamique colonnes DB fonctionnelle ;
- stale data détectée ;
- gaps M1 détectés ;
- absence de données future correctement refusée.

### Ce qui reste à valider en marché ouvert

- B4 : `dominant_period_bars` dynamique en conditions réelles ;
- B5 : `rho` fluctuant en conditions réelles ;
- EIE : état non figé si la confluence existe réellement ;
- fraîcheur DB avec `last_db_age_seconds <= 900` par défaut ;
- comportement sur capture live lundi/mardi.

---

## 6. Points de vigilance techniques

### 6.1 `TF1440_NO_ROWS`

Le guard retourne `FAIL` si TF1440 est absent depuis la date `--since`.

Deux options architecte :

1. garder strict : absence TF1440 = `FAIL` ;
2. rendre configurable : TF1440 manquant = `WARN` tant que la densité daily reste naturellement faible.

Recommandation : garder strict pour Phase 1 infra, puis ajouter une option future :

```powershell
--allow-missing-htf
```

---

### 6.2 Stale data en week-end

Le guard marque stale selon :

```text
stale_threshold = timeframe_seconds * stale_multiplier
```

C’est volontairement strict.  
En week-end, le statut `WARN` / `FAIL` est donc attendu.

Option future possible :

```powershell
--market-calendar forex
```

Mais ce n’est pas nécessaire pour Phase 1.

---

### 6.3 Market validator : mode DB proxy vs outputs réels

Le validator peut lire :

- soit les outputs JSON réels B4/B5/EIE ;
- soit calculer des proxies DB.

Pour validation finale P0, l’architecte peut préférer le mode JSON réel afin de tester les briques exactes :

```powershell
--b4-json
--b5-json
--eie-json
```

Le mode DB proxy reste utile comme garde-fou indépendant.

---

## 7. Décision demandée à l’architecte

Valider l’une des deux directions :

### Option A — Validation Phase 1 acceptée

Les modules sont acceptés comme garde qualité infra.  
Prochaine étape :

- intégrer dans `Core/` ;
- lancer après reprise marché ;
- ajouter éventuellement au Task Scheduler P1 ;
- conserver les JSON dans `output/`.

### Option B — Patch mineur avant intégration

Patchs possibles :

1. ajouter `--allow-missing-htf` pour TF1440 ;
2. ajouter `--market-closed-ok` pour éviter stale week-end ;
3. brancher directement les runners B4/B5/EIE existants au validator ;
4. produire un résumé compact type cockpit/lab.

---

## 8. Conclusion

Mission Phase 1 livrée.

Le résultat actuel `FAIL` n’indique pas une panne des fichiers.  
Il indique correctement :

```text
DB non fraîche
date future pour validation marché ouvert
TF1440 absent sur fenêtre
gaps M1 existants
```

Le comportement est conforme à un guard infra : il expose les problèmes de données sans les masquer.

Prochaine validation réelle : marché ouvert avec capture active.

---

## 9. Checklist pour suite sprint

```text
[ ] Architecte valide les 4 fichiers
[ ] Copie définitive dans Core/
[ ] py_compile côté environnement final
[ ] Test data_quality_guard en sortie output/
[ ] Test market_open_validator en mode historique week-end
[ ] Test market_open_validator mardi avec capture live
[ ] Décision sur TF1440 strict FAIL ou WARN configurable
[ ] Décision sur intégration Task Scheduler
```
