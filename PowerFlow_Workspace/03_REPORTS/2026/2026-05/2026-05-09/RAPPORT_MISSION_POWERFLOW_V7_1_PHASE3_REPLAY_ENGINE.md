# RAPPORT MISSION — PowerFlow V7.1 Phase 3  
## Replay Engine — Reconstruction déterministe du passé

**Date :** 2026-05-09  
**Mission :** Génération du Replay Engine historique PowerFlow V7.1  
**Destinataire :** Architecte PowerFlow / IA de validation  
**Statut global :** CODE LIVRÉ EN BLOCS — À INTÉGRER ET COMPILER CÔTÉ `Core/`

---

## 1. Objectif demandé

Produire le code complet et final pour 2 fichiers :

1. `pf_replay_engine.py`
2. `lab_replay.py`

But fonctionnel :

> Extraire les snapshots historiques de `powerflow.db`, table `force_snapshots`, sur une fenêtre de temps précise, pour un symbole donné, puis reconstruire une timeline chronologique frame par frame, minute par minute, sans recalculer d’indicateurs.

Le Replay Engine doit reconstruire la perception passée de manière déterministe.

---

## 2. Doctrine respectée

Le Replay Engine ne prédit rien.  
Il ne conseille rien.  
Il ne déclenche aucune logique de trading.  
Il ne recalcule pas les briques B1/B2/B3/B4/B5/EIE.

Il se contente de :

```text
lire la mémoire DB
extraire les snapshots bruts
aligner temporellement
regrouper par minute et timeframe
sérialiser en JSON
```

Doctrine PowerFlow respectée :

```text
La machine perçoit.
Le replay reconstruit ce que la machine pouvait percevoir à ce moment passé.
Le trader / analyste / architecte interprète.
```

---

## 3. Contraintes techniques demandées

### 3.1 DB read-only

Respecté dans le code :

```python
sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

Aucune écriture DB.  
Aucun `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`.

---

### 3.2 Aucun import interdit

Respecté :

```text
Aucun import cockpit_*
Aucun import dashboard_*
Aucun import telegram_*
Aucune logique de trading
```

Imports utilisés :

```text
argparse
dataclasses
datetime
json
math
os
sqlite3
collections
pathlib
typing
logging
sys
```

---

### 3.3 Architecture fichier

Respect de la nomenclature PowerFlow :

```text
pf_replay_engine.py  → moteur / logique de lecture et reconstruction
lab_replay.py        → CLI lab / exploration historique
```

Le module moteur ne dépend pas du lab.

---

## 4. Fichier 1 — `pf_replay_engine.py`

### 4.1 Rôle

Module moteur read-only qui :

- ouvre `powerflow.db` en lecture seule ;
- inspecte dynamiquement la table `force_snapshots` ;
- détecte les colonnes :
  - timestamp ;
  - symbol ;
  - timeframe ;
- extrait les lignes correspondant à :
  - un symbole ;
  - une date ;
  - une heure de début ;
  - une heure de fin ;
- normalise les lignes ;
- groupe les snapshots par minute ;
- regroupe dans chaque minute les snapshots par timeframe ;
- produit une structure JSON stable.

---

### 4.2 Fonctions principales

#### `connect_readonly(db_path)`

Connexion SQLite stricte :

```python
sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

---

#### `parse_replay_bounds(date_value, start, end)`

Convertit :

```text
date = YYYY-MM-DD
start = HH:MM
end = HH:MM
```

en bornes UTC.

Supporte les fenêtres qui traversent minuit :

```text
start = 23:00
end = 02:00
```

Dans ce cas, `end` est interprété comme le lendemain.

---

#### `detect_timestamp_column(conn, table)`

Détection dynamique des colonnes temporelles possibles :

```text
created_at
timestamp
ts
datetime
time
bar_time
snapshot_time
```

---

#### `detect_symbol_column(conn, table)`

Détection dynamique :

```text
symbol
pair
instrument
```

Si aucune colonne n’existe, le replay fonctionne en mode non filtré et ajoute un risque technique :

```text
SYMBOL_COLUMN_MISSING_REPLAY_UNFILTERED
```

---

#### `detect_timeframe_column(conn, table)`

Détection de la colonne :

```text
timeframe
```

Si absente, le replay fonctionne mais classe les lignes dans :

```text
timeframes["unknown"]
```

Risque technique associé :

```text
TIMEFRAME_COLUMN_MISSING
```

---

#### `fetch_snapshot_rows(...)`

Extrait les lignes de `force_snapshots` dans la fenêtre demandée.

Tri :

```sql
ORDER BY timestamp_column ASC
```

---

#### `normalize_row(...)`

Normalise une ligne DB en objet `ReplayRow`.

Structure :

```json
{
  "timestamp": "2026-05-06T08:14:00+00:00",
  "minute": "2026-05-06T08:14:00+00:00",
  "timeframe": 1,
  "symbol": "GBPUSD",
  "values": {}
}
```

Le champ `values` conserve les colonnes originales de la DB sous forme JSON-safe.

---

#### `build_frames(...)`

Construit une timeline minute par minute.

Même les minutes sans rows sont conservées avec :

```json
{
  "minute": "...",
  "rows_count": 0,
  "timeframes": {}
}
```

Ce choix est important : il permet de voir les trous de perception dans le film.

---

#### `replay_window(...)`

Point d’entrée principal du moteur.

Retourne un dictionnaire sérialisable JSON :

```json
{
  "module": "pf_replay_engine",
  "version": "7.1.0",
  "db_path": "...",
  "symbol": "GBPUSD",
  "window": {},
  "frames_count": 121,
  "rows_count": 480,
  "timeframes_found": [1, 5, 15],
  "technical_risks": [],
  "frames": []
}
```

---

### 4.3 Dataclasses utilisées

Le moteur utilise des dataclasses typées :

```text
ReplayWindow
ReplayRow
ReplayFrame
ReplayReport
```

Avantages :

- structure claire ;
- sérialisation maîtrisée ;
- stabilité JSON ;
- lisibilité architecturale.

---

## 5. Fichier 2 — `lab_replay.py`

### 5.1 Rôle

CLI d’exécution pour le Replay Engine.

Appelle :

```python
replay_window(...)
write_replay_json(...)
```

puis écrit un JSON de sortie.

---

### 5.2 Arguments CLI demandés

Implémentés :

```text
--db
--symbol
--date
--start
--end
--output
--pretty
```

Argument additionnel utile :

```text
--log-level
```

Par défaut :

```text
--db powerflow.db
--log-level WARNING
```

---

### 5.3 Exemple d’exécution

```powershell
python .\lab_replay.py --db .\powerflow.db --symbol GBPUSD --date 2026-05-06 --start 08:00 --end 12:00 --output .\output\replay_2026-05-06_0800_1200.json --pretty
```

---

### 5.4 Sortie en cas d’erreur

Le CLI retourne un JSON d’erreur sur `stderr` :

```json
{
  "module": "lab_replay",
  "status": "FAIL",
  "technical_risks": ["REPLAY_ENGINE_ERROR"],
  "error": "..."
}
```

---

## 6. Structure JSON produite

### 6.1 Niveau rapport

```json
{
  "module": "pf_replay_engine",
  "version": "7.1.0",
  "generated_at": "2026-05-09T18:45:00+00:00",
  "db_path": ".\\powerflow.db",
  "table": "force_snapshots",
  "symbol": "GBPUSD",
  "window": {
    "date": "2026-05-06",
    "start": "08:00",
    "end": "12:00",
    "start_utc": "2026-05-06T08:00:00+00:00",
    "end_utc": "2026-05-06T12:00:00+00:00",
    "inclusive_end": true
  },
  "timestamp_column": "created_at",
  "symbol_column": "symbol",
  "timeframe_column": "timeframe",
  "columns": [],
  "frames_count": 241,
  "rows_count": 0,
  "timeframes_found": [],
  "technical_risks": [],
  "frames": []
}
```

---

### 6.2 Niveau frame

Une frame correspond à une minute.

```json
{
  "minute": "2026-05-06T08:14:00+00:00",
  "rows_count": 3,
  "timeframes": {
    "1": [],
    "5": [],
    "15": []
  }
}
```

---

### 6.3 Niveau row

Une row correspond à une ligne brute DB normalisée.

```json
{
  "timestamp": "2026-05-06T08:14:00+00:00",
  "minute": "2026-05-06T08:14:00+00:00",
  "timeframe": 1,
  "symbol": "GBPUSD",
  "values": {
    "created_at": "2026-05-06 08:14:00",
    "symbol": "GBPUSD",
    "timeframe": 1,
    "force_gbp": 0.42,
    "force_usd": -0.31
  }
}
```

---

## 7. Risques techniques exposés

Le Replay Engine ajoute une liste :

```text
technical_risks
```

Risques possibles :

```text
SYMBOL_COLUMN_MISSING_REPLAY_UNFILTERED
TIMEFRAME_COLUMN_MISSING
NO_REPLAY_ROWS
EMPTY_REPLAY_FRAMES
REPLAY_ENGINE_ERROR
```

---

### 7.1 `NO_REPLAY_ROWS`

Aucune ligne trouvée dans la fenêtre.

Causes possibles :

- mauvaise date ;
- mauvaise plage horaire ;
- symbole absent ;
- DB non alimentée ;
- marché fermé ;
- colonne timestamp mal détectée.

---

### 7.2 `EMPTY_REPLAY_FRAMES`

Certaines minutes de la timeline n’ont aucune ligne.

Ce n’est pas forcément une erreur.

Cela peut signaler :

- trou de capture ;
- absence naturelle de TF supérieur sur cette minute ;
- fenêtre sans tick/barre ;
- microfilm incomplet.

---

### 7.3 `SYMBOL_COLUMN_MISSING_REPLAY_UNFILTERED`

La table ne contient pas de colonne symbole identifiable.

Le replay continue, mais ne peut pas filtrer par symbole.

---

### 7.4 `TIMEFRAME_COLUMN_MISSING`

La table ne contient pas de colonne timeframe identifiable.

Le replay continue mais range les lignes dans :

```text
timeframes["unknown"]
```

---

## 8. Commandes de validation recommandées

### 8.1 Compilation

```powershell
python -m py_compile .\pf_replay_engine.py .\lab_replay.py
```

---

### 8.2 Replay simple

```powershell
python .\lab_replay.py --db .\powerflow.db --symbol GBPUSD --date 2026-05-06 --start 08:00 --end 09:00 --output .\output\replay_test.json --pretty
```

---

### 8.3 Replay session complète

```powershell
python .\lab_replay.py --db .\powerflow.db --symbol GBPUSD --date 2026-05-06 --start 08:00 --end 12:00 --output .\output\replay_2026-05-06_0800_1200.json --pretty
```

---

### 8.4 Replay crossing midnight

```powershell
python .\lab_replay.py --db .\powerflow.db --symbol GBPUSD --date 2026-05-06 --start 23:00 --end 02:00 --output .\output\replay_overnight.json --pretty
```

---

### 8.5 Inspection rapide JSON PowerShell

```powershell
Get-Content .\output\replay_test.json -TotalCount 80
```

---

### 8.6 Vérifier nombre de frames

```powershell
python -c "import json; d=json.load(open('.\output\replay_test.json', encoding='utf-8')); print(d['frames_count'], d['rows_count'], d['timeframes_found'], d['technical_risks'])"
```

---

## 9. Points à valider par l’architecte

### 9.1 Format timestamp DB

Le code utilise une comparaison SQL directe entre la colonne timestamp et des strings ISO sans timezone :

```text
YYYY-MM-DD HH:MM:SS
```

C’est compatible avec les sorties observées précédemment :

```text
created_at = 2026-05-08T23:56:00 ou 2026-05-08 23:56:00
```

À valider sur DB réelle.

---

### 9.2 Inclusion de la minute de fin

Le moteur utilise une fenêtre inclusive :

```text
timestamp >= start
timestamp <= end
```

Et construit les frames jusqu’à la minute `end` incluse.

Décision architecte possible :

- garder inclusif ;
- passer à `[start, end[` pour alignement plus strict type pandas/time-series.

Statut actuel :

```text
inclusive_end = true
```

---

### 9.3 Conservation des minutes vides

Le moteur conserve les frames sans données.

Avantage :

- les trous de perception sont visibles ;
- le film temporel garde son axe minute ;
- utile pour lab/replay.

Inconvénient :

- JSON plus volumineux.

Décision proposée :

- conserver ce comportement pour V7.1 ;
- ajouter plus tard `--drop-empty-frames` si nécessaire.

---

### 9.4 Pas de recalcul indicateurs

Le moteur ne recalcule volontairement rien.

Il ne produit pas :

```text
B4
B5
EIE
Node
Regime
Cascade
```

Il reconstruit uniquement les snapshots disponibles.

C’est conforme à la mission.

---

## 10. Limites actuelles

### 10.1 Pas de pagination / streaming

Le moteur charge les rows de la fenêtre en mémoire.

Pour des fenêtres courtes ou sessions de quelques heures, c’est acceptable.

Si l’architecte prévoit du replay multi-jour lourd, patch possible :

```text
streaming rows
chunked JSON
max_rows guard
```

---

### 10.2 Timezone supposée UTC

Le moteur traite les dates/heures comme UTC.

Si les timestamps DB sont en heure locale MT4, il faudra ajouter :

```powershell
--timezone
```

ou :

```powershell
--offset-hours
```

Pour V7.1, ce n’était pas demandé.

---

### 10.3 Sortie brute potentiellement lourde

Chaque row contient `values` avec toutes les colonnes DB.

Avantage :

- replay complet ;
- aucune perte d’information ;
- pas de dépendance à une liste de colonnes.

Inconvénient :

- JSON volumineux.

Patch futur possible :

```powershell
--columns force_gbp,force_usd,price
```

---

## 11. Décision demandée à l’architecte

### Option A — Accepter Phase 3 telle quelle

Le Replay Engine est validé comme première couche de reconstruction historique brute.

Suite naturelle :

```text
Phase 3.1 — replay film enrichi
Phase 3.2 — superposition alertes behavioral_alert_queue
Phase 3.3 — replay B4/B5/EIE outputs JSON
Phase 3.4 — lab_film_engine
```

---

### Option B — Patch mineur avant intégration

Patchs possibles :

1. ajouter `--drop-empty-frames` ;
2. ajouter `--table` dans CLI ;
3. ajouter `--timezone` ou `--offset-hours` ;
4. ajouter `--columns` pour alléger JSON ;
5. passer la fenêtre en `[start, end[` au lieu de inclusive.

---

## 12. Verdict technique

Mission Phase 3 livrée sous forme de code complet.

Le design respecte :

```text
read-only DB
pas d’import cockpit/dashboard/telegram
pas de logique trading
pas de recalcul indicateurs
sortie JSON déterministe
dataclasses typées
timeline minute par minute
```

Le Replay Engine devient la première brique de film historique PowerFlow :

```text
pas encore une interprétation,
pas encore un lab comportemental complet,
mais la bande brute du passé.
```

---

## 13. Checklist intégration

```text
[ ] Créer pf_replay_engine.py dans Core/
[ ] Créer lab_replay.py dans Core/
[ ] Lancer py_compile
[ ] Exécuter replay court 1h
[ ] Vérifier output JSON
[ ] Vérifier rows_count > 0 sur fenêtre connue
[ ] Vérifier timeframes_found
[ ] Vérifier frames vides / non vides
[ ] Décider inclusive_end vs start/end strict
[ ] Décider conservation des empty frames
[ ] Commit si validé
```

---

*Rapport mission — PowerFlow V7.1 Phase 3 — Replay Engine*
