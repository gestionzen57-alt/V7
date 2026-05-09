# PATCH LEXIQUE — KINEMATICS / ENERGY / RELATIONAL GRAVITY / BEHAVIORAL FLOW

Date : 2026-05-06  
Statut : À intégrer dans `LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md`  
Objet : officialiser les briques runtime récentes et préparer les tests de séquences DB.

## 1. Kinematics

### KINEMATICS_STATE
Bloc d’état qui décrit la mécanique vivante du mouvement : angle, vitesse, accélération, détachement, clusters et release_state.

### ANGLE_STATE
Lecture des angles de force par devise et par timeframe. Sert à détecter poussée, pliure, décrochage, alignement, divergence GBP/USD.

### SPEED_STATE
Lecture de la vitesse de variation de force. Sert à détecter accélération locale, ralentissement, impulsion, fade mécanique.

### ACCELERATION_STATE
Lecture du changement de vitesse. Sert à qualifier mouvement qui se renforce, fatigue, plie ou se retourne mécaniquement.

### FIRST_DETACHMENT
Premier décrochage mécanique significatif d’une devise.

```text
FIRST_DETACHMENT ≠ RELEASE_CONFIRMED
```

### SAME_ANGLE_CLUSTER
Groupe de devises dont les angles sont proches dans le même sens.

### TIGHT_GRAVITY_CLUSTER
Groupe de devises proches en niveau de force.

### RELEASE_STATE
État typé de tentative ou confirmation de libération mécanique.

Valeurs :
```text
RELEASE_ATTEMPT
RELEASE_CANDIDATE
RELEASE_CONFIRMED
COUNTER_RELEASE_ATTEMPT
FAKE_RELEASE
RELEASE_REJECTED
```

### RELEASE_ATTEMPT
Tentative de release mécanique non encore qualifiée.

### RELEASE_CANDIDATE
Tentative avec plusieurs conditions favorables, mais sans confirmation complète.

### RELEASE_CONFIRMED
Release mécaniquement confirmée par détachement, relais et cohérence suffisante.

### COUNTER_RELEASE_ATTEMPT
Tentative de contre-release ou mouvement opposé au champ attendu.

```text
COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED
```

### FAKE_RELEASE
Mouvement de release apparent absorbé ou invalidé par le champ.

### RELEASE_REJECTED
Release rejetée faute de détachement, de relais ou de charge suffisante.

---

## 2. Energy

### CURRENCY_ENERGY
Mesure de la charge comportementale d’une devise.

```text
Energy ≠ direction
Energy ≠ signal
```

### ENERGY_RELEASE_ALIGNMENT
Bloc qui compare release_state et Currency Energy.

### ENERGY_NEUTRAL_OR_TOO_THIN
État où l’énergie du couple ou du champ est trop neutre/faible pour soutenir la release.

### ENERGY_THIN_OR_MIXED
État où l’énergie est présente mais dispersée, contradictoire ou trop mince.

### COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
Counter release visible mécaniquement mais non soutenue par la charge énergétique.

### PAIR_ENERGY_NOT_CONFIRMED
GBP/USD ou paire observée sans charge énergétique de couple suffisante.

### ENERGY_QUALIFIES_RELEASE_STATE
Energy qualifie release_state. Energy ne crée pas release_state.

### ENERGY_DOES_NOT_CREATE_SIGNAL
Currency Energy ne produit aucun BUY/SELL. Elle qualifie l’intensité comportementale.

---

## 3. Relational Gravity

### RELATIONAL_GRAVITY_STATE
Mesure la relation vivante entre devises : alignement, distance, variation de distance, leader/follower, antagoniste et cohérence multi-TF.

```text
Relational Gravity ≠ signal
Relational Gravity ≠ Currency Energy
Relational Gravity ≠ Node
```

### RELATIONAL_GRAVITY_BRIDGE
Pont de synthèse entre probes Relational Gravity M1/M5/M15 et cockpit.

### RELATIONAL_GRAVITY_COCKPIT_BLOCK
Bloc cockpit exposant la synthèse relationnelle.

### RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15
Alignement relationnel propre entre M1, M5 et M15.

### M1_RELATIONAL_COUNTERFIELD
Champ relationnel M1 qui contre ou nuance le champ dominant supérieur.

### M5_M15_RELATIONAL_ALIGNMENT
M5 et M15 racontent un champ relationnel compatible.

### RELATIONAL_GRAVITY_MIXED
Champ relationnel mixte ou conflictuel.

Règle critique :
```text
Si RELATIONAL_GRAVITY_MIXED :
ne pas raconter un leader top-level clair.
```

### RELATIONAL_GRAVITY_MISSING
Bloc absent ou probe indisponible.

### DIRECTION_MIN_DELTA
Seuil minimal de variation directionnelle pour éviter les devises fantômes.

### GHOST_CURRENCY_IN_GROUP
Devise incluse dans un groupe malgré une variation trop faible ou incohérente.

### RELATIONAL_GROUP_PURIFIED
Groupe nettoyé des ghost currencies.

### DOMINANT_RELATIONAL_LEADER
Leader relationnel dominant si et seulement si la synthèse est fiable.

### DOMINANT_RELATIONAL_ANTAGONIST
Antagoniste relationnel dominant.

Règle :
```text
dominant_leader ne doit jamais apparaître aussi dans dominant_antagonist.
```

### CROSS_TF_RELATIONAL_GRAVITY_STATE
État relationnel multi-timeframe agrégé.

### LEADER_CONFLICT_INFO
Info émise quand les TF ou groupes racontent des leaders incompatibles.

### TOPLINE_RELIABILITY
Fiabilité de la synthèse top-level.

```text
MIXED => topline_reliable = false
```

---

## 4. Behavioral Flow

### BEHAVIORAL_FLOW
Synthèse comportementale qui relie Node, Kinematics, Energy et Relational Gravity sans produire de signal trading.

### HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
Node chaud + détachement/counter release + Energy divergente.

### FIRST_DETACHMENT_WITH_CLEAN_RELAY
First detachment avec relais M5 clean, mais pas forcément release confirmée.

### NODE_HEAT_ENERGY_DIVERGENCE
Node Heat fort mais Currency Energy faible/mixte.

### HOT_BEHAVIORAL_NOT_RELEASE_CONFIRMED
Champ comportemental chaud mais release_state non confirmée.

---

## 5. Règles de non-confusion ajoutées

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
