# CHECKPOINT_LATEST — POWERFLOW V6

Date : 2026-05-06
Statut : dernier point officiel

## Dernier état officiel

Le dernier état officiel n'est plus Node V0.7.1.

```text
Node V0.7.1 validé
Node V0.7.2 validé
Node V0.7.3 validé
Node V0.8-B validé runtime
Node V0.8.1 validé runtime
Currency Energy V0.1 validée en observation live
```

## Briques actives

```text
capture_quality actif
freshness relative active
relay_quality actif
M5 missing / thin / clean actif
session_transition actif
Daily Open Transition prêt
telegram_gating qualifié
kinematics_state actif
release_state typé actif
Currency Energy V0.1 standalone active
```

## Règles majeures

```text
NODE ≠ CROSS
NODE = fenêtre d’énergie
M1 allume
M5 relaie
M15 porte
HTF donne le poids
```

```text
Pas de first_detachment = pas de release confirmée.
Relay clean seul ne suffit pas.
COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED.
```

```text
NODE_HEAT ≠ CURRENCY_ENERGY.
FIRST_DETACHMENT ≠ DOMINANT_CURRENCY_ENERGY.
Kinematics Node ≠ Currency Energy Ranking.
```

## Nouveau fil IA — correction obligatoire

Si un nouveau fil s'arrête à Node V0.7.1, il est obsolète.

Bloc à lui donner :

```text
Tu t’es arrêté à Node V0.7.1.
État réel :
V0.7.2 relay_quality validé.
V0.7.3 session_transition validé.
V0.8-B kinematics_state validé.
V0.8.1 release_state typé validé.
Currency Energy V0.1 validée en observation live.
```

## Prochaine action

```text
P0 — Mettre à jour mémoire officielle
P1 — Analyser une séquence DB avec les briques actuelles
P2 — Définir alertes comportementales spécifiques
P3 — Patch minimal dashboard / alert_queue
```
