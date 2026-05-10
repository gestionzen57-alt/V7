# PATCH LEXIQUE — B7 Fractal Resonance Detection

**Document cible :** `LEXIQUE_GRAMMAIRE_V7.1.md`  
**Section proposée :** `## 23. FRACTAL RESONANCE DETECTION — B7`  
**Statut :** prêt à intégrer  
**Contexte :** B7 commitée localement sous `8c467c4 — B7: Fractal Resonance Detection`  

---

## 23. FRACTAL RESONANCE DETECTION — B7

### FRACTAL_RESONANCE

Mesure de synchronisation entre timeframes adjacents.

Elle indique si plusieurs étages temporels vibrent ensemble sur le même événement, ou si un timeframe est en avance, en retard, isolé ou en contre-phase.

Fractal Resonance ne prédit pas. Elle qualifie la cohérence temporelle du flux.

Fichier moteur :

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

---

### RESONANT

État où plusieurs timeframes adjacents présentent une corrélation positive forte et un lag faible.

Comportement :

```text
M1 + M5 + M15 vibrent ensemble
```

Traduction PowerFlow :

```text
Tous les étages de la maison tremblent.
```

Exemple JSON :

```json
{
  "resonance_state": "RESONANT",
  "resonance_score": 0.84,
  "resonant_tfs": [1, 5, 15],
  "expected_amplification": true
}
```

Usage comportemental : un signal LTF accompagné d'une résonance MTF reçoit une qualité technique supérieure. Ce n'est pas une instruction de trade.

---

### LAGGED

État où une corrélation positive existe entre timeframes, mais avec un délai visible.

Le LTF a bougé, le MTF ou HTF n'a pas encore totalement réagi.

Comportement :

```text
M1/M5 déjà actifs
M15 ou M30 en retard
```

Traduction PowerFlow :

```text
Tremblement en cascade, fenêtre temporelle ouverte.
```

Exemple JSON :

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

Usage comportemental : LAGGED qualifie une fenêtre de synchronisation potentielle. Il ne force pas la confirmation et ne censure pas l'alerte précoce.

---

### DISSONANT

État où les timeframes montrent une corrélation faible ou partielle.

Un étage peut bouger sans que les autres vibrent franchement.

Comportement :

```text
M1 actif mais M5/M15 peu synchronisés
```

Traduction PowerFlow :

```text
Étage isolé, les autres sont calmes.
```

Usage comportemental : DISSONANT signale une lecture fractale moins propre. Il qualifie le risque technique d'isolement LTF.

---

### SILENT

État où aucune synchronisation positive exploitable n'est détectée.

SILENT ne signifie pas forcément que le marché est mort. Il signifie que la vibration fractale commune n'est pas lisible sur la fenêtre actuelle.

Comportement :

```text
Pas de vibration fractale positive exploitable.
```

Cas réel observé le 2026-05-10 :

```json
{
  "resonance_state": "SILENT",
  "resonance_score": 0.0,
  "avg_signed_correlation": -0.517481,
  "valid": true
}
```

Lecture PowerFlow : les TF ne vibrent pas ensemble positivement. Plusieurs paires sont en contre-phase.

---

### RESONANCE_SCORE

Score 0.0-1.0 mesurant la corrélation positive moyenne entre paires adjacentes valides.

Seuils V0.1 :

```text
>= 0.80  RESONANT
>= 0.60  LAGGED
>= 0.30  DISSONANT
<  0.30  SILENT
```

Important : une corrélation inverse forte ne doit pas augmenter le `resonance_score`. Elle peut être informative, mais elle ne représente pas une vibration commune directionnelle.

---

### AVG_SIGNED_CORRELATION

Moyenne signée des corrélations brutes entre paires adjacentes.

Elle garde la polarité de la relation fractale.

Lecture :

```text
+0.80  synchronisation positive forte
 0.00  champ neutre ou dispersé
-0.80  opposition fractale forte / contre-phase
```

Contrairement à `resonance_score`, `avg_signed_correlation` peut être négative.

---

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

Cas réel observé le 2026-05-10 :

```json
{
  "(1, 5)": -0.278398,
  "(5, 15)": -0.869968,
  "(15, 30)": -0.744471,
  "(30, 60)": -0.177088
}
```

Lecture : le champ fractal n'était pas résonant. M5/M15 et M15/M30 étaient en opposition forte.

---

### PAIR_STATES

Dictionnaire des états par paire adjacente.

Exemple :

```json
{
  "(1, 5)": "RESONANT",
  "(5, 15)": "LAGGED",
  "(15, 30)": "DISSONANT",
  "(30, 60)": "SILENT"
}
```

Permet de lire finement où la chaîne fractale se synchronise ou se casse.

---

### LAG_DETECTION

Dictionnaire des retards estimés en barres entre paires adjacentes.

Convention :

```text
lag > 0 : le second timeframe traîne le premier
lag = 0 : synchronisation directe
lag < 0 : le second timeframe semble en avance
```

Exemple :

```json
{
  "(1, 5)": 0,
  "(5, 15)": 1,
  "(15, 30)": 3,
  "(30, 60)": 5
}
```

Cas réel observé le 2026-05-10 :

```json
{
  "(1, 5)": 7,
  "(5, 15)": -3,
  "(15, 30)": -2,
  "(30, 60)": -3
}
```

Lecture : le champ n'était pas simplement silencieux ; il montrait aussi des décalages multiples.

---

### RESONANT_TFS

Liste des timeframes participant à une vibration commune.

Exemple :

```json
"resonant_tfs": [1, 5, 15]
```

---

### LAGGED_TFS

Liste des timeframes qui semblent en retard par rapport aux étages plus rapides.

Exemple :

```json
"lagged_tfs": [30, 60]
```

---

### DISSONANT_TFS

Liste des timeframes qui ne participent pas clairement à la vibration commune.

Cas réel observé le 2026-05-10 :

```json
"dissonant_tfs": [1, 5, 15, 30, 60]
```

---

### EXPECTED_AMPLIFICATION

Booléen indiquant que la synchronisation fractale positive est assez forte pour qualifier une amplification attendue du flux.

Ce n'est pas une prédiction de trade. C'est une qualification de cohérence temporelle.

Exemples :

```json
"expected_amplification": true
```

```json
"expected_amplification": false
```

---

### CROSS_CORRELATION_MULTI_TF

Méthode B7 V0.1 basée sur corrélation et lag detection entre paires adjacentes.

Principe minimal :

```text
1. prendre les séries rolling par TF
2. normaliser en z-score
3. calculer corrélation + lag entre paires adjacentes
4. classifier RESONANT / LAGGED / DISSONANT / SILENT
```

Méthode déclarée dans le JSON :

```json
"method": "cross_correlation_multi_tf"
```

---

### BAR_TAIL_ALIGNMENT

Mode d'alignement V0.1 : comparaison des N dernières barres de chaque timeframe.

Avantage : très léger, rapide, facile à intégrer.

Limite : 50 barres ne couvrent pas la même durée réelle selon le TF.

Exemple :

```text
TF1  : 50 barres = 50 minutes
TF5  : 50 barres = 250 minutes
TF15 : 50 barres = 750 minutes
TF30 : 50 barres = 1500 minutes
TF60 : 50 barres = 3000 minutes
```

---

### TEMPORAL_WINDOW_MISMATCH

Risque technique indiquant que les séries comparées couvrent des durées réelles différentes.

Ce risque apparaît quand la résonance est calculée en mode `BAR_TAIL_ALIGNMENT` plutôt qu'en mode timestamp-aligned.

Il ne rend pas la brique invalide. Il signale une limite de justesse temporelle.

---

### TIMESTAMP_ALIGNED_RESONANCE

Évolution V0.2 recommandée de B7.

Principe : comparer les timeframes sur une même fenêtre horloge, puis resampler ou interpoler les séries sur une grille commune avant corrélation.

Exemple :

```text
Fenêtre horloge : 180 minutes
TF1  : jusqu'à 180 points
TF5  : jusqu'à 36 points
TF15 : jusqu'à 12 points
TF30 : jusqu'à 6 points
TF60 : jusqu'à 3 points
```

But : mesurer une vraie résonance temporelle, pas seulement une ressemblance des queues de séries.

---

### INVERSE_FRACTAL_OPPOSITION

Situation où plusieurs paires adjacentes présentent une corrélation fortement négative.

Exemple réel :

```text
M5 ↔ M15  = -0.869968
M15 ↔ M30 = -0.744471
```

Lecture PowerFlow : les étages ne vibrent pas ensemble, ils répondent en contre-phase.

En V0.1, cette situation peut sortir comme `SILENT` avec `avg_signed_correlation` négatif. Une V0.2 pourrait exposer un état additionnel sans casser le contrat principal.

---

### RISQUES TECHNIQUES B7

```text
INSUFFICIENT_DATA          Moins de 50 barres sur une paire TF
FLAT_SERIES                Série figée, weekend ou capture morte
CORRELATION_UNSTABLE       Corrélation non stable ou non finie
LAGGED_MULTIPLE_TF         Plusieurs timeframes montrent un retard / décalage simultané
SILENT_HTF                 H1/H4 présents mais non synchronisés positivement
TEMPORAL_WINDOW_MISMATCH   Fenêtres comparées non équivalentes en temps horloge
```

Ces risques qualifient la lecture. Ils ne filtrent pas l'alerte et ne produisent aucune décision de trade.

---

## Formule PowerFlow B7

```text
RESONANT  -> Tous les étages de la maison tremblent
LAGGED    -> Tremblement en cascade, fenêtre ouverte
DISSONANT -> Étage isolé, les autres sont calmes
SILENT    -> Pas de vibration fractale positive exploitable
```

Version enrichie post-run :

```text
avg_signed_correlation < 0
  -> les étages peuvent être en contre-phase, pas seulement silencieux
```

---

## Note d'intégration

B7 V0.1 est commitée et fonctionnelle.

Amélioration recommandée pour B7 V0.2 :

```text
timestamp-aligned resonance
```

Cette amélioration ne change pas la doctrine PowerFlow. Elle améliore la justesse de la perception.
