# ROADMAP UPDATE — KINEMATICS / ENERGY / RELATIONAL GRAVITY

Date : 2026-05-06

## P0 — Runtime validation DB

Tester :

```text
Node / Kinematics
Currency Energy
Relational Gravity standalone
Cockpit Bridge Relational Gravity
```

## P1.2 — Relational Gravity Bridge Guard

Condition :

```text
Si RELATIONAL_GRAVITY_MIXED est raconté comme un leader clair.
```

Patch cible :

```text
pf_relational_gravity_bridge.py
```

Règles :

```text
MIXED => dominant_leader = MIXED
MIXED => leader_consistency = CONFLICT
MIXED => topline_reliable = false
leader absent de dominant_antagonist
direction_consistency ajouté
leader_consistency ajouté
antagonist_consistency ajouté
topline_reliable ajouté
tf_details intacts
```

## P2 — Behavioral Mapper

Autorisé uniquement si P1.2 est propre.

Fichier cible :

```text
pf_behavioral_alert_mapper.py
```

Alertes futures :

```text
RELATIONAL_GRAVITY_ALIGNED_ALERT
LEADER_PULLING_AWAY_ALERT
M1_RELATIONAL_COUNTERFIELD_ALERT
M5_M15_RELATIONAL_ALIGNMENT_ALERT
COALITION_VS_ANTAGONIST_EXPANSION_ALERT
RELATIONAL_GRAVITY_MIXED_INFO
LEADER_CONFLICT_INFO
```

Règle critique :

```text
Si cross_tf_state = RELATIONAL_GRAVITY_MIXED :
ne pas produire LEADER_PULLING_AWAY_ALERT HOT/WATCH.
Produire RELATIONAL_GRAVITY_MIXED_INFO.
Produire éventuellement LEADER_CONFLICT_INFO.
```
