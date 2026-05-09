# 06 — ROADMAP POWERFLOW V6 — PRIORITÉS À LEVIER

Date : 2026-05-05  
Statut : ROADMAP MODE TRADER ACTIF

---

# 0. Règle

```text
Le nécessaire d’abord.
Le puissant ensuite.
Le confortable plus tard.
```

---

# P0 — Ne plus perdre le contexte

Utiliser :

```text
04_POWERFLOW_CURRENT_STATE_V3_CORE_20260505.md
05_CORE_INVENTORY_REPORT_INITIAL_20260505.md
```

Levier :

```text
moins de confusion
moins de contradiction IA
plus de vitesse de reprise
```

---

# P0 — Temporal Node Alert State

Créer / stabiliser :

```text
output/temporal_node_state.json
```

via :

```text
pf_temporal_node_state.py
```

ou adaptation read-only de :

```text
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
```

Levier :

```text
nodes visibles
alertes possibles
aucun besoin de casser capture_bridge.py
```

---

# P0 — Telegram Node Policy

Ajouter modes :

```text
OFF
WATCH
SCALPING
HOT_ONLY
```

Levier :

```text
alerte adaptée au trader
pas de censure
pas de spam non contrôlé
```

---

# P1 — Stabiliser Agentic Core

Auditer :

```text
pf_db_vision_guard.py
pf_flow_event_extractor_v02_extended.py
pf_scene_namer.py
pf_fractal_window_engine.py
cockpit_agentic_state_v01.py
telegram_agentic_nodes_v01.py
```

Levier :

```text
chaîne DB → agents → cockpit → Telegram plus fiable
```

---

# P1 — FlowEventExtractor V0.2 Extended

Events prioritaires :

```text
FAST_BIRTH_ALERT
NODE_BIRTH
COUNTER_BREATH
ABSORPTION
WATCH_SECOND_LEG
PRICE_LAG_THEN_CATCHUP
SPREAD_FRICTION_FIELD
```

Levier :

```text
meilleure lecture M1/M5
meilleures alertes scalping
```

---

# P1 — Cockpit State minimal

Créer / stabiliser :

```text
output/cockpit_state_v2.json
```

Structure :

```json
{
  "meta": {},
  "db_vision": {},
  "current_scene": {},
  "temporal_nodes": {},
  "flow_events": [],
  "fractal_context": {},
  "telegram": {},
  "next_watch": {}
}
```

Levier :

```text
une seule vérité lisible par dashboard, Telegram et IA
```

---

# P1 — DBVisionGuard / Freshness

Vérifier :

```text
pf_db_vision_guard.py
run_db_vision_guard_once.py
```

Sorties utiles :

```text
DATA_BLIND
DATA_STALE
TACTICAL_PARTIAL
TACTICAL_OK
HTF_MISSING
FULL_STACK_VISIBLE
```

---

# P2 — Nettoyage core progressif

Après inventaire :

```text
déplacer backups
isoler anciens rapports
marquer legacy
réduire doublons run_*
```

Interdit :

```text
pas de suppression brutale
pas de refactor global
```

---

# P2 — Dashboard V2

Condition :

```text
seulement après state stable
```

---

# P3 — TemporalWindowActive

Condition :

```text
Temporal Node State
TemporalDensity auditée
FlowEvents stables
Fractal context
Telegram policy
```

Règle :

```text
On alerte les nodes avant de déclarer TemporalWindowActive.
```

---

# Synthèse

```text
1. Temporal Node State
2. Telegram Node Policy
3. Agentic Core audit
4. FlowEventExtractor V0.2 consolidation
5. Cockpit State V2 minimal
6. DBVisionGuard vérification
7. Core cleanup progressif
8. Dashboard V2
9. TemporalWindowActive
```

Phrase finale :

```text
Le plus gros levier immédiat :
rendre les Temporal Nodes visibles et alertables.
```
