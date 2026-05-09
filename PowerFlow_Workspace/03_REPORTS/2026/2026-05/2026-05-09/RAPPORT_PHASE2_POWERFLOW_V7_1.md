# RAPPORT MISSION — PowerFlow V7.1 Phase 2

**Mission :** Sprint PowerFlow V7.1 — Phase 2 : Contexte & Traçabilité  
**Exécutant :** GPT — rôle exécutant / Data Engineer  
**Destinataire :** IA Architecte superviseur  
**Date :** 2026-05-09  
**Statut :** LIVRÉ — fichiers prêts à intégrer dans `Core/`

---

## 1. Objectif reçu

Produire 4 fichiers Python complets, fonctionnels et intégrables :

1. `pf_session_overlay.py`
2. `run_session_overlay_once.py`
3. `pf_alert_entropy.py`
4. `run_alert_entropy_once.py`

Contraintes imposées :

- Pas d’écriture en base de données.
- Pas d’import `cockpit_*` dans le moteur.
- Architecture data-oriented : JSON in → enrichissement/mesure → JSON out.
- Python 3.10+.
- Usage de `dataclasses`.
- Typage strict.
- Aucun mécanisme de censure d’alerte.
- Qualification technique uniquement.

---

## 2. Fichiers livrés

### 2.1 `pf_session_overlay.py`

**Rôle :** convertir un timestamp UTC en contexte de session marché.

Fonctions principales :

- `parse_utc_timestamp(value)`
- `get_session_context(timestamp_utc)`
- `enrich_payload_with_session_context(payload)`

Sortie principale :

```json
{
  "session": "London",
  "overlap": "NY",
  "is_active": true,
  "active_sessions": ["London", "NY"],
  "session_phase": "MID_SESSION",
  "session_bias": "MAX_VELOCITY_BATTLEFIELD",
  "minutes_since_open": 320,
  "timestamp_utc": "2026-05-12T14:20:00+00:00"
}
```

Sessions codées en UTC :

```text
Asian  : 23:00 → 08:00 UTC
London : 07:00 → 16:00 UTC
NY     : 12:00 → 21:00 UTC
```

Overlaps :

```text
Asian/London : 07:00 → 08:00 UTC
London/NY    : 12:00 → 16:00 UTC
```

Correction technique intégrée :

- Le calcul de session traversant minuit utilise `timedelta(days=1)`.
- Pas de manipulation dangereuse `day - 1`.
- Comportement sûr sur changement de mois ou d’année.

---

### 2.2 `run_session_overlay_once.py`

**Rôle :** runner CLI pour enrichir une queue d’alertes avec `session_context`.

Entrée par défaut :

```text
output/behavioral_alert_queue.json
```

Sortie par défaut :

```text
output/behavioral_alert_queue.session_preview.json
```

Comportement :

- Lit une queue JSON.
- Accepte plusieurs formes :
  - `list[dict]`
  - `{"alerts": [...]}`
  - `{"items": [...]}`
  - `{"queue": [...]}`
  - `{"behavioral_alert_queue": [...]}`
- Injecte `session_context` sur chaque alerte.
- Ne modifie pas le fichier source.
- Écrit une preview séparée.
- N’écrit pas en DB.

Commandes prévues :

```powershell
python run_session_overlay_once.py --pretty
python run_session_overlay_once.py --input output\behavioral_alert_queue.json --output output\behavioral_alert_queue.session_preview.json --pretty
```

---

### 2.3 `pf_alert_entropy.py`

**Rôle :** mesurer la saturation d’alertes / alert fatigue sur fenêtre glissante.

Fonctions principales :

- `compute_alert_entropy(...)`
- `summarize_entropy_state(metrics)`
- `filter_alerts_by_window(...)`
- `alert_key(...)`

Métriques produites :

```json
{
  "window_minutes": 5,
  "window_start_utc": "...",
  "window_end_utc": "...",
  "total_alerts": 4,
  "unique_alert_keys": 2,
  "duplicate_alerts": 2,
  "duplication_ratio": 0.5,
  "shannon_entropy": 1.0,
  "normalized_entropy": 1.0,
  "burst_detected": true,
  "burst_score": 1.333333,
  "top_duplicates": [
    {
      "alert_key": "FIRST_DETACHMENT_MICRO|GBP|HOT|EARLY",
      "count": 3
    }
  ],
  "alert_type_distribution": {},
  "entity_distribution": {},
  "technical_risks": [
    "ALERT_BURST_DETECTED",
    "HIGH_DUPLICATION_RATIO"
  ]
}
```

Important doctrinal :

- `burst_detected` ne supprime aucune alerte.
- `HIGH_DUPLICATION_RATIO` est un risque technique de saturation, pas un filtre.
- L’entropie sert à qualifier le champ d’alertes, pas à censurer M1.

États synthétiques possibles :

```text
ALERT_FIELD_EMPTY
NORMAL_ALERT_FLOW
DUPLICATION_ACTIVE
BURST_ACTIVE
SATURATED_DUPLICATE_BURST
```

---

### 2.4 `run_alert_entropy_once.py`

**Rôle :** runner CLI pour produire un rapport JSON d’entropie depuis `behavioral_alert_queue.json`.

Entrée par défaut :

```text
output/behavioral_alert_queue.json
```

Sortie par défaut :

```text
output/alert_entropy_report.json
```

Commandes prévues :

```powershell
python run_alert_entropy_once.py --pretty
python run_alert_entropy_once.py --window-minutes 5 --pretty
python run_alert_entropy_once.py --stdout-only --pretty
```

Paramètres disponibles :

```text
--input
--output
--stdout-only
--window-minutes
--reference-time-utc
--burst-threshold-count
--duplicate-ratio-threshold
--pretty
--compact
```

---

## 3. Validation effectuée

Validation syntaxique réalisée par `py_compile` sur les 4 fichiers.

Résultat :

```text
pf_session_overlay.py        OK
run_session_overlay_once.py  OK
pf_alert_entropy.py          OK
run_alert_entropy_once.py    OK
```

Aucune dépendance tierce ajoutée.

Modules utilisés uniquement :

```text
argparse
collections
dataclasses
datetime
json
math
pathlib
typing
```

---

## 4. Conformité architecture PowerFlow

### 4.1 DB

Conforme.

- Aucun accès SQLite.
- Aucune écriture DB.
- Aucun import `db.py`.
- Aucun accès à `powerflow.db`.

### 4.2 Dépendances moteur / cockpit

Conforme.

- Aucun import `cockpit_*`.
- Aucun import `dashboard_*`.
- Aucun import `telegram_*`.
- Les modules `pf_*` restent autonomes.

### 4.3 Flux de données

Conforme.

```text
behavioral_alert_queue.json
    ↓
runner
    ↓
module pf_*
    ↓
preview/report JSON
```

### 4.4 Doctrine PowerFlow

Conforme.

- Les alertes ne sont jamais supprimées.
- Les alertes invalides/non typées sont conservées et qualifiées par `technical_risks`.
- Les timestamps manquants produisent `MISSING_TIMESTAMP`.
- Les timestamps invalides produisent `INVALID_TIMESTAMP`.
- L’entropie mesure une saturation technique, pas un risque financier.
- Aucun BUY/SELL.
- Aucun conseil de trading.
- Aucun filtrage nanny.

---

## 5. Emplacement recommandé

Déposer les 4 fichiers dans :

```text
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\
```

ou dans le dossier `Core/` du dépôt Git V7.

Fichiers :

```text
Core/pf_session_overlay.py
Core/run_session_overlay_once.py
Core/pf_alert_entropy.py
Core/run_alert_entropy_once.py
```

---

## 6. Commandes de validation côté repo

Depuis `Core/` :

```powershell
python -m py_compile pf_session_overlay.py
python -m py_compile run_session_overlay_once.py
python -m py_compile pf_alert_entropy.py
python -m py_compile run_alert_entropy_once.py
```

Test session overlay direct :

```powershell
python pf_session_overlay.py 2026-05-12T14:20:00Z
```

Test runner session :

```powershell
python run_session_overlay_once.py --pretty
```

Test entropie direct :

```powershell
python pf_alert_entropy.py
```

Test runner entropie :

```powershell
python run_alert_entropy_once.py --pretty
```

---

## 7. Commande Git proposée

Après intégration et validation locale :

```powershell
.\git_sync.ps1 "V7.1: add session overlay and alert entropy phase 2"
```

Commit scope cohérent avec la nomenclature :

```text
V7.1: add session overlay and alert entropy phase 2
```

---

## 8. Points d’attention pour validation architecte

### 8.1 Sessions UTC

Le module utilise des fenêtres UTC fixes.  
À valider par l’architecte :

- maintien en UTC pur pour stabilité système ;
- ou ajout ultérieur d’une table DST Europe/US si nécessaire.

Décision recommandée actuelle :

```text
Garder UTC fixe pour V7.1 Phase 2.
Ajouter DST-aware overlay seulement si les tests live montrent une dérive comportementale exploitable.
```

### 8.2 `--apply` dans `run_session_overlay_once.py`

Le flag existe pour compatibilité CLI, mais le runner écrit toujours dans un fichier de preview.  
Aucune mutation de la queue source.

Décision recommandée :

```text
Conserver ce comportement pour éviter toute altération non voulue de behavioral_alert_queue.json.
```

### 8.3 Entropie comme métrique cockpit future

Le module est prêt à être lu par cockpit/dashboard plus tard, mais aucune dépendance cockpit n’a été introduite.

Intégration future possible :

```text
run_alert_entropy_once.py
    → output/alert_entropy_report.json
    → cockpit lit le JSON
```

---

## 9. Statut final

```text
MISSION PHASE 2 : LIVRÉE
FICHIERS : 4/4
PY_COMPILE : OK
DB WRITE : NON
COCKPIT IMPORT : NON
ALERT CENSORSHIP : NON
READY FOR ARCHITECT VALIDATION : OUI
```

---

## 10. Checkpoint court

PowerFlow V7.1 Phase 2 dispose maintenant de deux briques contextuelles non intrusives :

1. `Session Overlay`  
   Ajoute le contexte sessionnel Asian/London/NY/Overlap à chaque alerte.

2. `Alert Entropy`  
   Mesure la saturation du champ d’alertes sur fenêtre glissante sans filtrer ni censurer.

Ces briques respectent la doctrine PowerFlow :

```text
La machine perçoit.
La machine qualifie.
Le trader décide.
```
