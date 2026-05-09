# 02 — LEXIQUE / GRAMMAIRE ACTIVE POWERFLOW V6

Date : 2026-05-05  
Statut : GRAMMAIRE ACTIVE — version nettoyée

## Principe

```text
Nommer pour voir.
Pas nommer pour classer inutilement.
```

Une nomenclature doit réduire la charge mentale.

## Cycle de travail

```text
VISION NOTE
→ FLOW BEHAVIOR
→ FLOW EVENT
→ FLOW WINDOW
→ SYSTEM ACTION
```

## Familles

```text
VISION
FORCE
ZONE
NODE
TEMPORAL
FRACTAL
COALITION
BATTLEFIELD
COCKPIT
TELEGRAM
LAB
SYSTEM
```

## Force / tension

### FORCE_SHIFT
Changement d’angle ou de régime d’une devise.

### TENSION_FIELD
Champ de tension actif.

### ELASTIC_LOADED
Élastique chargé.

```text
tension maintenue
pullbacks absorbés
champ prêt à libérer ou casser
```

### PRICE_LAG_THEN_CATCHUP
Le prix est en retard sur la force puis rattrape.

### SPREAD_FRICTION_FIELD
Le spread crée une friction ou une rugosité de lecture.

## Zone

```text
NEUTRAL
PRE_EXTREME
EARLY_EXTREME
ACCUMULATING
LEAKING
RUPTURE
PULLBACK
ABSORBED_PULLBACK
```

## Nodes

Un node n’est pas seulement un croisement.

Il peut être contact, non-contact, étirement, opposition, pli, compression, répulsion, synchronisation, bascule de leadership.

```text
NODE
NODE_BIRTH
FAST_NODE_BIRTH
NODE_WATCH
NODE_CONFIRMED
NODE_REPULSION
NODE_ABSORPTION
SECOND_LEG_NODE
LATE_NODE
```

## Temporal

```text
TEMPORAL_NODE_ALERT
TEMPORAL_WINDOW_CANDIDATE
TEMPORAL_WINDOW_ACTIVE
TEMPORAL_DENSITY
```

Règle :

```text
Temporal Node Alert ≠ TemporalWindowActive.
```

## Fractal

```text
LTF = M1 / M5 / M15
HTF = M30 / H1 / H4
LTF_BIRTH_ACTIVE
HTF_GRAVITY_SUPPORTIVE
HTF_GRAVITY_OPPOSED
HTF_CONFIRMED_BUT_LTF_LATE
```

Règle :

```text
HTF confirmé + LTF tardif = pas NODE_BIRTH.
Chercher absorption, second leg ou clôture.
```

## Flow Events

```text
FAST_BIRTH_ALERT
NODE_BIRTH
COUNTER_BREATH
ABSORPTION
WATCH_SECOND_LEG
VOLUME_PRESSURE_SPIKE
PRICE_LAG_THEN_CATCHUP
SPREAD_FRICTION_FIELD
```

Signature minimale FAST_BIRTH_ALERT :

```text
M1 force shift
angle change
price lag
devise antagoniste active
spread non destructeur
pip_range ou volume en expansion si disponible
```

## Coalitions / Battlefield

```text
COALITION_FIELD
ANTAGONIST_FIELD
BATTLEFIELD_RADAR
BIPOLAR_FIELD
```

Règle :

```text
Coalition forte seule ≠ bataille complète.
Relation active moyenne > coalition isolée forte.
```

## Cockpit / Telegram

```text
COCKPIT_STATE
NODE_STATE
ALERT_LEVELS
TELEGRAM_NODE_MODE
```

Alert levels :

```text
BIRTH
WATCH
HOT
CONFIRMING
ABSORBING
SECOND_LEG
LATE
CHAOTIC
```

Telegram modes :

```text
OFF
WATCH
SCALPING
HOT_ONLY
```

Règle :

```text
Le filtre Telegram appartient au trader.
```

## Labs

États :

```text
VISION NOTE
À TESTER
À PATCHER
À CONSOLIDER
LEGACY
```

Format fiche :

```text
ID :
VISION NOTE :
FLOW BEHAVIOR :
FLOW EVENT :
FLOW WINDOW :
SYSTEM ACTION :
DB TESTABLE :
ALERTE UTILE :
STATUT :
```
