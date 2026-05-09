# CHECKPOINT POWERFLOW V6 — 2026-05-06
## Relational Gravity Guard / Behavioral Mapper P2 / Runner P2.1.1

Statut : VALIDÉ RUNTIME

## Résumé

Relational Gravity enrichit maintenant le Behavioral Flow sans mentir sur le leader.

Runtime validé :

```text
direction_consistency = ALIGNED
leader_consistency = CONFLICT
dominant_leader = MIXED
topline_reliable = false
topline_state = RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT
```

Alerte ajoutée :

```text
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

## Briques validées

```text
P1.2   Relational Gravity Bridge Guard        VALIDÉ
P1.2.2 Topline State                          VALIDÉ
P2     Behavioral Mapper Guard-Aware          VALIDÉ
P2.1   Full Refresh Runner RG-aware           VALIDÉ
P2.1.1 Refresh Cockpit From Queue             VALIDÉ
```

## Fichiers concernés

```text
pf_relational_gravity_bridge.py
pf_behavioral_alert_mapper.py
run_behavioral_alert_mapper_once.py
run_powerflow_dashboard_refresh_once.py
cockpit_agentic_state_v01.py
dashboard_sync_agent_v01.py
```

## État final des alertes

```text
[HOT]   FIRST_DETACHMENT_WITH_CLEAN_RELAY
[WATCH] COUNTER_RELEASE_ATTEMPT_ALERT
[WATCH] NODE_HEAT_ENERGY_DIVERGENCE
[INFO]  TIGHT_GRAVITY_CLUSTER_ALERT
[INFO]  SAME_ANGLE_CLUSTER_ALERT
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

Dashboard :

```text
behavioral_count = 6
degraded_count = 0
top_alert = FIRST_DETACHMENT_WITH_CLEAN_RELAY
top_level = HOT
behavioral_flow_status = HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
```

## Commandes validées

Full refresh complet :

```powershell
python .\run_powerflow_dashboard_refresh_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --start 2026-05-06T08:00:00 `
  --end 2026-05-06T13:30:00 `
  --visual-htf-story confirmed `
  --pretty `
  --summary
```

Refresh rapide :

```powershell
python .\run_powerflow_dashboard_refresh_once.py `
  --skip-cockpit `
  --refresh-cockpit-from-queue `
  --pretty `
  --summary
```

## Prochaines actions

```text
P1 — Patch lexique Relational Gravity Guard sur autre fil.
P2 — Intégrer les termes dans LEXIQUE_UPDATE_QUEUE.
P3 — Éventuellement P2.2 : ajouter film_step [RELATIONAL_GRAVITY].
P4 — Éventuellement P2.3 : mode --recent-minutes auto.
```

Phrase checkpoint :

```text
Relational Gravity enrichit le Behavioral Flow en WATCH quand la direction est alignée mais le leader conflictuel.
```
