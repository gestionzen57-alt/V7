# CURRENT_STATE — POWERFLOW V6 ORCHESTRATION

Date : 2026-05-07  
Statut : ÉTAT ACTIF À SYNCHRONISER DANS LE WORKSPACE  
Destination recommandée : `PowerFlow_Workspace/00_CURRENT/CURRENT_STATE.md`

---

# 1. Nature active de PowerFlow

PowerFlow V6 est un moteur de perception du flux Forex.

Il n’est pas :
- un bot BUY/SELL ;
- une nounou ;
- une tour de contrôle ;
- un indicateur technique classique ;
- une usine de signaux retardés.

Règle centrale :

```text
La machine perçoit.
La machine mesure.
La machine nomme.
La machine alerte.
Le trader filtre.
Le trader décide.
```

Objectif opérationnel :

```text
Alerter vite sur des comportements précis,
pas afficher des labels génériques.
```

---

# 2. État officiel attendu

```text
Node V0.7.1 — VALIDÉ
capture_quality / relative freshness / telegram_gating

Node V0.7.2 — VALIDÉ
relay_quality / M5 missing-thin-clean

Node V0.7.3 — VALIDÉ
session_transition / DAILY_OPEN_TRANSITION

Node V0.8-B — VALIDÉ
kinematics_state / first_detachment / angle-speed-acceleration

Node V0.8.1 — VALIDÉ
release_state typé

Node V0.8.2 — VALIDÉ
energy_release_alignment

Currency Energy V0.1 — VALIDÉE EN OBSERVATION
probe standalone, non signal

Behavioral Flow Dashboard Live — VALIDÉ
temporal_node_state → behavioral_queue → cockpit → dashboard

Relational Gravity V0.1 — VALIDÉ
probe standalone

Relational Gravity V0.1.1 — VALIDÉ
DIRECTION_MIN_DELTA filtre les devises plates

Relational Gravity P1.1 — VALIDÉ
bloc relational_gravity visible dans cockpit_agentic_state_v01.json

Relational Gravity P1.2 — À FAIRE
Bridge Guard pour éviter qu’un champ MIXED soit raconté comme un leader clair

Relational Gravity P2 — EN ATTENTE
Behavioral Mapper relational alerts après P1.2 seulement
```

---

# 3. État actuel bloquant

Le cockpit contient maintenant `relational_gravity`, mais le dernier runtime a montré :

```text
cross_tf_state = RELATIONAL_GRAVITY_MIXED
dominant_direction = DOWN
dominant_leader = USD
dominant_antagonist = AUD/GBP/USD/CAD
aligned_tfs = [1, 5]
counter_tf = 15
```

Détail :

```text
M1  DOWN | leader USD | score 0.787 | HIGH
M5  DOWN | leader CHF | score 0.556 | MEDIUM
M15 UP   | leader CHF | score 0.871 | HIGH
```

Problème :

```text
USD apparaît comme leader dominant ET dans les antagonistes.
Un champ MIXED ne doit pas produire un leader top-level fiable.
```

Donc :

```text
P1.2 Bridge Guard obligatoire avant P2.
```

---

# 4. Priorité active

```text
P0 — Synchroniser mémoire workspace
P1 — P1.2 Relational Gravity Bridge Guard
P2 — Relancer audit runtime Kinematics / Energy / Gravity
P3 — Autoriser ou bloquer P2 Behavioral Mapper
P4 — Dashboard Sync relationnel seulement après queue stable
P5 — Telegram plus tard
```

---

# 5. Phrase de reprise

```text
Kinematics dit comment ça bouge.
Energy dit si le champ est vivant.
Relational Gravity dit comment les acteurs se tiennent.
Behavioral Flow doit alerter seulement quand ces lectures sont qualifiées.
```
