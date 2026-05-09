# MISSION — P1.2 RELATIONAL GRAVITY BRIDGE GUARD

Date : 2026-05-07  
Fichier cible unique : `pf_relational_gravity_bridge.py`

---

# Objectif

Empêcher qu’un champ `RELATIONAL_GRAVITY_MIXED` soit raconté comme un leader clair.

---

# Diagnostic runtime

Le cockpit contient :

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
USD apparaît comme leader dominant ET dans dominant_antagonist.
Champ MIXED ≠ leader unique fiable.
```

---

# Patch demandé

Dans `pf_relational_gravity_bridge.py` :

1. Si `cross_tf_state = RELATIONAL_GRAVITY_MIXED` :

```text
dominant_leader = MIXED
leader_consistency = CONFLICT
topline_reliable = false
summary mentionne leader conflict / mixed field
```

2. Ne jamais laisser `dominant_leader` apparaître dans `dominant_antagonist`.

3. Ajouter :

```text
direction_consistency
leader_consistency
antagonist_consistency
topline_reliable
```

4. Garder `tf_details` intacts.

---

# Interdits

```text
ne pas modifier pf_relational_gravity_probe.py
ne pas modifier cockpit_agentic_state_v01.py sauf nécessité minimale
ne pas lire DB
ne pas patcher dashboard
ne pas brancher Telegram
ne pas refactor global
```

---

# Tests

```powershell
python -m py_compile .\pf_relational_gravity_bridge.py
python -m py_compile .\cockpit_agentic_state_v01.py

python .\run_cockpit_agentic_state_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-06T08:00:00 --end 2026-05-06T13:30:00 --visual-htf-story confirmed --behavioral-queue output\behavioral_alert_queue.json --out output\cockpit_agentic_state_v01.json --pretty

$json = Get-Content .\output\cockpit_agentic_state_v01.json -Raw | ConvertFrom-Json
$json.relational_gravity | ConvertTo-Json -Depth 10
```

---

# Critères de succès

```text
cross_tf_state reste RELATIONAL_GRAVITY_MIXED
dominant_leader = MIXED ou leader_consistency = CONFLICT
topline_reliable = false
dominant_antagonist ne contient pas le leader
tf_details restent inchangés
```
