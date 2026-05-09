# RAPPORT MISSION — PowerFlow V7.1 Phase 3

**Mission :** Sprint PowerFlow V7.1 — Phase 3 : Film Engine  
**Rôle exécutant :** Analyste Quantitatif / Traducteur Comportemental  
**Destinataire :** IA Architecte superviseur  
**Date :** 2026-05-09  
**Statut :** LIVRÉ — code brut fourni pour intégration dans `Core/`

---

## 1. Objectif reçu

Produire le code complet et final pour deux fichiers :

1. `pf_film_engine.py`
2. `lab_film.py`

Objectif fonctionnel :

```text
Transformer des données brutes de replay ou une queue d’alertes
en frise chronologique Markdown lisible par le trader.
```

Le Film Engine doit raconter l’histoire comportementale du flux :

- tensions ;
- compressions ;
- inflexions ;
- accélérations ;
- désynchronisations M1/M5 ;
- apparitions d’alertes ;
- cascades ;
- tentatives de rupture ;
- libérations.

Doctrine imposée :

```text
Aucune nounou.
Aucun BUY/SELL.
Aucune décision de trade.
Aucune censure d’alerte.
Traduction comportementale uniquement.
```

---

## 2. Contrat technique respecté

### 2.1 Base de données

Conforme.

```text
Aucune connexion DB directe.
Aucun import sqlite3.
Aucune écriture dans powerflow.db.
Aucun accès à force_snapshots.
```

Le moteur lit uniquement des payloads JSON ou des fichiers JSON fournis par le runner.

---

### 2.2 Frontières d’architecture

Conforme.

```text
Aucun import cockpit_*.
Aucun import dashboard_*.
Aucun import telegram_*.
Aucune dépendance vers couche affichage.
```

Le moteur reste dans la couche `pf_*`.

Le runner reste dans la couche `lab_*`.

Architecture cible :

```text
Replay Engine JSON / behavioral_alert_queue.json
    ↓
lab_film.py
    ↓
pf_film_engine.py
    ↓
reports/*.md
```

---

### 2.3 Python

Conforme à l’intention.

```text
Python 3.10+
dataclasses
typing
pathlib
json
datetime
stdlib uniquement
```

Aucune dépendance tierce introduite.

---

## 3. Fichier livré : `pf_film_engine.py`

### 3.1 Rôle

`pf_film_engine.py` est le traducteur comportemental.

Il prend :

```text
Replay JSON
+ optionnellement behavioral_alert_queue.json
```

et produit :

```text
un rapport Markdown structuré chronologiquement.
```

---

### 3.2 Entrées acceptées

Le moteur normalise plusieurs formes de payload replay :

```text
list[dict]
{"frames": [...]}
{"replay": [...]}
{"timeline": [...]}
{"snapshots": [...]}
{"items": [...]}
{"data": [...]}
{"payload": ...}
```

Pour les alertes, il accepte :

```text
list[dict]
{"alerts": [...]}
{"items": [...]}
{"queue": [...]}
{"behavioral_alert_queue": [...]}
{"payload": ...}
```

Ce choix rend le moteur robuste aux variations de format entre Replay Engine, lab et queue.

---

### 3.3 Fonctions principales

Fonctions publiques prévues :

```python
generate_film_markdown(
    replay_payload,
    alert_payload=None,
    config=None
)

generate_film_markdown_from_files(
    replay_file,
    queue_file=None,
    config=None
)

events_from_payloads(
    replay_payload,
    alert_payload=None,
    config=None
)
```

Dataclasses principales :

```python
FilmEngineConfig
FilmEvent
FilmState
```

---

### 3.4 Détection des scènes

Le moteur détecte plusieurs familles de scènes.

#### 3.4.1 INFLEXION

Déclenchée par :

```text
first_detachment = true
```

Lecture comportementale :

```text
Naissance d’une inflexion cinématique.
M1 expose une naissance de mouvement si timeframe=1.
```

---

#### 3.4.2 KINEMATIC_SHIFT

Déclenchée par :

```text
variation forte d’angle entre deux frames successives
```

Seuil par défaut :

```text
strong_angle_threshold = 35.0
```

Lecture comportementale :

```text
Changement d’angle marqué.
Accélération ou décélération visible du flux.
```

---

#### 3.4.3 M1_M5_DESYNC

Déclenchée par :

```text
écart significatif entre angle M1 courant et dernier angle M5 connu
```

Seuil par défaut :

```text
m1_m5_angle_gap_threshold = 12.0
```

Lecture comportementale :

```text
M1 prend de l’avance sur M5
ou
M1 se replie sous le relais M5
```

Important doctrinal :

```text
La désynchronisation M1/M5 n’est pas censurée.
Elle est exposée comme scène de timing.
```

---

#### 3.4.4 COMPRESSION

Déclenchée par :

```text
cycle_state contenant COMPRESS
```

Lecture comportementale :

```text
Les oscillations temporelles se compriment.
La densité augmente.
```

---

#### 3.4.5 COMPRESSION_RATIO

Déclenchée par :

```text
compression_ratio >= 0.70
```

Lecture comportementale :

```text
Compression quantitative élevée.
```

---

#### 3.4.6 ELASTIC_TENSION

Déclenchée par :

```text
elastic_tension_score >= 0.65
```

Lecture comportementale :

```text
Naissance d’une tension élastique.
```

---

#### 3.4.7 ELASTIC_SIGNATURE

Déclenchée par :

```text
tension_signature contenant ELASTIC ou LOADED
```

Lecture comportementale :

```text
Signature d’élastique chargé.
```

---

#### 3.4.8 EIE

Déclenchée par :

```text
eie_state contenant EIE ou ELASTIC
```

Lecture comportementale :

```text
Zone élastique active.
```

---

#### 3.4.9 RELEASE

Déclenchée par :

```text
release_state contenant RUPTURE, RELEASE, CONFIRMED ou ATTEMPT
```

Lecture comportementale :

```text
Libération ou tentative de rupture.
```

---

#### 3.4.10 REGIME

Déclenchée par :

```text
regime contenant COMPRESSION, TENDANCE, RANGE ou TRANSITION
```

Lecture comportementale :

```text
Contexte régime HTF qualifiant la scène.
```

---

#### 3.4.11 CASCADE

Déclenchée par :

```text
cascade_state contenant HIGH ou BUILDING
```

Lecture comportementale :

```text
Cascade d’événements en accélération.
```

---

#### 3.4.12 ALERT

Déclenchée par :

```text
présence d’une alerte dans behavioral_alert_queue.json
```

Le moteur transforme les alertes en scènes Markdown :

```text
FIRST_DETACHMENT → Alerte: premier détachement
EIE / ELASTIC    → Alerte: tension élastique
COMPRESSION      → Alerte: compression active
CASCADE          → Alerte: cascade d’événements
DIVERGENT        → Alerte: divergence relationnelle
CODEPENDANT      → Alerte: coalition ou codépendance
REGIME           → Alerte: contexte régime
RELEASE/RUPTURE  → Alerte: libération du flux
```

---

## 4. Fichier livré : `lab_film.py`

### 4.1 Rôle

`lab_film.py` est le runner CLI du Film Engine.

Il lit :

```text
--replay-file
--queue-file optionnel
```

et écrit :

```text
--output Markdown
```

---

### 4.2 Arguments CLI

Arguments implémentés :

```text
--replay-file                         requis
--queue-file                          optionnel
--output                              optionnel
--format                              markdown par défaut
--title                               titre du rapport
--no-evidence                         masque les champs evidence
--m1-m5-angle-gap-threshold            seuil désync M1/M5
--strong-angle-threshold               seuil shift angle
--compression-ratio-threshold          seuil compression
--elastic-score-threshold              seuil tension élastique
```

---

### 4.3 Sortie par défaut

Si `--output` n’est pas fourni :

```text
reports/film_<nom_replay>_<timestamp>.md
```

Exemple :

```text
reports/film_replay_20260509_231502.md
```

---

### 4.4 Commandes prévues

Depuis `Core/` :

```powershell
python lab_film.py --replay-file output\replay.json --pretty
```

Commande standard :

```powershell
python lab_film.py --replay-file output\replay.json --output reports\film.md
```

Avec queue d’alertes :

```powershell
python lab_film.py `
  --replay-file output\replay.json `
  --queue-file output\behavioral_alert_queue.json `
  --output reports\film_session.md
```

Sans evidence compacte :

```powershell
python lab_film.py `
  --replay-file output\replay.json `
  --queue-file output\behavioral_alert_queue.json `
  --output reports\film_session.md `
  --no-evidence
```

Note : le flag `--pretty` n’a pas été implémenté dans `lab_film.py`, car la sortie CLI est déjà un JSON de statut indenté. Si l’architecte veut une symétrie avec les autres runners, il peut être ajouté.

---

## 5. Format Markdown généré

Structure de sortie :

```markdown
# PowerFlow Film

**Generated at UTC:** ...
**Film dates:** ...
**Scenes detected:** ...

## Synthèse

COMPRESSION: 3, INFLEXION: 2, ALERT: 2

## Frise chronologique

### 2026-05-12

- **14:02 UTC / GBP / M1 / HOT / EARLY** — Alerte: premier détachement
  Type: FIRST_DETACHMENT_MICRO. Niveau: HOT. Maturité: EARLY.

- **14:05 UTC / GBP / M5** — Compression temporelle visible
  Les oscillations temporelles se compriment. Compression ratio: 0.780.

## Lecture PowerFlow

Le film traduit les frames et alertes en scènes comportementales.
Il expose les tensions, compressions, inflexions, désynchronisations M1/M5, cascades et libérations détectées.
Il ne filtre pas les alertes et ne transforme aucune perception en décision.
```

---

## 6. Exemple de lecture comportementale attendue

Exemple de film :

```text
14:02 UTC — Naissance d’une inflexion cinématique sur GBP M1.
14:03 UTC — M1 prend de l’avance sur M5.
14:05 UTC — Compression temporelle visible sur M5.
14:07 UTC — Tension élastique active.
14:09 UTC — Alerte FIRST_DETACHMENT_MICRO HOT EARLY.
14:11 UTC — Cascade d’événements en accélération.
14:14 UTC — Libération ou tentative de rupture.
```

Lecture PowerFlow :

```text
Le moteur ne dit pas quoi faire.
Le film raconte la séquence de perception :
naissance → désynchronisation → compression → tension → alerte → cascade → release.
```

---

## 7. Conformité doctrine PowerFlow

Conforme.

```text
Aucun BUY/SELL.
Aucun conseil de trading.
Aucun avertissement financier.
Aucune suppression d’alerte M1.
Aucun filtrage par prudence.
```

Les scènes sont des traductions comportementales :

```text
Qualifier n’est pas décider.
Raconter n’est pas ordonner.
Filmer n’est pas prédire.
```

---

## 8. Points d’attention architecte

### 8.1 Robustesse du format Replay Engine

Le moteur accepte plusieurs clés génériques (`frames`, `replay`, `timeline`, etc.), mais la structure finale du Replay Engine doit être confirmée.

Point à valider :

```text
Quel sera le format canonique du replay JSON ?
```

Recommandation :

```json
{
  "frames": [
    {
      "timestamp": "2026-05-12T14:02:00Z",
      "currency": "GBP",
      "timeframe": 1,
      "angle_kalman": 52.4,
      "speed_state": "ACCELERATING",
      "first_detachment": true,
      "noise_ratio": 0.08
    }
  ]
}
```

---

### 8.2 Seuils configurables

Les seuils sont exposés dans `FilmEngineConfig` et dans le CLI.

Seuils par défaut :

```text
m1_m5_angle_gap_threshold = 12.0
strong_angle_threshold    = 35.0
compression_ratio_threshold = 0.70
elastic_score_threshold     = 0.65
```

Ces seuils ne sont pas des vérités de marché.  
Ce sont des seuils de détection narrative pour produire des scènes.

À valider sur données réelles :

```text
- Faux positifs M1_M5_DESYNC
- Redondance COMPRESSION + COMPRESSION_RATIO
- Sensibilité ELASTIC_TENSION
```

---

### 8.3 Risque de doublons narratifs

Le Film Engine peut produire plusieurs scènes proches pour une même frame :

```text
COMPRESSION
COMPRESSION_RATIO
ELASTIC_TENSION
EIE
```

Ce comportement est volontaire en V7.1 pour ne pas censurer.

Option future possible :

```text
scene_coalescing = True
```

Rôle :

```text
Fusionner plusieurs scènes d’un même timestamp en paragraphe unique.
```

Non implémenté à cette phase.

---

### 8.4 Evidence compacte

Le Markdown peut afficher les champs `Evidence`.

Avantage :

```text
Traçabilité immédiate.
```

Risque technique :

```text
Rapport plus verbeux si beaucoup de scènes.
```

Option existante :

```powershell
--no-evidence
```

---

## 9. Emplacement recommandé

Déposer dans :

```text
Core/pf_film_engine.py
Core/lab_film.py
```

---

## 10. Validation recommandée après intégration

Depuis `Core/` :

```powershell
python -m py_compile pf_film_engine.py
python -m py_compile lab_film.py
```

Test minimal avec replay synthétique :

```powershell
python lab_film.py --replay-file output\replay_sample.json --output reports\film_sample.md
```

Avec queue :

```powershell
python lab_film.py `
  --replay-file output\replay_sample.json `
  --queue-file output\behavioral_alert_queue.json `
  --output reports\film_with_alerts.md
```

---

## 11. Exemple de replay sample pour test

```json
{
  "frames": [
    {
      "timestamp": "2026-05-12T14:02:00Z",
      "currency": "GBP",
      "timeframe": 1,
      "angle_kalman": 54.2,
      "speed_state": "ACCELERATING",
      "first_detachment": true,
      "noise_ratio": 0.08
    },
    {
      "timestamp": "2026-05-12T14:05:00Z",
      "currency": "GBP",
      "timeframe": 5,
      "angle_kalman": 31.5,
      "cycle_state": "CYCLE_COMPRESSING",
      "compression_ratio": 0.78
    },
    {
      "timestamp": "2026-05-12T14:07:00Z",
      "currency": "GBP",
      "timeframe": 1,
      "elastic_tension_score": 0.72,
      "tension_signature": "ELASTIC_LOADED",
      "eie_state": "EIE"
    }
  ]
}
```

---

## 12. Commit proposé

Après intégration et validation locale :

```powershell
.\git_sync.ps1 "V7.1: add Film Engine phase 3"
```

Alternative plus descriptive :

```powershell
.\git_sync.ps1 "Lab: add PowerFlow Film Engine markdown replay"
```

---

## 13. Statut final

```text
MISSION PHASE 3 : LIVRÉE
FICHIERS : 2/2
DB WRITE : NON
COCKPIT IMPORT : NON
ALERT CENSORSHIP : NON
OUTPUT : Markdown film
READY FOR ARCHITECT REVIEW : OUI
```

---

## 14. Checkpoint court

PowerFlow V7.1 dispose maintenant d’un Film Engine capable de transformer un replay JSON et une queue d’alertes en narration Markdown chronologique.

Le moteur raconte le flux :

```text
frame brute
→ scène comportementale
→ frise Markdown
→ lecture humaine du film
```

La machine perçoit.  
Le film raconte.  
Le trader décide.
