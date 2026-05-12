# CHECKPOINT V7.3.5b — Trader Cockpit Clarity

## Etat

V7.3.5b rend le cockpit trader plus lisible et moins bruyant.

## Point important

EURUSD / USDJPY ne doivent plus apparaître en `WAKE_TRADER` quand ils sont seulement contexte.
Ils doivent apparaître en `WATCH_CONTEXT`.

## Lecture frontale attendue

```text
ETAT = CONFLIT DAILY/B6 vs LIVE
SURVEILLER = reintegration, echec PAIR_UP, second test, bascule PAIR_DOWN
```

Selon le flux réel, l'état peut aussi devenir :

```text
CONTEXTE BAISSIER PARTIEL
CONTEXTE HAUSSIER PARTIEL
CONFLIT MULTI-LECTURE
SURVEILLANCE CONTEXTE
```

## Commande test

```powershell
python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --output output/dashboard_surface/trader_cockpit.json --txt output/dashboard_surface/trader_cockpit.txt --pretty
```

## URL

```text
http://localhost:8787/dashboard_trader_cockpit.html
```
