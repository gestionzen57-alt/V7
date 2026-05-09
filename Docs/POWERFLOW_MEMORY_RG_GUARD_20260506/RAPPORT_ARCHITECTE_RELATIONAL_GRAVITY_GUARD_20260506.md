# RAPPORT ARCHITECTE — RELATIONAL GRAVITY GUARD
## P1.2 / P1.2.2 / P2 / P2.1.1
**Date : 2026-05-06**
**Statut : VALIDÉ RUNTIME**

## Objet

Cette phase a ajouté une garde de cohérence autour de Relational Gravity.

But : reconnaître une direction relationnelle commune sans déclarer un leader fiable quand les TFs sont en conflit.

## P1.2 — Bridge Guard

Fichier : `pf_relational_gravity_bridge.py`  
Version : `0.1.2`

Champs ajoutés :

```text
direction_consistency
leader_consistency
antagonist_consistency
topline_reliable
```

Règles :

```text
Leader conflict → dominant_leader = MIXED
Leader conflict → topline_reliable = false
Antagonist dedup quand leader réel identifiable
tf_details préservés
```

## P1.2.2 — Topline State

Version : `0.1.3`  
Champ : `topline_state`

Runtime :

```text
topline_state = RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT
direction_consistency = ALIGNED
leader_consistency = CONFLICT
dominant_leader = MIXED
topline_reliable = false
```

## P2 — Mapper Guard-Aware

Fichier : `pf_behavioral_alert_mapper.py`  
Version : `0.8.3`

Ajout :

```text
map_behavioral_alerts(..., relational_gravity=...)
```

Alerte runtime :

```text
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

Garde-fous : pas de HOT RG si `topline_reliable=false`, pas de leader HOT si `dominant_leader=MIXED`, no BUY/SELL.

## P2.1 / P2.1.1 — Runner

Fichier : `run_powerflow_dashboard_refresh_once.py`

```text
P2.1   Le runner passe relational_gravity au mapper.
P2.1.1 Ajout --refresh-cockpit-from-queue.
```

Validation :

```text
mapper = 6
cockpit_behavioral_count = 6
dashboard alerts_count = 6
```

## Alertes finales

```text
[HOT]   FIRST_DETACHMENT_WITH_CLEAN_RELAY
[WATCH] COUNTER_RELEASE_ATTEMPT_ALERT
[WATCH] NODE_HEAT_ENERGY_DIVERGENCE
[INFO]  TIGHT_GRAVITY_CLUSTER_ALERT
[INFO]  SAME_ANGLE_CLUSTER_ALERT
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

## Verdict

```text
Relational Gravity Guard est validé runtime.
La direction relationnelle enrichit le film.
Le conflit de leader est exposé.
Aucun HOT leader n’est produit si la topline n’est pas fiable.
```

Phrase noyau :

```text
Le moteur voit l’alignement relationnel sans mentir sur le leader.
```
