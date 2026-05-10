# PATCH LEXIQUE — B1 HMM Gaussian Regime Upgrade
**PowerFlow V7.1 / V7.2**  
**Date : 2026-05-10**  
**Objet : Ajout des termes liés au moteur de régime HMM B1**  
**Commit associé : `e1e175f` — `B1: HMM Gaussian regime upgrade`**

---

## Section proposée à ajouter au `LEXIQUE_GRAMMAIRE_V7.1.md`

À insérer après la section sur le régime HTF, ou en nouvelle section dédiée :

```markdown
---

## 19. B1 HMM REGIME ENGINE — Régime HTF probabiliste

### B1_HMM_REGIME_ENGINE
Module PowerFlow (`pf_hmm_regime.py`) ajoutant une lecture probabiliste du régime HTF.
Il apprend les transitions entre `COMPRESSION`, `TENDANCE` et `RANGE` à partir de l’historique `force_snapshots`.
Il ne remplace pas la décision du trader et ne filtre aucune alerte.
Il qualifie le contexte dans lequel une alerte apparaît.

### HMM_GAUSSIAN_STANDALONE
Méthode HMM Gaussian autonome utilisée par PowerFlow pour détecter le régime HTF.
Version livrée sans dépendance `hmmlearn`, compatible Python 3.14.
Implémentée en `numpy` pour éviter les blocages de compilation de dépendances externes.
Méthode reportée dans le JSON sous :

```json
"method": "hmm_gaussian_standalone"
```

### HMMRegimeV1.2StandaloneSchema
Version validée du moteur B1 HMM.
Caractéristiques :
- HMM Gaussian autonome ;
- auto-détection du schéma DB ;
- TF240 primaire ;
- TF60 fallback ;
- modèle sérialisé dans `output/hmm_regime_model.pkl` ;
- sortie JSON dans `output/hmm_regime_result.json`.

### HMMRegimeRunnerV1.2StandaloneSchema
Version validée du runner one-shot :

```text
Core/run_hmm_regime_once.py
```

Commandes principales :

```powershell
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
```

### HMM_STATE
État caché appris par le HMM.
Dans PowerFlow, les états cachés sont mappés vers :

```text
COMPRESSION
TENDANCE
RANGE
```

Un état HMM n’est pas une décision de trade.
C’est une classe de comportement HTF.

### RAW_STATE
Index numérique de l’état caché retourné par le moteur.
Exemple :

```json
"raw_state": 1
```

Le `raw_state` est technique.
Le label PowerFlow lisible reste `regime`.

### HMM_PROBABILITIES
Distribution probabiliste des régimes possibles pour l’observation courante.
Exemple :

```json
"probabilities": [0.000002, 0.912568, 0.087430]
```

Ordre standard :

```text
[COMPRESSION, TENDANCE, RANGE]
```

### HMM_PROBABILITY_MAP
Version lisible de `HMM_PROBABILITIES`.
Exemple :

```json
"probability_map": {
  "COMPRESSION": 0.000002,
  "TENDANCE": 0.912568,
  "RANGE": 0.087430
}
```

Permet au cockpit et au trader de voir la compétition entre régimes.

### HMM_CONFIDENCE
Probabilité maximale dans la distribution HMM.
Exemple :

```json
"confidence": 0.912568
```

Une confiance haute indique que le moteur distingue clairement un régime dominant.
Une confiance basse déclenche un risque technique de type `LOW_CONFIDENCE`.

### TRANSITION_MATRIX
Matrice apprise par le HMM indiquant les transitions probables entre régimes.
Exemple :

```json
[
  [0.538462, 0.384615, 0.076923],
  [0.166667, 0.766667, 0.066667],
  [0.25, 0.5, 0.25]
]
```

Lecture : probabilité de passer d’un régime courant vers un régime suivant.
Elle aide à mesurer la persistance ou la rotation d’un régime.

### HMM_MEANS
Centres statistiques appris par état caché sur les features :

```text
angle_kalman
speed_magnitude
zone_numeric
```

Les `means` ne sont pas des seuils fixes.
Ils décrivent le centre comportemental appris de chaque régime.

### HMM_COVARIANCE_DIAGONALS
Dispersion statistique des features par état HMM.
Permet d’évaluer si un régime est compact ou diffus dans l’espace des observations.

### HMM_MODEL_PATH
Chemin du modèle sérialisé :

```text
output/hmm_regime_model.pkl
```

Si ce fichier est absent, le runner retourne :

```text
HMM_MODEL_MISSING
```

### HMM_RESULT_JSON
Fichier de sortie du runner :

```text
output/hmm_regime_result.json
```

Contient :
- régime détecté ;
- confiance ;
- probabilités ;
- source DB ;
- timeframe utilisé ;
- risques techniques.

### TF240_HMM_PRIMARY
Timeframe primaire du moteur HMM.
TF240 correspond à H4, zone de gravité HTF dans PowerFlow.
Utilisé prioritairement pour apprendre le régime.

### TF60_HMM_FALLBACK
Timeframe de secours du moteur HMM.
TF60 correspond à H1, traducteur entre structure HTF et fenêtre intraday.
Utilisé si TF240 n’offre pas assez d’échantillons.

### HMM_FEATURE_VECTOR
Vecteur d’observation transmis au HMM.
Structure :

```text
[angle_kalman, speed_magnitude, zone_numeric]
```

Ce vecteur représente le comportement HTF d’une barre.

### ANGLE_KALMAN_HMM
Angle lissé utilisé dans les observations HMM.
Issu d’un filtrage Kalman avec paramètres PowerFlow :

```text
Q = 0.01
R = 0.10
```

Mesure la pente propre du flux HTF.

### SPEED_MAGNITUDE_HMM
Amplitude de variation de l’angle entre deux observations.
Permet au HMM de distinguer :
- régime qui accélère ;
- régime stable ;
- régime qui perd sa pente ;
- rotation de flux.

### ZONE_NUMERIC_HMM
Encodage numérique de la tension de zone.
Utilisé comme troisième dimension du vecteur HMM.
Il traduit le degré de stress / extrême dans l’espace HTF.

### SCHEMA_AWARE_DB_MAPPING
Capacité du moteur V1.2 à détecter automatiquement les colonnes pertinentes dans `force_snapshots`.
Résout le problème des variantes de noms de colonnes GBP/USD.
Risque technique associé si échec : `DB_FORCE_COLUMN_MAPPING`.

### HMM_MODEL_MISSING
Risque technique retourné quand `output/hmm_regime_model.pkl` n’existe pas encore.
Solution : lancer un entraînement.

```powershell
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
```

### MISSING_HMM_DEPENDENCY
Ancien risque technique de la V1.0 lié à l’absence de `hmmlearn`.
Résolu par la version `HMMRegimeV1.2StandaloneSchema`.
Ce risque ne doit plus apparaître dans la version standalone.

### HMM_RUNTIME_ERROR
Risque technique générique retourné si le runner rencontre une exception non prévue.
À analyser via le champ `error` du JSON.

### LOW_STATE_DIVERSITY
Risque technique indiquant que l’historique d’entraînement ne contient pas assez de diversité entre régimes.
Exemple observé :

```json
"label_counts": {
  "COMPRESSION": 10,
  "TENDANCE": 28,
  "RANGE": 1
}
```

Lecture : le moteur fonctionne, mais un état est sous-représenté.
Conséquence technique : risque de biais vers l’état dominant.
Ce n’est pas un risque de marché.

### LOW_CONFIDENCE
Risque technique retourné si la probabilité maximale du HMM est sous le seuil minimal.
Le régime peut être affiché, mais doit être qualifié comme peu net.
Aucune alerte ne doit être censurée pour cette raison.

### HMM_STABLE
État de validation obtenu quand plusieurs prédictions successives donnent le même régime et la même confiance sur données identiques.
Exemple validé :

```text
[True, True, True]
['TENDANCE', 'TENDANCE', 'TENDANCE']
[0.912568, 0.912568, 0.912568]
HMM STABLE
```

### HMM_REGIME_CONTEXT
Bloc destiné à enrichir les alertes comportementales.
Format cible :

```json
"regime_context": {
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

Le contexte HMM ne décide rien.
Il qualifie l’environnement HTF.

### HMM_PARALLEL_B1_MODE
Mode recommandé pendant la phase de validation : faire tourner HMM en parallèle de l’ancienne heuristique B1.
Objectif : comparer les régimes détectés sans casser la chaîne d’alerte live.

### HMM_DAILY_RETRAIN
Routine possible de recalibration quotidienne.
Commande :

```powershell
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
```

Recommandé après accumulation de nouvelles barres TF240.

### HMM_NOT_A_SIGNAL
Règle doctrinale : le HMM ne produit pas un signal de trading.
Il produit un contexte de régime.
Le mapper qualifie.
Le trader filtre.
Le trader décide.

---
```

---

## Patch court pour section “RÉGIME HTF” existante

Ajouter sous `REGIME_CONFIDENCE` :

```markdown
### REGIME_CONFIDENCE_HMM
Confiance probabiliste issue du moteur `pf_hmm_regime.py`.
Correspond à la probabilité maximale parmi `COMPRESSION`, `TENDANCE`, `RANGE`.
Exemple : `0.912568` pour `TENDANCE`.
Ne représente pas une probabilité de succès de trade.
Représente seulement la netteté statistique du régime HTF perçu.

### REGIME_PROBABILITY_MAP
Distribution complète des régimes HTF possibles.
Exemple :

```json
{
  "COMPRESSION": 0.000002,
  "TENDANCE": 0.912568,
  "RANGE": 0.087430
}
```

Permet de voir si le régime dominant est net ou si plusieurs états se disputent le flux.
```

---

## Patch court pour section “RISQUES TECHNIQUES”

Ajouter dans les exemples de risques techniques :

```markdown
### LOW_STATE_DIVERSITY
Historique d’entraînement déséquilibré entre régimes HMM.
Le moteur reste valide, mais un régime peut être sous-représenté.

### HMM_MODEL_MISSING
Modèle HMM non encore entraîné ou fichier `output/hmm_regime_model.pkl` absent.

### LOW_CONFIDENCE
Probabilité maximale HMM sous le seuil minimal de validation.
Le régime est flou statistiquement.

### DB_FORCE_COLUMN_MAPPING
Le moteur n’a pas pu identifier les colonnes de force nécessaires dans `force_snapshots`.

### HMM_RUNTIME_ERROR
Erreur technique d’exécution dans le runner HMM.
Lire le champ `error` du JSON.
```

---

## Patch court pour section “FICHIERS / NOMENCLATURE”

Ajouter :

```markdown
### pf_hmm_regime.py
Brique moteur B1 HMM.
Détecte le régime HTF via HMM Gaussian standalone.
Lit `force_snapshots` en read-only.
Produit un contexte probabiliste `COMPRESSION / TENDANCE / RANGE`.

### run_hmm_regime_once.py
Runner one-shot du moteur B1 HMM.
Modes :
- `--train`
- `--predict`
- `--train --predict`

Produit :

```text
output/hmm_regime_result.json
output/hmm_regime_model.pkl
```
```

---

## Checkpoint lexique

```text
2026-05-10 — Ajout B1 HMM Regime Engine
Nouveaux termes :
B1_HMM_REGIME_ENGINE
HMM_GAUSSIAN_STANDALONE
HMMRegimeV1.2StandaloneSchema
HMMRegimeRunnerV1.2StandaloneSchema
HMM_STATE
RAW_STATE
HMM_PROBABILITIES
HMM_PROBABILITY_MAP
HMM_CONFIDENCE
TRANSITION_MATRIX
HMM_MEANS
HMM_COVARIANCE_DIAGONALS
HMM_MODEL_PATH
HMM_RESULT_JSON
TF240_HMM_PRIMARY
TF60_HMM_FALLBACK
HMM_FEATURE_VECTOR
ANGLE_KALMAN_HMM
SPEED_MAGNITUDE_HMM
ZONE_NUMERIC_HMM
SCHEMA_AWARE_DB_MAPPING
HMM_MODEL_MISSING
MISSING_HMM_DEPENDENCY
HMM_RUNTIME_ERROR
LOW_STATE_DIVERSITY
LOW_CONFIDENCE
HMM_STABLE
HMM_REGIME_CONTEXT
HMM_PARALLEL_B1_MODE
HMM_DAILY_RETRAIN
HMM_NOT_A_SIGNAL
```
