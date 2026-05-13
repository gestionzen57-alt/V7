# PATCH LEXIQUE / GRAMMAIRE POWERFLOW V7.6 — Alert Gate & Perception Spine

Date : 20260513

Ce patch ajoute la grammaire officielle introduite pendant la session V7.6.

---

## 1. Concepts ajoutés

### LEGACY_BEHAVIORAL_BUS

Bus JSONL qui transforme les détecteurs legacy rapides en preuves V7.

```text
legacy fast detector → legacy_behavioral_events.jsonl
```

But : récupérer la vitesse du legacy sans lui laisser décider.

---

### TEMPORAL_COMPRESSION_BRIDGE

Pont entre le legacy TIME-COMP et la couche TEMPORAL V7.

Écrit :

```text
legacy_timecomp_events.jsonl
time_compression_state.json
```

Rôle : détecter lock, break, release, acceptance temporelle.

---

### PERCEPTION_SPINE

Colonne de lecture qui agrège les couches disponibles :

```text
TEMPORAL
LEGACY_BEHAVIORAL
ENERGY
TACTICAL
ZONE_REACTION
```

Elle produit un film, pas une décision.

---

### TRADER_ATTENTION_PACKET

Compression de la Spine en message trader court.

Objectif : être lisible en 2 secondes.

Format :

```text
<SYMBOL> | <ATTENTION> | <FILM>
bias=<BIAS> score=<SCORE> next_wake=<NEXT_WAKE>
phrase organique
watch=<WATCH_LIST>
conflict=<CONFLICT>
```

---

### TRADER_ATTENTION_ALERT_GATE

Porte d’alerte finale.

Elle ne répète pas le packet à chaque refresh.  
Elle alerte seulement sur changement pertinent.

Critères :

```text
premier état pertinent
film changé
release détectée
next_wake changé
score jump
loading très dense
cooldown expiré
```

---

## 2. Films ajoutés

### MULTI_TF_ELASTIC_LOADING

Définition :

```text
Élastique multi-timeframe chargé.
Compression visible.
Pas encore de release validée.
```

Réveils associés :

```text
TIME_COMP_BREAK
COMPRESSION_BREAK
KISS_REJECT
SLINGSHOT
```

Message trader :

```text
Élastique multi-TF chargé — attendre détachement ou répulsion.
```

---

### ELASTIC_RELEASE_LEGACY

Définition :

```text
Le legacy détecte un premier relâchement.
La release est vue, mais l’acceptation post-release n’est pas encore validée.
```

Réveils associés :

```text
LOCK_ACCEPTANCE_AFTER_RELEASE
SECOND_LEG
COUNTER_BREATH
ZONE_REJECTION
```

Message trader :

```text
Élastique legacy relâché — attendre acceptation, second leg ou rejet de zone.
```

---

### FIRST_RELEASE_NOT_YET_ACCEPTED

Définition :

```text
Une première release existe, mais le marché n’a pas encore montré l’acceptation, le second leg ou le rejet.
```

Nature :

```text
conflit / état transitoire
```

---

### MULTI_TF_COMPRESSION_WITHOUT_RELEASE

Définition :

```text
Compression multi-TF forte, mais pas de release détectée.
```

Transition attendue :

```text
TIME_COMP_BREAK
COMPRESSION_BREAK
KISS_REJECT
SLINGSHOT
```

---

## 3. Rôles d’événements

```text
TEMPORAL_LOCK
TEMPORAL_BREAK
ELASTIC_LOADING_LEGACY
ELASTIC_RELEASE_LEGACY
ZONE_PRESSURE_LOW
ZONE_PRESSURE_HIGH
CROSS_OR_REJECT_IMMINENT
TACTICAL_REARM_RELEASE
ZONE_REPULSION
PRESSURE_SQUEEZE
TRAP_OR_REINTEGRATION
FORCE_SWITCH
MULTI_TF_CONVERGENCE
DOMINANCE_CROSS
```

---

## 4. Next Wake officiels

```text
TIME_COMP_BREAK
COMPRESSION_BREAK
LOCK_ACCEPTANCE_AFTER_RELEASE
SECOND_LEG
COUNTER_BREATH
ZONE_REJECTION
KISS_REJECT
SLINGSHOT
FIRST_DETACHMENT
NEW_TEMPORAL_LOCK
```

---

## 5. Attention levels

### OBSERVE

```text
Film visible, mais pas assez transformateur.
```

### WATCH

```text
Film actif.
Le trader peut se préparer, mais le réveil fort n’est pas encore là.
```

### WAKE_TRADER

```text
Événement pertinent.
La machine réveille l’attention.
```

### WAKE_TRADER_WITH_TECH_RISK

```text
Événement pertinent, mais un risque technique doit être connu.
Exemples : TIME_SYNC, TEMPORAL_GAPS, COUNTERFLOW.
```

---

## 6. Risques techniques officiels

### EVENT_TIME_AHEAD_OF_DETECTED_AT

```text
event_at est plus récent que detected_at.
Probable offset broker / UTC mal interprété.
```

### EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE

```text
Le flux LTF et MTF ne racontent pas le même sens.
```

### *_TEMPORAL_GAPS

```text
Certaines preuves temporelles manquent pour le symbole.
```

### B8_INSUFFICIENT_CROSS_PAIR_COVERAGE

```text
La couverture inter-paires est insuffisante pour la gravité relationnelle.
```

### TIME_SYNC

Abréviation UI pour :

```text
EVENT_TIME_AHEAD_OF_DETECTED_AT
```

### GAP

Abréviation UI pour :

```text
*_TEMPORAL_GAPS
```

### CFLOW

Abréviation UI pour :

```text
EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE
```

---

## 7. Doctrine d’alerte

```text
Une alerte PowerFlow n’est pas une décision.
Une alerte est une perception transmise.
```

Règles :

```text
Ne pas alerter à chaque tick.
Ne pas alerter à chaque refresh.
Alerter sur transition pertinente.
Dédupliquer par fingerprint.
Qualifier les risques techniques.
Ne pas censurer une alerte précoce.
```

Fingerprint Alert Gate :

```text
symbol + film + next_wake + bias + conflict
```

---

## 8. Grammaire terminal

### Table scanner

```text
SYMBOL  ATTN  FILM             BIAS       NEXT             SCORE  RISK
GBPUSD  WAKE  ELASTIC_RELEASE  MIXED      LOCK_ACCEPTANCE  86.6   TIME,GAP
```

### Packet compact

```text
GBPUSD | WAKE_TRADER_WITH_TECH_RISK | ELASTIC_RELEASE_LEGACY
bias=MIXED score=86.57 next_wake=LOCK_ACCEPTANCE_AFTER_RELEASE
Élastique legacy relâché — attendre acceptation, second leg ou rejet de zone.
Réveil suivant : acceptation post-release.
watch=LOCK_ACCEPTANCE_AFTER_RELEASE | SECOND_LEG | COUNTER_BREATH | ZONE_REJECTION
conflict=FIRST_RELEASE_NOT_YET_ACCEPTED
```

---

## 9. Règle d’intégration Telegram

Telegram ne doit pas lire les alertes legacy brutes.  
Telegram doit lire uniquement :

```text
pf_trader_attention_alert_gate_once.py
```

ou ses sorties :

```text
trader_attention_last_alert.txt
trader_attention_alerts.jsonl
```

But :

```text
moins de bruit
plus de pertinence
meilleure lisibilité pendant trading
```
