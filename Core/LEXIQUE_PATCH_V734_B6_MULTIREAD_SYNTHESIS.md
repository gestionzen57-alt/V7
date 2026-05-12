# LEXIQUE PATCH — V7.3.4 B6 MULTIREAD SYNTHESIS

## B6_ORDER_FLOW_PROXY_LITE

Lecture tactique complète du flux récent.

Rôle :

```text
Dire si le flux live confirme, contredit ou nuance Daily / Topdown / Live Brief.
```

## B6_LIVE_FUSION

Sortie B6 par symbole.

Fichiers :

```text
output/dashboard_surface/GBPUSD/b6_live_fusion.json
output/dashboard_surface/GBPUSD/b6_live_fusion.txt
```

## B6_LIVE_FUSION_DASHBOARD

Contrat normalisé B6.

Sortie :

```text
output/dashboard_surface/b6_live_fusion_dashboard.json
```

## MULTIREAD_SYNTHESIS

Synthèse parallèle des lectures :

```text
Daily Journal
Topdown Reader
Live Brief
B6
Signal Adaptive
Data Health
```

## ALIGNMENT

État d'accord entre lectures.

Valeurs possibles :

```text
BULLISH_ALIGNMENT
BEARISH_ALIGNMENT
PARTIAL_BULLISH_ALIGNMENT
PARTIAL_BEARISH_ALIGNMENT
CONFLICT
MIXED_OR_AMBIGUOUS
NO_DIRECTIONAL_ALIGNMENT
```

## WATCH_ATTENTION_CONFLICT

Le système voit un conflit exploitable entre lectures.

Ce n'est pas une décision. C'est une perception à comparer au regard trader.
