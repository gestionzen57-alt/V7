# CURRENT STATE UPDATE — KINEMATICS / ENERGY / RELATIONAL GRAVITY

Date : 2026-05-06  
Statut : Pré-runtime validation DB

## Briques à considérer actives / à tester

```text
KINEMATICS_STATE
CURRENCY_ENERGY
ENERGY_RELEASE_ALIGNMENT
RELATIONAL_GRAVITY_STATE
RELATIONAL_GRAVITY_BRIDGE
RELATIONAL_GRAVITY_COCKPIT_BLOCK
BEHAVIORAL_FLOW
```

## Règles officielles

```text
NODE ≠ CROSS
Energy ≠ direction
Energy ≠ signal
Node Heat ≠ Currency Energy
First Detachment ≠ Dominant Currency Energy
Relay clean ≠ release confirmée
Counter release attempt ≠ release confirmed
Relational Gravity ≠ signal
Relational Gravity ≠ Currency Energy
Relational Gravity ≠ Node
Relational Gravity mesure la relation vivante entre devises
```

## Chantier actif

```text
P1.2 Relational Gravity Bridge Guard
```

Priorité :

```text
Empêcher le bridge de raconter un leader clair si le champ multi-TF est MIXED.
```

## P2 Behavioral Mapper

Statut :

```text
BLOQUÉ tant que P1.2 n’est pas propre.
```

Condition de déblocage :

```text
cross_tf_state correct
MIXED => top-level non fiable
dominant_leader = MIXED ou leader_consistency = CONFLICT
dominant_antagonist ne contient pas le leader
tf_details intacts
```
