# CURRENT_STATE — POWERFLOW V6 ACTIVE

Date : 2026-05-06
Statut : vérité courte active

## Nature

PowerFlow V6 est un moteur de perception du flux Forex.
Ce n'est pas une nounou, pas un robot BUY/SELL, pas une tour de contrôle.

Règle centrale :

```text
La machine perçoit.
La machine mesure.
La machine nomme.
La machine alerte.
Le trader filtre.
Le trader décide.
```

## Doctrine active

```text
M1 = microfilm / ignition / naissance
M5 = relais tactique
M15 = source / fenêtre courte
M30-H1 = gravité
H4+ = poids supérieur
```

```text
NODE ≠ CROSS
CROSS = manifestation possible
NODE = fenêtre d’énergie / partition des forces
```

## État moteur validé

```text
Node V0.7.1 = VALIDÉ
capture_quality / freshness relative / telegram_gating / M5_RELAY_MISSING_IN_DB

Node V0.7.2 = VALIDÉ
relay_quality / M5_RELAY_MISSING_IN_DB / M5_RELAY_THIN_SAMPLE / M5_RELAY_CLEAN

Node V0.7.3 = VALIDÉ
session_transition / DAILY_OPEN_TRANSITION / M5_RELAY_CLEAN maintient HOT_READY

Node V0.8-B = VALIDÉ RUNTIME
kinematics_state / angle_state / speed_state / acceleration_state / first_detachment

Node V0.8.1 = VALIDÉ RUNTIME
release_state typé / RELEASE_ATTEMPT / RELEASE_CANDIDATE / RELEASE_CONFIRMED / COUNTER_RELEASE_ATTEMPT / FAKE_RELEASE / RELEASE_REJECTED

Currency Energy V0.1 = VALIDÉE EN OBSERVATION LIVE
standalone / non branchée Node State
```

## Règles validées

```text
Pas de first_detachment = pas de release confirmée.
Relay clean seul ne suffit pas.
COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED.
Energy ≠ Direction.
Energy ≠ Signal.
NODE_HEAT ≠ CURRENCY_ENERGY.
FIRST_DETACHMENT ≠ DOMINANT_CURRENCY_ENERGY.
Kinematics Node ≠ Currency Energy Ranking.
```

## Problème dashboard actuel

Le dashboard affiche encore trop générique :

```text
RAW_NODE_BIRTH
LTF_BIRTH_INSIDE_VISUAL_HTF_STORY
WATCH_M5_CONFIRMATION
```

Il doit évoluer vers :

```text
capture_quality
relay_quality
kinematics_state
release_state
currency_energy
behavioral_alerts
next_watch enrichi
film de séquence
```

## Priorité actuelle

```text
P0 — Mémoire officielle / lexique / checkpoint latest
P1 — Analyse de séquence DB avec briques actuelles
P2 — Behavioral Alert Agent
P3 — Dashboard Sync Agent
P4 — Currency Energy V0.2 calibration
P5 — Density Context V0.9
P6 — Energy Context → Node State seulement après calibration
```

Phrase de reprise :

```text
Ne pas tout brancher parce que tout marche.
Consolider ce qui est vrai.
Observer ce qui est nouveau.
Intégrer seulement ce qui augmente la perception.
```
