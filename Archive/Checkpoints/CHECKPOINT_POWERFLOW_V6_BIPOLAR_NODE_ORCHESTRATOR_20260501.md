# CHECKPOINT POWERFLOW V6 — Bipolar Node + Orchestrator

**Date :** 2026-05-01  
**Statut :** checkpoint de session  
**Objet :** stabilisation de la lecture directionnelle LONG / SHORT, scanner multi-timeframes et orchestration fractale.

---

## 1. Résumé court

La session a permis de transformer une idée brute — détecter la scène bipolaire type 17h26 — en une première chaîne logicielle claire :

```text
powerflow.db
→ pf_bipolar_node_alert.py
→ pf_engine_orchestrator.py
→ SIGNAL_VALIDATED_LONG / SIGNAL_VALIDATED_SHORT
```

Le système ne lit plus un cross isolé. Il lit une construction : tension sur timeframes lourds, fermeture / déclenchement sur timeframes tactiques, puis validation seulement si le sens est cohérent.

La correction majeure de la session est la suivante : la première version lisait l'acteur comme s'il devait toujours rebondir. Cela pouvait inverser le sens réel. La version corrigée lit maintenant la paire dans les deux directions :

```text
spread = force_BASE - force_QUOTE
```

Pour `GBPUSD` :

```text
spread monte  = GBP domine USD = LONG
spread baisse = USD domine GBP = SHORT
```

---

## 2. Doctrine appliquée

La doctrine PowerFlow V6 appliquée pendant cette session :

```text
Voir le flux.
Calculer la tension.
Alerter vite.
Ne pas confondre géométrie brute et comportement réel.
```

Le cross géométrique n'est plus la porte d'entrée unique. La séquence correcte est :

```text
1. tension bipolaire
2. compression / absorption / écart qui se ferme
3. déclenchement tactique
4. validation fractale
```

Un cross sans tension préalable reste du bruit. Une tension forte sans cross peut devenir `PRE_ALERT`. Une tension lourde + un déclenchement tactique aligné devient `SIGNAL_VALIDATED`.

---

## 3. Problème initial

La demande initiale était :

```text
Écris-moi le script qui me sort une alerte Telegram propre quand cette scène bipolaire de 17h26 se reproduit.
```

La première version a volontairement été construite sans brancher Telegram immédiatement, afin de vérifier la logique mathématique sur la DB avant tout envoi externe.

Le premier problème détecté : le script sortait `NO_ALERT` avec `z_min=0.00`, car il résumait mal les timeframes et risquait d'écraser le signal tactique par des timeframes lourds.

Correction : création d'un debug multi-TF imprimant une ligne par timeframe.

---

## 4. Script 1 — `pf_bipolar_node_alert.py`

### Rôle

`pf_bipolar_node_alert.py` est le radar local multi-timeframe.

Il lit `powerflow.db`, interroge la table `force_snapshots`, puis analyse chaque timeframe séparément.

Il ne décide pas encore de l'alerte globale. Il dit seulement ce que chaque TF raconte.

### Sorties locales finales

```text
NO_ALERT
PRE_ALERT_LONG
PRE_ALERT_SHORT
ALERT_LONG
ALERT_SHORT
```

### Lecture directionnelle

Pour une paire `BASEQUOTE`, le script calcule :

```text
spread_pair = force_BASE - force_QUOTE
```

Interprétation :

```text
spread_pair monte  → BASE domine QUOTE → LONG
spread_pair baisse → QUOTE domine BASE → SHORT
```

Pour `GBPUSD` :

```text
GBP fort / USD faible = ALERT_LONG
USD fort / GBP faible = ALERT_SHORT
```

### Pourquoi cette correction était vitale

L'ancienne logique pouvait lire :

```text
GBP très bas = GBP va rebondir
```

Alors que le graphique réel pouvait dire :

```text
USD écrase GBP
GBP/USD chute
```

Le moteur voyait bien une tension, mais il pouvait poser la flèche dans le mauvais sens. La correction a supprimé ce biais.

---

## 5. Paramètres locaux utilisés

Les paramètres principaux placés en haut du fichier :

```text
ROWS_TO_LOAD = 220
Z_LOOKBACK = 60
MIN_ROWS_FOR_Z = 25
TENSION_WINDOW = 45
```

### Seuils de tension

```text
Z_DOMINANT = 1.50
Z_EXTREME = 2.10
```

Ces seuils disent : une devise commence à parler fortement autour de 1.50 en Z-score, et devient extrême autour de 2.10.

### Seuils de poussée du spread

```text
MIN_THRUST_DELTA_3 = 3.0
MIN_THRUST_DELTA_5 = 5.0
```

Ces seuils détectent une fermeture / poussée sur 3 ou 5 bougies.

### Quasi-cross

```text
QUASI_CROSS_DISTANCE = 7.0
```

Le système n'attend pas forcément un croisement parfait. Si les deux forces deviennent proches, le comportement peut déjà être exploitable en lecture.

### Zone centrale

```text
CENTER_LEVEL = 50.0
CENTER_BAND = 18.0
```

Cette zone sert à détecter un retour vers la zone de bataille / validation centrale, sans figer une ligne absolue.

### Scores

```text
PRE_ALERT_SCORE = 3.4
ALERT_SCORE = 4.6
```

Le score combine tension, poussée, compression, quasi-cross, retour centre et absorption.

---

## 6. Informations imprimées par TF

Chaque ligne de log contient :

```text
[M5] GBP/USD ALERT_SHORT dir=SHORT rows=...
GBP=... USD=...
Z(GBP)=... Z(USD)=...
spread=...
d3=...
d5=...
scoreL=...
scoreS=...
raison exacte
```

En mode verbose, le script imprime aussi les drapeaux internes :

```text
LONG_tension
SHORT_tension
LONG_thrust
SHORT_thrust
LONG_cross
SHORT_cross
quasi_cross
center
compression
liq_LONG
liq_SHORT
```

Ce mode debug est essentiel pour calibrer les seuils en voyant précisément pourquoi un TF donne `NO_ALERT`, `PRE_ALERT` ou `ALERT`.

---

## 7. Script 2 — `pf_engine_orchestrator.py`

### Rôle

`pf_engine_orchestrator.py` est le chef d'orchestre fractal.

Il consomme les résultats de `pf_bipolar_node_alert.py` et ne valide une alerte globale que si la structure est complète.

### Règle de validation globale

```text
SIGNAL_VALIDATED_LONG / SHORT
=
au moins un TF lourd en PRE_ALERT_LONG / SHORT
+
au moins un TF tactique en ALERT_LONG / SHORT
+
même direction obligatoire
```

### Timeframes lourds

```text
M15
M30
M60
```

Ces TF représentent la gravité / l'élastique chargé.

### Timeframes tactiques

```text
M1
M5
```

Ces TF représentent le déclenchement / fermeture du spread.

### Exemple SHORT

```text
M60 PRE_ALERT_SHORT
M30 PRE_ALERT_SHORT
M5  ALERT_SHORT

=> SIGNAL_VALIDATED_SHORT
```

### Exemple LONG

```text
M30 PRE_ALERT_LONG
M5  ALERT_LONG

=> SIGNAL_VALIDATED_LONG
```

### Protection contre l'inversion

L'orchestrator refuse les contradictions directionnelles :

```text
M60 PRE_ALERT_LONG + M5 ALERT_SHORT = refus
M30 PRE_ALERT_SHORT + M1 ALERT_LONG = refus
```

La gravité et le déclencheur doivent raconter le même sens.

---

## 8. Bug critique corrigé

### Bug

Le script initial lisait la tension comme si l'acteur devait toujours rebondir.

Dans le cas observé à 22h05 :

```text
GBP/USD en chute libre
USD écrase GBP
```

Mais le log pouvait produire une lecture comme si GBP allait rebondir.

### Cause

Le calcul était trop lié à :

```text
acteur faible = futur rebond acteur
```

Cela ne lit qu'un scénario. PowerFlow doit lire les deux : continuation / écrasement et rotation / rebond.

### Correction

Utilisation de :

```text
spread_pair = force_BASE - force_QUOTE
```

Puis lecture directionnelle :

```text
spread monte  => LONG
spread baisse => SHORT
```

Résultat attendu :

```text
Z(GBP) négatif / Z(USD) positif / spread qui plonge
=> ALERT_SHORT
```

---

## 9. Commandes Windows utiles

Depuis la racine du workspace :

```bat
python code\pf_bipolar_node_alert.py --db db\powerflow.db --symbol GBPUSD --verbose
```

Si les scripts sont dans `Core` et la DB dans `..\db` :

```bat
python pf_bipolar_node_alert.py --db ..\db\powerflow.db --symbol GBPUSD --verbose
```

Orchestrator depuis la racine :

```bat
python code\pf_engine_orchestrator.py --db db\powerflow.db --symbol GBPUSD --verbose
```

Orchestrator depuis `Core` :

```bat
python pf_engine_orchestrator.py --db ..\db\powerflow.db --symbol GBPUSD --verbose
```

Mode live :

```bat
python pf_engine_orchestrator.py --db ..\db\powerflow.db --symbol GBPUSD --loop --sleep 6 --verbose
```

Forcer les TF :

```bat
python pf_engine_orchestrator.py --db ..\db\powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --verbose
```

---

## 10. Sortie attendue après correction

Dans un scénario de chute GBP/USD :

```text
[M60] PRE_ALERT_SHORT
[M30] PRE_ALERT_SHORT
[M5 ] ALERT_SHORT

GLOBAL VERDICT : SIGNAL_VALIDATED_SHORT
STATUS         : SIGNAL_VALIDATED
DIRECTION      : SHORT
```

Dans un scénario de hausse GBP/USD :

```text
[M60] PRE_ALERT_LONG
[M5 ] ALERT_LONG

GLOBAL VERDICT : SIGNAL_VALIDATED_LONG
STATUS         : SIGNAL_VALIDATED
DIRECTION      : LONG
```

---

## 11. Ce que le système sait faire maintenant

Le système sait maintenant :

```text
lire chaque TF séparément
ne plus écraser M5 par H4/M60
lire LONG et SHORT
imprimer la raison exacte d'un rejet
séparer radar local et orchestration globale
valider une confluence fractale
refuser une contradiction de sens
```

Le comportement obtenu correspond à la grammaire PowerFlow :

```text
TF lourd = gravité / élastique chargé
TF tactique = déclenchement / fermeture du spread
même direction = phrase validée
```

---

## 12. Ce qui n'est pas encore branché

À ce checkpoint, il n'y a volontairement :

```text
aucun Telegram
aucune écriture DB
aucune modification ORION
aucun ordre BUY/SELL
```

Le système reste en mode lecture / debug / validation.

---

## 13. Formule finale de checkpoint

```text
La DB voit les forces.
Le scanner lit le sens par TF.
L'orchestrator valide la fractalité.
Le signal global n'existe que si gravité et tactique racontent le même film.
```

Statut de session : **bon noyau validé, direction corrigée, prêt pour calibration live.**
