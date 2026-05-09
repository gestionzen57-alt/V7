# ROADMAP_ACTIVE — POWERFLOW V6

Date : 2026-05-06

## P0 — Mémoire officielle

```text
CURRENT_STATE.md
CHECKPOINT_LATEST.md
LEXIQUE_UPDATE_QUEUE.md
ROADMAP_ACTIVE.md
```

Objectif : ne plus perdre les avancées validées.

## P1 — Analyse de séquence DB

Analyser une séquence réelle avec :

```text
capture_quality
relay_quality
session_transition
kinematics_state
release_state
currency_energy
```

Sortie attendue :

```text
film de séquence
alertes comportementales utiles
dashboard fields à ajouter
patch minimal recommandé
```

## P2 — Behavioral Alert Agent

Sortie cible :

```text
output/behavioral_alert_queue.json
```

Alertes candidates :

```text
FIRST_DETACHMENT_WITH_CLEAN_RELAY
HOT_DEGRADED_BY_MISSING_RELAY
M5_RELAY_THIN_ALERT
RELEASE_REJECTED_NO_DETACHMENT
COUNTER_RELEASE_ATTEMPT
NODE_HEAT_NOT_EQUAL_CURRENCY_ENERGY
M1_ACTIVE_M5_WEAK
ACCELERATION_SPIKE_WITHOUT_ZONE_TENSION
TIGHT_GRAVITY_CLUSTER
SAME_ANGLE_CLUSTER
```

## P3 — Dashboard Sync Agent

Mission : transformer les JSON moteur en `dashboard_data.json`.

Blocs dashboard à ajouter :

```text
CAPTURE QUALITY
RELAY QUALITY
KINEMATICS STATE
RELEASE STATE
CURRENCY ENERGY
BEHAVIORAL ALERTS
NEXT WATCH
FILM
```

## P4 — Currency Energy V0.2

```text
basket_deviation_saturation_flag
acceleration_spike_without_zone_tension
component_overlap_warning
sample_continuity
zero_value_suspect
energy_component_quality
```

## P5 — Density Context V0.9

```text
density_context
window_charge
density_building
density_release
density_fade
```

## P6 — Energy Context → Node State

Seulement après plusieurs scènes et calibration Energy V0.2.

Ordre de combat :

```text
1. Mémoire officielle
2. Séquence DB avec briques actuelles
3. Behavioral Alert Agent
4. Dashboard Sync Agent
5. Energy V0.2
6. Density V0.9
7. Energy Context dans Node State
```
