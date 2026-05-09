# PATCH LEXIQUE — NODE / RELEASE / ENERGY POWERFLOW V6

Date : 2026-05-06
Statut : patch lexique à intégrer

## Node

Un node PowerFlow est une fenêtre d’énergie et de partition des forces.

```text
NODE ≠ CROSS
CROSS = manifestation possible du node
NODE = événement de flux
```

## Relay Quality

Qualité du relais tactique M5.

```text
M5_RELAY_MISSING_IN_DB
M5_RELAY_THIN_SAMPLE
M5_RELAY_CLEAN
```

Règle :

```text
M5 live ne veut pas forcément dire M5 clean.
```

## Kinematics State

Bloc qui qualifie la cinématique du node :

```text
angle_state
speed_state
acceleration_state
first_detachment
same_angle_cluster
tight_gravity_cluster
force_hold_with_acceleration_fade
```

## Release State

Classification de maturité d’une libération potentielle :

```text
RELEASE_ATTEMPT
RELEASE_CANDIDATE
RELEASE_CONFIRMED
COUNTER_RELEASE_ATTEMPT
FAKE_RELEASE
RELEASE_REJECTED
```

Règles :

```text
Pas de first_detachment = pas de release confirmée.
Relay clean seul ne suffit pas.
COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED.
```

## Currency Energy

Mesure de la force vivante contextualisée d’une devise.

```text
Energy ≠ Direction
Energy ≠ Signal
Energy ≠ Node Heat
```

Phrase noyau :

```text
Node lit la structure et le détachement.
Energy lit la vitalité devise.
Density lira la charge de fenêtre.
Le cockpit doit afficher les trois sans les confondre.
```
