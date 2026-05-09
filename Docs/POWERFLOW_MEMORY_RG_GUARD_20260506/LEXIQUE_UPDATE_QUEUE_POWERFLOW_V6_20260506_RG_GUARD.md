# LEXIQUE_UPDATE_QUEUE — POWERFLOW V6
## Mise à jour 2026-05-06 — Relational Gravity Guard P1.2 / P1.2.2 / P2 / P2.1.1

Statut : À intégrer dans le lexique complet sur un autre fil.

## Termes à ajouter

```text
RELATIONAL_GRAVITY_BRIDGE_GUARD
RELATIONAL_GRAVITY_TOPLINE_STATE
RELATIONAL_GRAVITY_TOPLINE_RELIABLE
RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT
RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT
RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE
RELATIONAL_GRAVITY_TOPLINE_PARTIAL
RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO
LEADER_CONFLICT_INFO
direction_consistency
leader_consistency
antagonist_consistency
topline_reliable
topline_state
dominant_leader = MIXED
```

## Définitions courtes

### RELATIONAL_GRAVITY_BRIDGE_GUARD

Garde de cohérence dans le bridge Relational Gravity. Empêche la topline de déclarer un leader fiable quand les TFs ne s’accordent pas.

### topline_reliable

Booléen indiquant si la topline Relational Gravity peut être utilisée comme synthèse fiable. Si false : pas de HOT leader.

### topline_state

État compact destiné au mapper. Résume la fiabilité de la topline en une seule clé.

### RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT

Les TFs sont alignés en direction, mais le leader est conflictuel. Direction visible, leader non fiable.

### RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO

Alerte comportementale INFO/WATCH. Signale une direction relationnelle alignée avec leadership conflictuel.

### dominant_leader = MIXED

Le bridge refuse de choisir un leader unique quand les TFs divergent. MIXED n’est pas une devise et ne doit jamais être traité comme leader exploitable.

## Règles de non-confusion

```text
Relational Gravity direction ≠ leader fiable
topline_reliable=false ≠ signal
dominant_leader=MIXED ≠ devise dominante
direction_consistency=ALIGNED ≠ HOT
leader_consistency=CONFLICT → pas de leader HOT
topline_state informe le mapper, il ne décide pas seul
```

## Règle P2 active

Si `topline_reliable = false`, le mapper peut produire :

```text
RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
LEADER_CONFLICT_INFO
RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO
```

Interdit :

```text
RELATIONAL_GRAVITY_ALIGNED_ALERT HOT
LEADER_PULLING_AWAY_ALERT HOT
tout HOT basé sur dominant_leader=MIXED
tout signal BUY/SELL
```

Phrase noyau :

```text
Relational Gravity enrichit le Behavioral Flow sans mentir sur le leader.
```
