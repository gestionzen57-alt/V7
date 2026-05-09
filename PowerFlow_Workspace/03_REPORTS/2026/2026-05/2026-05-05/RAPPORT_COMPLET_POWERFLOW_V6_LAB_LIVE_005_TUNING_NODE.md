# RAPPORT COMPLET — POWERFLOW V6 — LAB LIVE 005
## Tuning Temporal Node / M1 Alignment Ignition / M15 Rotation Window

**Date :** 2026-05-05  
**Statut :** Lab live improvisé terminé — à consolider  
**Symbole principal :** GBPUSD  
**Mode :** observation trader + screens MT4 + DB partielle + probes read-only  

---

## 0. Résumé

Ce Lab live a montré que le **Temporal Node** ne doit pas être réduit à un croisement géométrique.

Un node PowerFlow est plutôt :

```text
une fenêtre temporelle d’énergie
+ compression / range vivant
+ angles qui se rapprochent
+ gravité serrée entre devises
+ cross / decross / recross
+ premier détachement
+ prix qui rattrape ou se fait absorber
```

Découverte centrale :

```text
Le scalp semble venir du M1 quand il s’aligne dans un champ M5/M15 déjà chargé.
Le signal perceptif n’est pas le cross.
Le signal perceptif est l’ignition :
M1 alignment → first detachment → price catch-up.
```

Nom central :

```text
M1_ALIGNMENT_IGNITION_INSIDE_M5_LOADED_FIELD
```

---

## 1. État technique du Lab

### Ce qui a fonctionné

```text
- Le patch Temporal Node V0.6 a fonctionné.
- Le JSON a sorti node_context / extended / telegram_candidates.
- Le M5 a été récupéré après correction de l’EA.
- Le node est repassé HOT_NODE après retour de la donnée M5.
```

Sortie importante après récupération M5 :

```text
HOT_NODE
NODE_COMPLET_FULL
score = 16.0
direction_bias = GBP pressure up / USD pressure down
structure_label = M5_HOT_NODE_WITH_M1_RESPRING_INSIDE_HTF_BATTLE
extended_micro_window = MICRO_WINDOW_ACTIVE_WEAK
```

Raisons détectées :

```text
cross
kiss_reject
repulsion
convergence
force_shift
price_lag_then_catchup
m1_microfilm_context
m15_energy_relay
htf_battle_context
micro_window_active_weak
```

### Ce qui a posé problème

```text
M1  stale pendant le Lab.
M15 stale pendant le cross attendu.
M30/H1 stale.
M5 mal attaché pendant un moment critique.
DB du matin incomplète.
```

État critique à garder :

```text
VISUAL_NODE_CONFIRMED
DB_NODE_NOT_CONFIRMED
CAPTURE_GAP_DURING_CRITICAL_EVENT
```

---

## 2. Lecture HTF / M15 / M5 / M1

### HTF

```text
H1 / H4 / Daily / Weekly = bataille / mémoire / poids supérieur.
H4 avait posé un ancrage énergétique.
Daily / Weekly donnaient une mémoire plus lourde.
```

Concepts :

```text
HTF_BATTLE_CONTEXT_ACTIVE
H4_MULTI_CURRENCY_ROTATION_NODE
H4_GBP_DESCENT_THROUGH_MULTI_CURRENCY_CLUSTER
HTF_SHOCK_MEMORY
SESSION_CARRIED_IMBALANCE
```

### M15

```text
M15 = fenêtre énergétique / battle window.
Le cross M15 attendu a été vu visuellement.
La DB n’a pas capté le cross car le feed M15 était stale.
```

Concepts :

```text
VISUAL_M15_CROSS_EVENT_CONFIRMED
M15_CROSS_FLIP_BATTLE_WINDOW
M15_PINCH_ENERGY_WINDOW
M15_ROTATION_NODE_PRE_US
M15_ENERGY_RELAY_WITHOUT_REQUIRED_FULL_CROSS
```

### M5

```text
M5 = trigger tactique mesuré.
Après correction EA, M5 a réactivé le node.
```

Concepts :

```text
M5_LOADED_FIELD
M5_HOT_TACTICAL_TRIGGER
M5_PRICE_CATCHUP_RELEASE
M5_RELEASE_AFTER_RANGE_WITH_FORCE_HOLD_BUT_ACCELERATION_FADE
```

### M1

```text
M1 = microfilm / ignition.
En scalp, le trader attend l’alignement M1.
Quand le M1 s’aligne dans un champ M5 chargé, le départ devient perceptible.
```

Concept central :

```text
M1_ALIGNMENT_IGNITION_INSIDE_M5_LOADED_FIELD
```

---

## 3. Règle importante : même angle ≠ direction

Règle issue du Lab :

```text
Quand trois devises ont à peu près le même angle,
ce n’est pas encore une direction.
C’est souvent range / accumulation de liquidité / énergie stockée.
```

Nom :

```text
TRIPLE_PARALLEL_ANGLE_RANGE
SAME_ANGLE_LIQUIDITY_ACCUMULATION_FIELD
```

Direction seulement quand :

```text
une devise casse l’angle commun
= FIRST_DETACHMENT_IGNITION
```

---

## 4. Paramètres à mesurer

### Angle parallèle

```text
ANGLE_CLOSE_DEG = 8 à 12 degrés
MIN_PARALLEL_POINTS_M1 = 3 snapshots
MIN_PARALLEL_POINTS_M5 = 2 bougies
```

### Gravité serrée

```text
TIGHT_FORCE_GAP = 8 à 12 points sur l’échelle 0-100
gap_stable = distance stable ou qui se réduit
centroid_stable = centre moyen qui ne fuit pas violemment
```

### Pincement

```text
angle proche
+ force proche
+ cross / decross / recross
= PINCH_ENERGY_BUILDUP
```

### Premier détachement

```text
une devise sort de l’angle commun
+ distance qui s’ouvre
+ prix encore en retard ou commence à rattraper
= FIRST_DETACHMENT_IGNITION
```

---

## 5. Énergie d’une devise

L’énergie d’une devise ne doit pas être seulement sa force brute.

Elle doit intégrer :

```text
force brute
vitesse
angle
accélération
écart au panier
z-score comportemental
tension de zone
persistance
absorption / fuite
contexte HTF
```

Formule V0.7 provisoire :

```text
currency_energy =
  0.25 * force_position
+ 0.20 * speed_score
+ 0.15 * angle_score
+ 0.20 * basket_deviation
+ 0.15 * zone_tension
+ 0.05 * persistence
+ bonus / malus contextuels
```

Bonus / malus :

```text
+ absorption_bonus
+ htf_alignment_bonus
+ coalition_bonus
+ first_detachment_bonus
+ acceleration_bonus
- spread_friction_penalty
- stale_data_penalty
- dead_flat_penalty
```

---

## 6. Accélération

L’accélération devient une couche prioritaire.

Formule :

```text
speed_t = (force_t - force_t-1) / minutes
acceleration_t = (speed_t - speed_t-1) / minutes
```

Ou forme discrète :

```text
acceleration = force_now - 2*force_previous + force_before
```

Cas live observé :

```text
M5 bars5 = force large encore forte.
M5 bars2 = impulsion fraîche en décélération.
```

État nommé :

```text
M5_RELEASE_AFTER_RANGE_WITH_FORCE_HOLD_BUT_ACCELERATION_FADE
```

Conclusion :

```text
La cassure prix était réelle.
Le node était HOT.
Mais l’accélération fraîche n’était pas explosive.
Donc : RELEASE_CANDIDATE, pas SECOND_LEG confirmé.
```

---

## 7. Probes utilisés

### Temporal Node

```powershell
python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --visual-htf-story confirmed --out output/temporal_node_state.json --pretty
```

### Force / angle / vitesse

```powershell
python pf_force_angle_speed_probe.py --db powerflow.db --symbol GBPUSD --timeframes 5 --bars 2 --out output/force_angle_speed_m5_bars2.json --pretty
python pf_force_angle_speed_probe.py --db powerflow.db --symbol GBPUSD --timeframes 5 --bars 5 --out output/force_angle_speed_m5_bars5.json --pretty
```

Limites du probe V0.1 :

```text
- pas d’accélération
- pas de fraîcheur relative
- pas d’angle cluster
- pas de gravity cluster
- pas de first detachment
```

---

## 8. Points positifs

```text
1. La perception trader a été exprimée en live.
2. Les briques invisibles ont été nommées.
3. Le node a cessé d’être un simple cross.
4. V0.6 a validé la structure node_context.
5. Le moteur a réagi après récupération M5.
6. La règle “même angle = range” a été clarifiée.
7. FIRST_DETACHMENT devient central.
8. L’accélération devient une couche obligatoire.
9. La séparation DB / visuel / HTF a été clarifiée.
10. Le rôle M1 en scalp a été mieux nommé.
```

---

## 9. Points faibles

```text
1. Capture multi-timeframe instable.
2. M1 stale.
3. M15 stale pendant l’événement attendu.
4. M5 mal attaché pendant une partie du Lab.
5. DB du matin incomplète.
6. LIVE_OK trompeur sans fraîcheur relative.
7. next_watch trop pauvre.
8. Telegram dry-run encore brut.
9. Pas encore d’accélération dans le probe.
10. Le moteur peut confondre trigger M5 et biais M15/HTF.
```

---

## 10. États techniques à ajouter

```text
CAPTURE_GAP_DURING_NODE
VISUAL_NODE_CONFIRMED_DB_NOT_CONFIRMED
DB_M5_TRIGGER_AGAINST_VISUAL_M15_HTF_BIAS
STALE_RELATIVE_TO_M5
M15_FEED_STALE
M1_FEED_STALE
EA_MISATTACHED
```

---

## 11. Patchs recommandés

### P0 — Stabiliser capture

```text
M1 live
M5 live
M15 live
M30/H1 cohérents
check_tf_counts.py avant Lab
capture_bridge visible
```

### P1 — Probe V0.2

Créer ou étendre :

```text
pf_force_acceleration_probe.py
```

Champs :

```text
force
speed
angle
acceleration
deceleration
angle_cluster
tight_gravity_cluster
first_detachment
relative_freshness
price_break_context
pip_range_expansion
volume_expansion
```

### P2 — Temporal Node V0.7

Ajouter :

```text
angle_state
gravity_state
microstructure_state
acceleration_state
release_state
direction_conflict
visual_node_tf
db_trigger_tf
measured_trigger_bias
visual_structural_bias
stale_timeframes
capture_quality
next_watch enrichi
```

### P3 — Telegram dry-run V0.2

Messages :

```text
NODE RANGE ACCUMULATION
NODE IGNITION WATCH
NODE RELEASE CANDIDATE
NODE SECOND LEG WATCH
NODE FAKE BREAK ABSORPTION WATCH
CAPTURE GAP WARNING
```

---

## 12. JSON cible V0.7

```json
{
  "node_context": {
    "structure_label": "M1_ALIGNMENT_IGNITION_INSIDE_M5_LOADED_FIELD",
    "visual_node_tf": "M15",
    "db_trigger_tf": "M5",
    "measured_trigger_bias": "GBP pressure up / USD pressure down",
    "visual_structural_bias": "M15/HTF battle",
    "direction_conflict": true
  },
  "microstructure": {
    "angle_state": "TRIPLE_PARALLEL_ANGLE_RANGE",
    "gravity_state": "TIGHT_GRAVITY_CLUSTER",
    "liquidity_state": "ACCUMULATING",
    "direction_status": "NO_DIRECTION_YET",
    "first_detachment": null
  },
  "release": {
    "price_state": "PRICE_LAG_THEN_CATCHUP",
    "acceleration_state": "FORCE_HOLD_WITH_ACCELERATION_FADE",
    "release_state": "RELEASE_CANDIDATE",
    "second_leg": false
  },
  "capture_quality": {
    "live_reference_tf": "M5",
    "stale_timeframes": ["M1", "M15", "M30", "H1"],
    "capture_gap": true
  },
  "next_watch": [
    "WATCH_FIRST_DETACHMENT",
    "WATCH_ACCELERATION_HOLD",
    "WATCH_SECOND_LEG",
    "WATCH_FAKE_BREAK_ABSORPTION",
    "WATCH_M15_FEED_RECOVERY"
  ]
}
```

---

## 13. Prochaine session recommandée

Préparer un Lab propre :

```text
M1 actif
M5 actif
M15 actif
check_tf_counts.py OK avant le live
screens M1/M5/M15
temporal_node_state toutes les 5 min
force/angle/speed/acceleration toutes les 5 min
```

Objectif :

```text
Valider mathématiquement :
TRIPLE_PARALLEL_ANGLE_RANGE
TIGHT_GRAVITY_CLUSTER
FIRST_DETACHMENT_IGNITION
M1_ALIGNMENT_IGNITION
RELEASE_AFTER_RANGE
FAKE_BREAK_ABSORPTION
```

---

## 14. Phrase de reprise

```text
Le Lab live 005 a montré que le node n’est pas un point.
C’est une fenêtre d’énergie.
Le même angle crée le range.
Le premier détachement crée l’ignition.
Le M1 allume.
Le M5 déclenche.
Le M15 porte la fenêtre.
Le HTF donne le poids.
La DB doit être assez fraîche pour raconter le film.
```
