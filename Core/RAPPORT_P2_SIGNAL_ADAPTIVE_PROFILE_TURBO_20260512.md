# RAPPORT P2 — SIGNAL_ADAPTIVE_PROFILE TURBO  
PowerFlow V7.2.1 — 2026-05-12

## Objectif

Transformer le test local USDJPY en brique officielle, paramétrique et multi-symbol.

## Résultat livré

```text
pf_signal_adaptive_profile.py
run_signal_adaptive_profile_once.py
run_signal_adaptive_all_once.py
dashboard_normalize_signal_adaptive.py
dashboard_signal_adaptive_card_patch.html
dashboard_inject_signal_adaptive_card.py
scheduler_powerflow_turbo_wrapper.py
setup_windows_task_scheduler_turbo.ps1
```

## Amélioration apportée

Avant :

```text
script local hardcodé USDJPY
```

Après :

```text
module paramétrique
multi-symbol
dashboard-ready
scheduler-ready
read-only
```

## Modes

```text
FULL_STACK_SIGNAL_READY
M1_TACTICAL_THIN_HTF
M1_ONLY_NO_RELAY
DATA_NOT_READY
```

## Doctrine

```text
M1 jamais censuré.
HTF thin qualifie, ne bloque pas.
Signal permission = état de perception, pas ordre.
```

## Intégration turbo

Le wrapper turbo ajoute au cycle :

```text
data health monitor
flow ontology cycle
signal adaptive profile
dashboard normalizers
```

## Risques techniques

```text
DATA_HEALTH doit être rafraîchi avant le profil.
EURUSD peut rester DATA_STALE tant que la capture n’est pas rétablie.
USDJPY reste M1 vivant / HTF thin tant que l’historique HTF n’est pas construit.
```

## Conclusion

La chaîne devient :

```text
capture -> data health -> scheduler -> ontology -> signal adaptive -> dashboard
```
