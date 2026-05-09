# 07 — SPEC TEMPORAL_NODE_ALERT_STATE

Date : 2026-05-05  
Statut : SPEC P0 — brique urgente

---

# 1. Problème

Le core contient déjà une famille Temporal / Nodes :

```text
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
pf_temporal_density.py
pf_temporal_patterns.py
pf_temporal_patterns_cockpit.py
telegram_agentic_nodes_v01.py
```

Mais il manque une sortie simple, stable, lisible :

```text
output/temporal_node_state.json
```

---

# 2. Mission

Créer ou stabiliser une brique :

```text
pf_temporal_node_state.py
```

Mission :

```text
lire les sources existantes
qualifier les nodes
produire un state JSON read-only
préparer cockpit / Telegram
ne pas écrire en DB
ne pas dépendre du dashboard
```

---

# 3. Inputs possibles

```text
powerflow.db
force_snapshots / force_snapshots_v2
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
pf_temporal_density.py
pf_temporal_patterns.py
pf_flow_event_extractor_v02_extended.py
pf_fractal_window_engine.py
pf_db_vision_guard.py
```

À confirmer après audit.

---

# 4. Output cible

```text
output/temporal_node_state.json
```

Structure minimale :

```json
{
  "meta": {
    "generated_at": "",
    "symbol": "",
    "window_minutes": 180,
    "source": "pf_temporal_node_state"
  },
  "db_vision": {
    "status": "TACTICAL_OK",
    "notes": []
  },
  "node_summary": {
    "active_count": 0,
    "highest_level": "NONE",
    "dominant_direction": null,
    "telegram_mode": "SCALPING"
  },
  "nodes": [
    {
      "id": "NODE_001",
      "timestamp": "",
      "symbol": "GBPUSD",
      "timeframe": "M1",
      "level": "NODE_BIRTH",
      "family": "TEMPORAL_NODE",
      "direction_bias": "GBP pressure up / USD pressure down",
      "maturity": "BIRTH",
      "confidence": "EARLY",
      "reasons": ["force_shift", "angle_change", "price_lag"],
      "risks_technical": ["early_maturity", "m1_noise"],
      "telegram_allowed": true,
      "telegram_level": "BIRTH"
    }
  ],
  "next_watch": [
    "WATCH_ABSORPTION",
    "WATCH_SECOND_LEG"
  ]
}
```

---

# 5. Levels

```text
NODE_WATCH
NODE_BIRTH
FAST_NODE_BIRTH
NODE_REPULSION_CANDIDATE
NODE_REPULSION
NODE_ABSORPTION
SECOND_LEG_NODE
NODE_CONFIRMED
HOT_NODE
LATE_NODE
```

---

# 6. Telegram modes

```text
OFF
WATCH
SCALPING
HOT_ONLY
```

## WATCH

```text
NODE_WATCH
NODE_BIRTH
NODE_REPULSION_CANDIDATE
```

## SCALPING

```text
FAST_NODE_BIRTH
NODE_BIRTH
NODE_REPULSION
NODE_ABSORPTION
SECOND_LEG_NODE
```

## HOT_ONLY

```text
HOT_NODE
NODE_CONFIRMED
```

---

# 7. Garde-fous techniques

```text
ne pas modifier capture_bridge.py
ne pas écrire dans powerflow.db
ne pas déclencher Telegram directement depuis pf_*
ne pas confondre node alert et TemporalWindowActive
ne pas supprimer les anciens modules avant audit
```

---

# 8. Commande future possible

```powershell
python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --out output/temporal_node_state.json --pretty
```

---

# 9. Critère de réussite

```text
le trader peut voir qu’un node est né
le cockpit peut lire le state
Telegram peut filtrer selon mode
aucune architecture n’est cassée
la sortie réduit la charge mentale
```

Phrase finale :

```text
Les nodes doivent devenir visibles avant d’être parfaits.
```
