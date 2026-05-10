# PATCH LEXIQUE — B7 Fractal Resonance Detection

Section proposée pour `LEXIQUE_GRAMMAIRE_V7.1.md`.

---

## 23. FRACTAL RESONANCE DETECTION — B7

### FRACTAL_RESONANCE
Mesure de synchronisation entre timeframes adjacents. Elle indique si plusieurs étages temporels vibrent ensemble sur le même événement, ou si un timeframe traîne les autres.

Fractal Resonance ne prédit pas. Elle qualifie la cohérence temporelle du flux.

### RESONANT
État où plusieurs timeframes adjacents présentent une corrélation forte et un lag faible.

Comportement :

```text
M1 + M5 + M15 vibrent ensemble
```

Interprétation PowerFlow :

```text
Tous les étages de la maison tremblent.
```

Usage :

```json
{
  "resonance_state": "RESONANT",
  "resonance_score": 0.84,
  "resonant_tfs": [1, 5, 15],
  "expected_amplification": true
}
```

### LAGGED
État où une corrélation existe entre timeframes, mais avec un délai visible. Le LTF a bougé, le MTF ou HTF n'a pas encore totalement réagi.

Comportement :

```text
M1/M5 déjà actifs
M15 ou M30 en retard
```

Interprétation PowerFlow :

```text
Tremblement en cascade, fenêtre temporelle ouverte.
```

Usage :

```json
{
  "resonance_state": "LAGGED",
  "lagged_tfs": [15, 30],
  "lag_detection": {
    "(5, 15)": 3,
    "(15, 30)": 5
  }
}
```

### DISSONANT
État où les timeframes montrent une corrélation faible. Un étage peut bouger sans que les autres vibrent franchement.

Comportement :

```text
M1 actif mais M5/M15 peu synchronisés
```

Interprétation PowerFlow :

```text
Étage isolé, les autres sont calmes.
```

### SILENT
État où aucune synchronisation exploitable n'est détectée, ou bien où les données sont insuffisantes/figées.

Comportement :

```text
Pas de vibration fractale lisible.
```

### RESONANCE_SCORE
Score 0.0-1.0 mesurant la corrélation positive moyenne entre paires adjacentes valides.

```text
>= 0.80  RESONANT
>= 0.60  LAGGED
>= 0.30  DISSONANT
<  0.30  SILENT
```

### AVG_SIGNED_CORRELATION
Moyenne signée des corrélations brutes. Permet de voir si une synchronisation est directionnellement cohérente ou inverse.

Contrairement à `resonance_score`, une corrélation inverse ne renforce pas la résonance.

### PAIR_CORRELATIONS
Dictionnaire des corrélations entre paires adjacentes.

Exemple :

```json
{
  "(1, 5)": 0.87,
  "(5, 15)": 0.81,
  "(15, 30)": 0.55,
  "(30, 60)": 0.42
}
```

### LAG_DETECTION
Dictionnaire des retards estimés en barres entre paires adjacentes.

Convention :

```text
lag > 0 : le second timeframe traîne le premier
lag = 0 : synchronisation directe
lag < 0 : le second timeframe semble en avance
```

### RESONANT_TFS
Liste des timeframes qui vibrent ensemble.

Exemple :

```json
"resonant_tfs": [1, 5, 15]
```

### LAGGED_TFS
Liste des timeframes qui semblent en retard par rapport aux timeframes plus rapides.

Exemple :

```json
"lagged_tfs": [30, 60]
```

### DISSONANT_TFS
Liste des timeframes qui ne participent pas clairement à la vibration commune.

### EXPECTED_AMPLIFICATION
Booléen indiquant que la synchronisation fractale est assez forte pour qualifier une amplification attendue du flux.

Ce n'est pas une prédiction de trade. C'est une qualification de cohérence temporelle.

### CROSS_CORRELATION_MULTI_TF
Méthode B7 basée sur corrélation et lag detection entre timeframes adjacents.

Fichier :

```text
Core/pf_fractal_resonance.py
```

Runner :

```text
Core/run_fractal_resonance_once.py
```

Output :

```text
output/fractal_resonance.json
```

### RISQUES TECHNIQUES B7

```text
INSUFFICIENT_DATA       Moins de 50 barres sur une paire TF
FLAT_SERIES             Série figée, weekend ou capture morte
CORRELATION_UNSTABLE    Corrélation non stable ou non finie
LAGGED_MULTIPLE_TF      Plusieurs timeframes traînent simultanément
SILENT_HTF              H1/H4 présents mais non synchronisés
```

Ces risques qualifient la lecture. Ils ne filtrent pas l'alerte.

---

## Formule PowerFlow

```text
RESONANT  -> Tous les étages de la maison tremblent
LAGGED    -> Tremblement en cascade, fenêtre ouverte
DISSONANT -> Étage isolé, les autres sont calmes
SILENT    -> Rien ne bouge
```
