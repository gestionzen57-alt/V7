# CURRENT_STATE — POWERFLOW V6
## 2026-05-06 — Behavioral Flow + Relational Gravity Guard

Statut : ACTIVE / RUNTIME VALIDÉ

## État actif

Chaîne live validée :

```text
Node V0.8.2
→ Energy Release Alignment
→ Behavioral Mapper V0.8.3
→ Behavioral Alert Queue
→ Cockpit Agentic State
→ Dashboard Sync Agent
→ Dashboard Server Sync
→ Dashboard Live Behavioral Flow
```

Dashboard live :

```text
BEHAVIORAL FLOW
HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
FIRST_DETACHMENT_WITH_CLEAN_RELAY
```

Alerte RG ajoutée :

```text
RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

## Doctrine active

```text
Energy ≠ Direction
Energy ≠ Signal
Node Heat ≠ Currency Energy
Counter Release Attempt ≠ Release Confirmed
Relational Gravity direction ≠ leader fiable
topline_reliable=false → pas de HOT leader
```

## Relational Gravity Guard — validé

### P1.2 Bridge Guard

Fichier : `pf_relational_gravity_bridge.py`  
Version : `0.1.2`

Champs ajoutés :

```text
direction_consistency
leader_consistency
antagonist_consistency
topline_reliable
```

Règle : si les TFs ne s’accordent pas sur un leader :

```text
dominant_leader = MIXED
leader_consistency = CONFLICT
topline_reliable = false
```

### P1.2.2 Topline State

Version : `0.1.3`

Champ ajouté :

```text
topline_state
```

Runtime validé :

```text
cross_tf_state = RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15
dominant_direction = UP
dominant_leader = MIXED
direction_consistency = ALIGNED
leader_consistency = CONFLICT
antagonist_consistency = DEDUPED
topline_reliable = false
topline_state = RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT
```

Lecture : direction commune visible, mais leader non fiable.

## Behavioral Mapper P2 — validé

Fichier : `pf_behavioral_alert_mapper.py`  
Version : `0.8.3`

Signature :

```python
map_behavioral_alerts(..., relational_gravity: dict | None = None)
```

Checkers RG :

```text
RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
LEADER_CONFLICT_INFO
RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO
```

Garde-fous :

```text
topline_reliable=false → jamais HOT
dominant_leader=MIXED → jamais leader fiable
no BUY/SELL
```

## Runners P2.1 / P2.1.1 — validés

Fichier : `run_powerflow_dashboard_refresh_once.py`

Ajouts :

```text
P2.1   passe relational_gravity au mapper
P2.1.1 ajoute --refresh-cockpit-from-queue
```

Commande live rapide validée :

```powershell
python .\run_powerflow_dashboard_refresh_once.py `
  --skip-cockpit `
  --refresh-cockpit-from-queue `
  --pretty `
  --summary
```

Résultat validé :

```text
mapper = 6
cockpit_behavioral_count = 6
dashboard alerts_count = 6
```

## Alertes runtime

```text
[HOT]   FIRST_DETACHMENT_WITH_CLEAN_RELAY
[WATCH] COUNTER_RELEASE_ATTEMPT_ALERT
[WATCH] NODE_HEAT_ENERGY_DIVERGENCE
[INFO]  TIGHT_GRAVITY_CLUSTER_ALERT
[INFO]  SAME_ANGLE_CLUSTER_ALERT
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

Lecture : M1 détache, M5 relaie, release counter attempt, Energy divergente/thin, Relational Gravity direction alignée mais leader conflictuel.

## Prochaine étape

Sur autre fil : patch lexique complet Relational Gravity Guard P1.2 / P1.2.2 / P2 / P2.1.1.
