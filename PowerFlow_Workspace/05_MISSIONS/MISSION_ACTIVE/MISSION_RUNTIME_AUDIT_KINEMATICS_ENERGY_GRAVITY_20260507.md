# MISSION — AUDIT RUNTIME KINEMATICS / ENERGY / RELATIONAL GRAVITY

Date : 2026-05-07

---

# Objectif

Tester si Kinematics, Currency Energy et Relational Gravity sont réellement opérationnels sur le Core actuel.

---

# 1. Tester Node / Kinematics

```powershell
python .\run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --visual-htf-story confirmed --out output\temporal_node_state.json --pretty

Select-String -Path .\output\temporal_node_state.json -Pattern "kinematics_state","first_detachment","release_state","energy_release_alignment","capture_quality","relay_quality"
```

À analyser :

```text
node actif ?
relay_quality ?
first_detachment ?
release_state ?
energy_release_alignment ?
```

---

# 2. Tester Currency Energy

```powershell
python .\run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --bars 50 --htf 5,15,30 --out output\currency_energy_state_m1.json --pretty --summary

python .\run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 5 --bars 50 --htf 15,30,60 --out output\currency_energy_state_m5.json --pretty --summary

python .\run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 15 --bars 50 --htf 15,30,60 --out output\currency_energy_state_m15.json --pretty --summary
```

À analyser :

```text
top energy par TF
GBP / USD energy
energy thin / mixed / aligned
support ou divergence avec release_state
```

---

# 3. Tester Relational Gravity

```powershell
python .\run_relational_gravity_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --bars 30 --out output\relational_gravity_m1_v011.json --pretty --summary

python .\run_relational_gravity_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 5 --bars 30 --out output\relational_gravity_m5_v011.json --pretty --summary

python .\run_relational_gravity_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 15 --bars 30 --out output\relational_gravity_m15_v011.json --pretty --summary
```

À analyser :

```text
primary_state
group
direction
leader
antagonist
score
confidence
```

---

# 4. Tester cockpit bridge

```powershell
python .\run_cockpit_agentic_state_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-06T08:00:00 --end 2026-05-06T13:30:00 --visual-htf-story confirmed --behavioral-queue output\behavioral_alert_queue.json --out output\cockpit_agentic_state_v01.json --pretty

Select-String -Path .\output\cockpit_agentic_state_v01.json -Pattern "relational_gravity","RELATIONAL_GRAVITY","dominant_leader","cross_tf_state"
```

Puis :

```powershell
$json = Get-Content .\output\cockpit_agentic_state_v01.json -Raw | ConvertFrom-Json
$json.relational_gravity | ConvertTo-Json -Depth 10
```

---

# 5. Sortie attendue

```text
GO/NO GO Kinematics
GO/NO GO Energy
GO/NO GO Relational Gravity Probe
GO/NO GO Relational Gravity Cockpit
P1.2 nécessaire ? oui/non
P2 autorisé ? oui/non
risques restants
next action
```
