# FLOW ONTOLOGY — V0

## Objet

Formaliser les comportements détectables par PowerFlow comme ontologie de flux.

PowerFlow ne classe pas des figures chartistes.
PowerFlow nomme des comportements vivants :

- naissance ;
- inflexion ;
- compression ;
- tension ;
- absorption ;
- relâchement ;
- rotation ;
- structure ;
- coalition ;
- opposition ;
- propagation.

Une alerte PowerFlow n’est pas un ordre.
Une alerte PowerFlow est une perception transmise.

---

## Catégories comportementales

### 1. INFLEXION

Détection d’un changement de pente, d’un décrochage initial, d’une tentative de bascule ou d’une naissance de mouvement.

Événements associés :

- FIRST_DETACHMENT_MICRO
- FIRST_DETACHMENT_WITH_CLEAN_RELAY
- KINEMATIC_SHIFT
- COUNTER_RELEASE_ATTEMPT
- COUNTER_RELEASE_ATTEMPT_ALERT
- EARLY_SHIFT
- MICRO_BEND
- CURVATURE_CHANGE
- NODE_BIRTH
- FIRST_IMPULSE

Sous-catégories :

- Naissance
- Bascule micro
- Changement cinématique
- Premier détachement
- Tentative de contre-relâchement

---

### 2. COMPRESSION

Accumulation, resserrement temporel, densité croissante, phase d’élasticité chargée avant relâchement.

Événements associés :

- CYCLE_COMPRESSING
- ELASTIC_LOADED
- ORCHESTRAL_COMPRESSION
- REGIME_COMPRESSION
- TEMPORAL_DENSITY_ACTIVE
- TIGHT_GRAVITY_CLUSTER_ALERT
- SAME_ANGLE_CLUSTER_ALERT
- COMPRESSION_CLUSTER
- DENSITY_RISE
- PRE_RELEASE_COMPRESSION

Sous-catégories :

- Temporelle
- Gravitationnelle
- Orchestrale
- Élastique
- Structurelle

---

### 3. RELEASE

Libération, rupture, accélération, séquence qui sort d’un état compressé ou d’un champ retenu.

Événements associés :

- RUPTURE
- CASCADE_BUILDING
- SEQUENCE_VELOCITY_HIGH
- RELEASE
- COUNTER_RELEASE
- DETACHMENT_RELEASE
- CASCADE_RELEASE
- EXPANSION
- BREAKOUT_FLOW
- IMPULSE_RELEASE

Sous-catégories :

- Libération
- Rupture
- Accélération
- Cascade
- Expansion

---

### 4. ABSORPTION

Rejet, contre-souffle, pullback absorbé, tentative inverse contenue, force adverse digérée.

Événements associés :

- LEAKING
- PULLBACK_ABSORBED
- PULLURES_ABSORBED
- COUNTER_BREATH
- ABSORPTION
- REJECTION_ABSORBED
- COUNTER_FORCE_DIGESTED
- FAILED_PULLBACK
- SUPPLY_ABSORBED
- DEMAND_ABSORBED

Sous-catégories :

- Pré-rejet
- Pullback absorbé
- Contre-souffle
- Digestion de force adverse
- Absorption locale

---

### 5. TENSION

Accumulation de force, état pré-extrême, élastique chargé, tension non encore libérée.

Événements associés :

- ACCUMULATING
- PRE_EXTREME
- ELASTIC_TENSION_SCORE
- ELASTIC_TENSION_HIGH
- NODE_HEAT_ENERGY_DIVERGENCE
- TENSION_RISE
- PRESSURE_BUILDUP
- HOT_NODE
- NODE_HEAT
- LATENT_FORCE

Sous-catégories :

- Élastique chargé
- Pré-extrême
- Chaleur de node
- Pression latente
- Divergence énergie / structure

Règle numérique :

```text
ELASTIC_TENSION_SCORE > seuil
```

Le seuil dépend du module appelant. L’ontologie nomme le comportement, elle ne fixe pas le seuil moteur global.

---

### 6. ROTATION

Changement de régime, drift relationnel, bascule de distribution, passage divergent vers synchro ou inversement.

Événements associés :

- REGIME_TRANSITION
- SPEARMAN_DRIFT
- DIVERGENT_EXTREME_TO_SYNCHRO
- DIVERGENT_EXTREME
- SYNCHRO
- ROTATION
- STATE_ROTATION
- CORRELATION_DRIFT
- GRAVITY_ROTATION
- REGIME_SHIFT

Sous-catégories :

- Transition de régime
- Drift relationnel
- Rotation gravitationnelle
- Synchro / désynchro
- Bascule de distribution

---

### 7. STRUCTURE

Organisation relative du champ : leader/follower, coalition, antagonisme, résonance fractale, architecture du flux.

Événements associés :

- LEADER
- FOLLOWER
- LEADER_FOLLOWER
- COALITION
- ANTAGONISTE
- ANTAGONIST
- FRACTAL_RESONANCE
- STRUCTURE
- RELATIVE_FORCE_FIELD
- CROSS_SYMBOL_DRIVER
- USD_WEAKNESS_DOMINANT
- GBP_STRENGTH_GENUINE
- EUR_DIVERGENT
- JPY_SAFE_HAVEN

Sous-catégories :

- Leader / follower
- Coalition
- Antagonisme
- Résonance fractale
- Driver cross-symbol
- Structure relative

---

## Mapping événements → catégories

| Événement | Catégorie | Sous-catégorie |
|-----------|-----------|----------------|
| FIRST_DETACHMENT_MICRO | INFLEXION | Naissance |
| FIRST_DETACHMENT_WITH_CLEAN_RELAY | INFLEXION | Premier détachement |
| KINEMATIC_SHIFT | INFLEXION | Changement cinématique |
| COUNTER_RELEASE_ATTEMPT | INFLEXION | Tentative contre-relâchement |
| COUNTER_RELEASE_ATTEMPT_ALERT | INFLEXION | Tentative contre-relâchement |
| CYCLE_COMPRESSING | COMPRESSION | Temporelle |
| ELASTIC_LOADED | COMPRESSION | Élastique |
| ORCHESTRAL_COMPRESSION | COMPRESSION | Orchestrale |
| REGIME_COMPRESSION | COMPRESSION | Régime |
| TIGHT_GRAVITY_CLUSTER_ALERT | COMPRESSION | Gravitationnelle |
| SAME_ANGLE_CLUSTER_ALERT | COMPRESSION | Structurelle |
| RUPTURE | RELEASE | Libération |
| CASCADE_BUILDING | RELEASE | Cascade |
| SEQUENCE_VELOCITY_HIGH | RELEASE | Accélération |
| RELEASE | RELEASE | Libération |
| LEAKING | ABSORPTION | Pré-rejet |
| PULLBACK_ABSORBED | ABSORPTION | Pullback absorbé |
| PULLURES_ABSORBED | ABSORPTION | Pullures absorbées |
| COUNTER_BREATH | ABSORPTION | Contre-souffle |
| ACCUMULATING | TENSION | Accumulation |
| PRE_EXTREME | TENSION | Pré-extrême |
| ELASTIC_TENSION_SCORE | TENSION | Score tension |
| NODE_HEAT_ENERGY_DIVERGENCE | TENSION | Chaleur node / énergie |
| REGIME_TRANSITION | ROTATION | Transition |
| SPEARMAN_DRIFT | ROTATION | Drift relationnel |
| DIVERGENT_EXTREME_TO_SYNCHRO | ROTATION | Synchro naissante |
| LEADER | STRUCTURE | Leader |
| FOLLOWER | STRUCTURE | Follower |
| COALITION | STRUCTURE | Coalition |
| ANTAGONISTE | STRUCTURE | Antagonisme |
| FRACTAL_RESONANCE | STRUCTURE | Résonance fractale |
| USD_WEAKNESS_DOMINANT | STRUCTURE | Driver cross-symbol |
| GBP_STRENGTH_GENUINE | STRUCTURE | Driver cross-symbol |
| EUR_DIVERGENT | STRUCTURE | Driver cross-symbol |
| JPY_SAFE_HAVEN | STRUCTURE | Driver cross-symbol |

---

## Règles d’interprétation

### Couverture ontologique

Une alerte est considérée couverte si au moins un champ significatif contient un événement ou un alias connu.

Champs typiques :

```text
type
event
alert
alert_type
name
label
status
state
category
message
description
reason
tags
signals
```

### Multi-catégorie

Une alerte peut contenir plusieurs signatures.
V0 choisit la première catégorie par priorité d’ontologie.

Ordre V0 :

```text
INFLEXION
COMPRESSION
RELEASE
ABSORPTION
TENSION
ROTATION
STRUCTURE
```

### Non-classé

Une alerte non-classée n’est pas rejetée.
Elle signale seulement :

```text
ONTOLOGY_UNMAPPED_ALERT
```

C’est une invitation à enrichir l’ontologie, pas un échec moteur.

---

## Contraintes

- Pas de BUY/SELL.
- Pas de décision de trade.
- Pas de DB write.
- L’ontologie nomme le flux, elle ne décide pas.
- Le trader arbitre.
