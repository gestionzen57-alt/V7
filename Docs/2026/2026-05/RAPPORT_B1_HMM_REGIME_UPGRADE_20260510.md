# RAPPORT COMPLET — B1 HMM Gaussian Regime Upgrade
**PowerFlow V7.1 — Mission B1 HMM**  
**Date : 2026-05-10**  
**Commit Git : `e1e175f` — `B1: HMM Gaussian regime upgrade`**  
**Statut : LIVRÉ / VALIDÉ / PUSHÉ**

---

## 1. Résumé exécutif

La mission B1 HMM avait pour objectif de remplacer ou compléter l’heuristique fragile du moteur de régime HTF par un moteur probabiliste de type Hidden Markov Model.

La brique livrée est :

```text
Core/pf_hmm_regime.py
Core/run_hmm_regime_once.py
```

Le moteur est opérationnel, autonome, compatible Python 3.14, et ne dépend plus de `hmmlearn`.

La version finale validée est :

```text
HMMRegimeV1.2StandaloneSchema
HMMRegimeRunnerV1.2StandaloneSchema
method = hmm_gaussian_standalone
```

Résultat validé sur la base locale :

```text
Regime       : TENDANCE
Confidence   : 0.912568
COMPRESSION  : 0.000002
TENDANCE     : 0.912568
RANGE        : 0.087430
TF utilisé   : 240
Samples      : 39
Dernière barre : 2026-05-08T16:00:00+00:00
```

Validation finale :

```text
py_compile OK
train OK
predict OK
JSON valide
modèle sauvegardé
stabilité 3 runs OK
commit OK
push OK
```

---

## 2. Contexte critique

B1 est une brique centrale de PowerFlow.

Le `regime_context` injecté dans chaque alerte comportementale dépend du moteur de régime.

Une même alerte peut changer de qualification selon le régime :

```text
FIRST_DETACHMENT + COMPRESSION  -> HOT
FIRST_DETACHMENT + RANGE        -> WATCH
FIRST_DETACHMENT + TENDANCE     -> INFO
```

Donc une erreur de régime peut contaminer toute la couche d’alerte.

L’objectif de la mission était donc d’ajouter une perception HTF plus robuste, probabiliste, et déterministe.

---

## 3. Objectif initial

Créer un moteur HMM capable de :

```text
1. Lire la DB powerflow.db en read-only.
2. Extraire les données HTF depuis force_snapshots.
3. Construire des features comportementales.
4. Apprendre trois états cachés : COMPRESSION / TENDANCE / RANGE.
5. Produire une probabilité par régime.
6. Sauvegarder un modèle réutilisable.
7. Prédire le régime courant.
8. Sortir un JSON stable pour intégration future.
```

Fichiers attendus :

```text
Core/pf_hmm_regime.py
Core/run_hmm_regime_once.py
output/hmm_regime_model.pkl
output/hmm_regime_result.json
```

---

## 4. Contraintes PowerFlow respectées

### 4.1 Architecture

La séparation des couches est respectée :

```text
pf_hmm_regime.py       -> couche moteur pf_*
run_hmm_regime_once.py -> couche runner run_*
output/*.json          -> interface de sortie
output/*.pkl           -> artefact modèle
```

Aucune dépendance cockpit/dashboard/telegram n’a été ajoutée.

### 4.2 DB read-only

Le moteur lit SQLite sans modifier la DB.

La table `force_snapshots` est utilisée comme mémoire brute.

Aucune écriture DB n’est effectuée.

### 4.3 Anti-nanny

Le moteur ne conseille rien.

Il produit uniquement un contexte statistique :

```json
{
  "regime": "TENDANCE",
  "confidence": 0.912568,
  "probability_map": {
    "COMPRESSION": 0.000002,
    "TENDANCE": 0.912568,
    "RANGE": 0.087430
  }
}
```

Le régime ne filtre pas les alertes.

Il qualifie le contexte.

Le trader décide.

---

## 5. Données utilisées

Données disponibles au moment de validation :

```text
TF240 : 39 rows
TF60  : 133 rows
```

Le moteur utilise :

```text
TF240 comme timeframe primaire
TF60 comme fallback
```

La prédiction validée s’est faite sur :

```text
TF240
samples_used = 39
last_timestamp = 2026-05-08T16:00:00+00:00
```

---

## 6. Implémentation finale

### 6.1 Version livrée

```text
MODEL_VERSION  = HMMRegimeV1.2StandaloneSchema
RUNNER_VERSION = HMMRegimeRunnerV1.2StandaloneSchema
METHOD         = hmm_gaussian_standalone
```

### 6.2 Dépendances finales

La version finale ne dépend plus de :

```text
hmmlearn
scikit-learn
scipy
```

Dépendance minimale :

```text
numpy
```

### 6.3 Pourquoi le standalone a été nécessaire

Le prompt initial proposait `hmmlearn`.

Sur l’environnement local, Python utilisé :

```text
Python 3.14 64-bit
```

`hmmlearn` n’a pas pu être installé car les wheels compatibles Python 3.14 n’étaient pas disponibles, et pip a tenté une compilation source locale.

Erreur observée :

```text
failed-wheel-build-for-install
Failed to build installable wheels for hmmlearn
```

Décision technique :

```text
Remplacer hmmlearn par un HMM Gaussian autonome en numpy.
```

Impact :

```text
+ compatibilité Python 3.14
+ pas de toolchain C requise
+ déterminisme complet
+ dépendance réduite
+ contrôle complet de la logique
```

---

## 7. Feature engineering

Le moteur extrait un flux comportemental depuis `force_snapshots`.

### 7.1 Force pair

Le moteur construit un spread de force entre GBP et USD :

```text
force_pair = force_gbp - force_usd
```

La version V1.2 est schema-aware : elle détecte automatiquement les colonnes disponibles.

### 7.2 Kalman smoothing

Le signal est lissé via Kalman :

```text
Q = 0.01
R = 0.10
```

Objectif : séparer le mouvement comportemental du bruit brut.

### 7.3 Features HMM

Chaque observation HMM contient :

```text
angle_kalman
speed_magnitude
zone_numeric
```

Conceptuellement :

```text
angle_kalman    -> pente du flux HTF
speed_magnitude -> variation de la pente
zone_numeric    -> état de tension / extrême
```

---

## 8. Régimes cachés

Le modèle travaille sur trois états PowerFlow :

```text
COMPRESSION
TENDANCE
RANGE
```

Ces états ne sont pas des signaux de trade.

Ce sont des contextes de flux HTF.

---

## 9. Entraînement

Commande validée :

```powershell
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
```

Sortie d’entraînement validée :

```json
{
  "valid": true,
  "timeframe": 240,
  "samples": 39,
  "last_timestamp": "2026-05-08T16:00:00+00:00",
  "label_counts": {
    "COMPRESSION": 10,
    "TENDANCE": 28,
    "RANGE": 1
  }
}
```

Le modèle est sauvegardé ici :

```text
output/hmm_regime_model.pkl
```

Validation existence modèle :

```powershell
Test-Path ..\output\hmm_regime_model.pkl
```

Résultat :

```text
True
```

---

## 10. Matrice de transition apprise

Matrice validée :

```json
[
  [0.538462, 0.384615, 0.076923],
  [0.166667, 0.766667, 0.066667],
  [0.25,     0.5,      0.25]
]
```

Lecture comportementale :

```text
COMPRESSION -> COMPRESSION : 53.84%
COMPRESSION -> TENDANCE    : 38.46%
TENDANCE    -> TENDANCE    : 76.66%
```

Le régime TENDANCE est actuellement l’état le plus persistant dans l’historique disponible.

---

## 11. Prédiction validée

Commande :

```powershell
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
```

Résultat :

```json
{
  "valid": true,
  "regime": "TENDANCE",
  "confidence": 0.912568,
  "probabilities": [0.000002, 0.912568, 0.087430],
  "probability_map": {
    "COMPRESSION": 0.000002,
    "TENDANCE": 0.912568,
    "RANGE": 0.087430
  },
  "raw_state": 1,
  "method": "hmm_gaussian_standalone"
}
```

---

## 12. Stabilité

Trois runs successifs ont produit le même régime et la même confiance.

Résultat :

```text
[True, True, True]
['TENDANCE', 'TENDANCE', 'TENDANCE']
[0.912568, 0.912568, 0.912568]
HMM STABLE
```

Conclusion :

```text
Le moteur est déterministe sur données identiques.
```

---

## 13. JSON output

Le runner écrit :

```text
output/hmm_regime_result.json
```

Validation JSON :

```powershell
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
```

Résultat : OK.

---

## 14. Risques techniques identifiés

### 14.1 LOW_STATE_DIVERSITY

Risque technique observé :

```text
LOW_STATE_DIVERSITY
```

Cause : historique TF240 encore court et déséquilibré.

Répartition :

```text
COMPRESSION : 10
TENDANCE    : 28
RANGE       : 1
```

Interprétation :

```text
Le modèle apprend surtout TENDANCE.
RANGE est sous-représenté.
La sortie reste valide, mais le moteur doit être recalibré avec plus d’historique live.
```

Ce n’est pas un risque financier.

C’est un risque de diversité statistique.

### 14.2 Python 3.14 / hmmlearn

Risque résolu :

```text
MISSING_HMM_DEPENDENCY
```

Résolution :

```text
Suppression complète de hmmlearn.
HMM autonome en numpy.
```

### 14.3 Schéma DB variable

Risque résolu :

```text
DB_FORCE_COLUMN_MAPPING
```

Résolution :

```text
V1.2 schema-aware : auto-détection des colonnes GBP/USD.
```

---

## 15. Historique de résolution

### 15.1 V1.0 — hmmlearn

Première version :

```text
HMMRegimeV1.0
HMMRegimeRunnerV1.0
```

Blocage :

```text
MISSING_HMM_DEPENDENCY
```

Cause :

```text
hmmlearn non installable facilement sur Python 3.14.
```

### 15.2 V1.1 — standalone

Deuxième version :

```text
HMMRegimeV1.1Standalone
```

Résolution :

```text
Suppression hmmlearn.
```

Nouveau blocage :

```text
force_snapshots must expose timestamp/timeframe and GBP/USD force columns
```

Cause :

```text
Noms de colonnes DB différents de force_gbp / force_usd.
```

### 15.3 V1.2 — standalone schema-aware

Version finale :

```text
HMMRegimeV1.2StandaloneSchema
```

Résolution :

```text
Auto-détection du schéma DB.
Train/predict validés.
```

---

## 16. Commandes validées

Depuis `Core` :

```powershell
python -m py_compile pf_hmm_regime.py run_hmm_regime_once.py
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
Test-Path ..\output\hmm_regime_model.pkl
```

Stabilité :

```powershell
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
Copy-Item ..\output\hmm_regime_result.json ..\output\hmm_regime_run1.json

python run_hmm_regime_once.py --db powerflow.db --predict --pretty
Copy-Item ..\output\hmm_regime_result.json ..\output\hmm_regime_run2.json

python run_hmm_regime_once.py --db powerflow.db --predict --pretty
Copy-Item ..\output\hmm_regime_result.json ..\output\hmm_regime_run3.json

python -c "import json; files=['../output/hmm_regime_run1.json','../output/hmm_regime_run2.json','../output/hmm_regime_run3.json']; data=[json.load(open(f, encoding='utf-8')) for f in files]; print([d.get('valid') for d in data]); print([d.get('prediction',{}).get('regime') for d in data]); print([d.get('prediction',{}).get('confidence') for d in data]); assert all(d.get('valid') for d in data), 'One run invalid'; assert len(set(d['prediction']['regime'] for d in data))==1, 'Regime differs'; print('HMM STABLE')"
```

Git :

```powershell
git add Core\pf_hmm_regime.py Core\run_hmm_regime_once.py
git commit -m "B1: HMM Gaussian regime upgrade"
git push
```

---

## 17. Git

Commit :

```text
e1e175f — B1: HMM Gaussian regime upgrade
```

Push :

```text
main -> main
```

Remote :

```text
https://github.com/gestionzen57-alt/V7.git
```

---

## 18. Intégration future

### 18.1 Intégration dans B1 existant

À terme, `pf_regime_engine.py` pourra appeler :

```python
from pf_hmm_regime import HMMRegimeEngine

engine = HMMRegimeEngine()
result = engine.predict_from_db("powerflow.db")
```

Puis injecter :

```json
{
  "regime": "TENDANCE",
  "confidence": 0.912568,
  "method": "hmm_gaussian_standalone",
  "probability_map": {
    "COMPRESSION": 0.000002,
    "TENDANCE": 0.912568,
    "RANGE": 0.087430
  }
}
```

### 18.2 Intégration orchestrateur

Le runner pourra devenir un step du cycle :

```text
run_hmm_regime_once.py --db Core/powerflow.db --predict
```

Retrain recommandé :

```text
quotidien ou après accumulation significative TF240
```

### 18.3 Intégration cockpit

Le cockpit pourra afficher :

```text
B1 HMM REGIME
TENDANCE 91.26%
COMPRESSION 0.00%
RANGE 8.74%
LOW_STATE_DIVERSITY si présent
```

---

## 19. Recommandations techniques

### 19.1 Court terme

```text
Ne pas remplacer brutalement l’ancien B1 dans la chaîne live.
Faire tourner HMM en parallèle pendant P0/P1.
Comparer HMM vs heuristique sur plusieurs sessions.
```

### 19.2 Moyen terme

```text
Accumuler davantage TF240.
Surveiller l’apparition de RANGE réel.
Recalibrer chaque jour ou chaque semaine.
```

### 19.3 Seuils

Seuil actuel de confiance :

```text
0.60
```

Si confidence < 0.60 :

```text
valid = false
technical_risks = LOW_CONFIDENCE
```

Pas de censure d’alerte.

Seulement une qualification de contexte.

---

## 20. Limites actuelles

```text
1. Historique TF240 encore court.
2. RANGE quasi absent dans les labels actuels.
3. Pas encore intégré dans pf_regime_engine.py.
4. Pas encore comparé automatiquement à l’heuristique B1 historique.
5. Pas encore affiché dans le dashboard.
```

Ces limites sont techniques et normales à ce stade.

---

## 21. Résultat final

La mission est validée.

B1 dispose maintenant d’un moteur HMM Gaussian autonome, probabiliste, déterministe, compatible Python 3.14, et branchable à PowerFlow.

Le moteur ne prédit pas un trade.

Il perçoit un régime HTF probable.

Il donne au mapper un contexte plus riche.

Le trader garde la décision.

---

## 22. Checkpoint PowerFlow

```text
2026-05-10 — B1 HMM Gaussian Regime Upgrade
Core/pf_hmm_regime.py créé
Core/run_hmm_regime_once.py créé
Méthode : hmm_gaussian_standalone
Version : HMMRegimeV1.2StandaloneSchema
DB : read-only
TF primaire : 240
Fallback : 60
Features : angle_kalman / speed_magnitude / zone_numeric
États : COMPRESSION / TENDANCE / RANGE
Modèle : output/hmm_regime_model.pkl
Output : output/hmm_regime_result.json
Résultat actuel : TENDANCE confidence=0.912568
Risque technique : LOW_STATE_DIVERSITY
Git : e1e175f — B1: HMM Gaussian regime upgrade
```
