# PATCH LEXIQUE — PowerFlow V6 / Gravity Respring / Fractalité / DB V2

**Date :** 2026-05-04  
**Statut :** patch à intégrer dans `LEXIQUE_GRAMMAIRE_POWERFLOW_V6_CONSOLIDE_2026-05-04.md`  
**Source :** session Agentic Core V0.1 + documents Lab/DB V2 ajoutés en cours de route

---

## 1. Concepts issus des notes Lab

### MICRO_WINDOW_ACTIVE

Fenêtre courte où le M1 cesse d’être bruité et devient informatif.

Signes possibles :

```text
hausse tick_volume
pip_range qui s’étend
force angle qui s’accentue
opposition de blocs
prix qui lag puis rattrape
```

Phrase :

```text
M1 bavarde hors fenêtre.
M1 révèle la naissance dans la bonne fenêtre.
```

---

### M1_NODE_BIRTH

Naissance du node sur microfilm.

Condition conceptuelle :

```text
accélération force
+ opposition blocs
+ activité volume
+ début réponse prix
```

Rôle :

```text
alerter vite sur la naissance
sans attendre que M15/H1 rendent la scène évidente
```

---

### M5_TACTICAL_CONFIRMATION

Le M5 confirme que le M1 n’était pas seulement du bruit.

Signes possibles :

```text
continuation angle
cohérence force/prix
pip_body dans le sens du champ
volume qui soutient
spread acceptable
```

---

### M15_SCENE_CONFIRMATION

Le M15 confirme la scène, mais arrive souvent après la naissance.

Rôle :

```text
valider le théâtre
donner la phrase de contexte
éviter que M1 commande seul
```

---

### PRICE_LAG_THEN_CATCHUP

Les forces bougent avant le prix.

Structure :

```text
forces basculent
prix reste retenu
prix rattrape ensuite
```

Importance :

```text
signature forte de node naissant
```

---

### VOLUME_PRESSURE_SPIKE

Spike de tick volume indiquant une activité réelle dans la fenêtre.

À utiliser avec :

```text
pip_range
pip_body
pip_change
force acceleration
spread friction
```

---

### SPREAD_FRICTION_FIELD

État de terrain lié au spread.

Ne sert pas à retenir une alerte, mais à qualifier la scène.

États possibles :

```text
champ propre
champ frictionné
champ instable
```

---

### FORCE_KINEMATICS

Famille de calculs pour mesurer la naissance du node.

```text
velocity = variation force / minute
angle = atan(velocity)
acceleration = variation velocity
energy = somme des amplitudes force
```

---

### VELOCITY_FORCE

Vitesse de variation d’une devise ou d’un bloc.

---

### ANGLE_FORCE

Angle mathématique approximatif d’une force.

---

### ACCELERATION_FORCE

Variation de vitesse de force entre deux segments.

---

### ENERGY_ROTATION

Énergie d’une rotation opposée de blocs.

Formule conceptuelle :

```text
ENERGY_ROTATION = somme(abs(force_delta)) sur les devises impliquées
```

---

## 2. Concepts DB V2 Extended

### FORCE_SNAPSHOTS_V2

Nouvelle table sonde complète.

Rôle :

```text
base future des agents séquence
capture enriched EA
support volume / pips / spread / NZD / OHLC
```

Colonnes principales :

```text
created_at
symbol
timeframe
bar_time
bar_close_time
server_time
capture_time
is_closed_bar
bid
ask
mid
spread
spread_points
spread_price
spread_pips
open
high
low
close
tick_volume
pip_range
pip_body
pip_change
force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
force_nzd
```

---

### LEGACY_FORCE_ONLY

Mode historique basé sur `force_snapshots`.

Caractéristiques :

```text
forces disponibles
bid parfois disponible
pas de bougie complète
pas de volume
pas de spread détaillé
pas de NZD
```

Utilité :

```text
backtest force-only
détection nodes / breaths / absorptions
scan historique
```

Limite :

```text
PRICE_UNKNOWN fréquent
pas de VOLUME_PRESSURE_SPIKE
pas de SPREAD_FRICTION_FIELD
```

---

### EXTENDED_MODE

Mode basé sur `force_snapshots_v2`.

Caractéristiques :

```text
forces + NZD
OHLC
tick_volume
pip_range
pip_body
pip_change
spread_pips
bid/ask/mid
bar_time / capture_time
is_closed_bar
```

Utilité :

```text
FlowEventExtractor V0.2
Sequence Reader V2
détection micro-window
comparaison M1/M5/M15
```

---

### BID_CLOSE_SEPARATION_RULE

Règle technique :

```python
bid = raw.get("bid")
close = raw.get("close")
ask = raw.get("ask")
mid = raw.get("mid")
```

À éviter :

```python
bid = raw.get("close", raw.get("bid"))
```

Car :

```text
bid = prix live
close = clôture bougie
les mélanger détruit la lecture prix/bougie
```

---

## 3. Concepts expériences DB

### LOOKBACK_EXPERIMENT_FIELD

Champ expérimental où plusieurs DB sont comparées pour déterminer quelle profondeur de lookback voit le mieux les nodes.

Critères :

```text
latence naissance
force angle
volume spike
pip expansion
cohérence M1/M5/M15
faux micro-events
```

---

### SCALP_FAST_FIELD

Configuration :

```text
DB      : powerflow_fast_300.db
Port    : 55555
Lookback: M1 300 / M5 300 / M15 300
```

But :

```text
capter très vite les pré-signaux
```

---

### SCALP_FRACTAL_FIELD

Configuration :

```text
DB      : powerflow_fractal_300_600_900.db
Port    : 55556
Lookback: M1 300 / M5 600 / M15 900
```

But :

```text
lecture imbriquée temps court → tactique → scène
```

Hypothèse prometteuse :

```text
M1  = naissance
M5  = traduction tactique
M15 = validation de scène
```

---

### SCALP_DEEP_FIELD

Configuration :

```text
DB      : powerflow_deep_900.db
Port    : 55557
Lookback: M1 900 / M5 900 / M15 900
```

But :

```text
champ plus stable
bruit réduit
```

---

## 4. Concepts issus de la session Agentic Core

### DBVisionGuard

Agent qui vérifie si PowerFlow voit vraiment.

Sorties :

```text
VISION_OK
TACTICAL_OK
DATA_PARTIAL
DATA_BLIND
LIVE_EXTENDED_ACTIVE
LEGACY_FORCE_ONLY
HISTORICAL_GAP_DETECTED
SCHEMA_EXTENDED_OK
SCHEMA_EXTENDED_PARTIAL
```

---

### FlowEventExtractor

Agent qui découpe le film en phases.

Sorties :

```text
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
SECOND_LEG
```

Règle critique :

```text
Une respiration contraire après confirmation ne doit pas être classée comme nouveau node principal.
```

---

### SceneNamer

Agent qui nomme la scène.

Règle :

```text
Il nomme.
Il ne recalcule pas.
Il ne décide pas.
```

---

### Weekly Agent Scan

Scanner historique force-only.

Fonction :

```text
scanner fenêtres glissantes
détecter scènes
clusteriser les hits
sortir candidats Lab
```

---

### Gap-Aware Cluster

Cluster qui prend en compte les trous de DB.

Utilité :

```text
éviter que les gaps historiques collent artificiellement des demi-journées
```

Paramètres utiles :

```text
cluster_gap_minutes
max_cluster_minutes
min_rows_window
```

---

## 5. Famille de rotation découverte

### GRAVITY_RESPRING_ROTATION_FAMILY

Définition :

```text
Famille de séquences où un bloc gravité/refuge/pivot reprend violemment le champ contre un bloc opposé,
puis passe par confirmation, respiration contraire et absorption.
```

Structure :

```text
PRE_FIELD optionnel
→ NODE_BIRTH
→ CONFIRMATION
→ COUNTER_BREATH
→ ABSORPTION
→ WATCH_SECOND_LEG
```

Signatures :

```text
bloc respring
bloc fold
énergie forte
opposition de blocs
confirmation après naissance
respiration contraire
absorption
```

---

### USD_CAD_JPY_RESPRING_VS_RISK_FOLD

Sous-pattern de `GRAVITY_RESPRING_ROTATION_FAMILY`.

Structure :

```text
USD/CAD/JPY ou JPY/CAD/USD respring
contre
EUR/GBP/AUD/CHF fold
```

Exemples validés :

```text
2026-05-04 09:00→10:15
JPY+CAD+USD vs EUR+GBP+AUD+CHF

2026-05-01 08:00→09:30
JPY+CAD+USD vs EUR+GBP+CHF+AUD
```

---

### RAW_VARIANT_ROTATION

Variante de rotation où la structure séquentielle est complète, mais où les blocs ne correspondent pas exactement au sous-pattern central.

Exemple :

```text
2026-04-30 17:30→19:00
AUD+CAD+CHF+JPY vs EUR+USD+GBP
```

Lecture :

```text
séquence complète
famille proche
bloc différent
à documenter avec screens
```

---

### LAB_MATCH_FORT

Fenêtre historique ou live qui répète fortement une structure Lab connue.

Critères :

```text
même famille de blocs
mêmes phases
même ordre temporel
node + confirmation + breath + absorption
```

Exemple :

```text
2026-05-01 08:00→09:30
match fort de LAB_004
```

---

### LAB_MATCH_PARTIEL

Fenêtre qui répète la structure séquentielle mais avec une variation notable des acteurs.

Critères :

```text
mêmes phases
même dynamique
blocs différents ou incomplets
contexte DB partiel
```

---

### FRACTAL_ROTATION_IMBRICATION

Imbrication d’une séquence courte dans une rotation plus large.

Définition :

```text
Le node local n’est pas isolé.
Il appartient à une rotation visible sur plusieurs fenêtres et timeframes.
```

Phrase :

```text
La fractalité confirme que le node n’est pas un point.
C’est une séquence imbriquée dans une rotation plus large.
```

---

## 6. Règles ajoutées

```text
M1 bavarde hors fenêtre.
M1 révèle la naissance dans la bonne fenêtre.
```

```text
Le signal n’est pas un point.
Le signal est une séquence.
```

```text
Une respiration opposée tardive ne doit pas voler le NODE_BIRTH principal.
```

```text
La DB V2 extended devient la sonde agentique future.
```

```text
Legacy force-only reste utile pour backtester les familles de forces.
```

```text
Les gaps historiques doivent être signalés, pas confondus avec une panne live.
```

```text
Un cluster hebdo doit être gap-aware pour éviter les demi-journées artificielles.
```

---

## 7. Prochaine intégration

Ce patch doit être fusionné dans :

```text
LEXIQUE_GRAMMAIRE_POWERFLOW_V6_CONSOLIDE_2026-05-04.md
```

Puis utilisé pour créer :

```text
LAB_FAMILY_GRAVITY_RESPRING_ROTATION_2026-05-04.md
FlowEventExtractor V0.2 Extended
FractalWindowEngine V0.1
Daily Agent Scan V0.1
```

Fin du patch.
