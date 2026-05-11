# DASHBOARD HYDRATION RUNNER GUIDE — PowerFlow V7.2

## 1. Rôle

`run_dashboard_hydrate_outputs.ps1` orchestre l’hydratation des sorties nécessaires au cockpit V7.2, puis relance :

```powershell
run_dashboard_live_stack.ps1 -Normalize -Validate -Doctor
```

Il ne modifie pas les `pf_*` et n’écrit jamais dans `powerflow.db`.

## 2. Ordre des 16 runners

```text
1  B1 Legacy Regime
2  B1+ HMM Regime
3  B3 Force Kinematics
4  P1 Currency Energy
5  B4 Temporal Density
6  B4+ Wavelet Density
7  B5 Spearman Gravity
8  B7 Fractal Resonance
9  B7+ Volatility Texture
10 B2 Cascade
11 Guard Entropy
12 Session Overlay
13 Data Quality LTF
14 B6 Memory
15 P2 Behavioral Mapper
16 Temporal Node State
```

## 3. Contrats CLI normalisés

```text
B3 Force Kinematics:
  --db powerflow.db --symbol GBPUSD --start <utc> --end <utc> --timeframes 1,5,15 --out output\force_kinematics_state.json --json

B4+ Wavelet:
  --db powerflow.db --symbol GBPUSD

B7 Fractal:
  --db powerflow.db --symbol GBPUSD

B7+ Texture:
  --db powerflow.db --symbol GBPUSD

B6 Memory:
  --queue output\behavioral_alert_queue.json --limit 50

P2 Mapper:
  --temporal output\temporal_density_state.json
```

## 4. Queue alertes

La queue est normalisée avant et après P2 :

```json
{
  "behavioral_alert_queue": [],
  "alerts": [],
  "items": [],
  "queue": []
}
```

Cela permet à Entropy et Session Overlay de lire une forme acceptée.

## 5. Extension avec nouveaux runners

Ajouter un runner via :

```powershell
Run-Step "Nom" "runner.py" @("--arg", "value")
```

Règles :
- Ne pas casser le pipeline si le runner fail.
- Laisser `StopOnError` disponible pour debug strict.
- Écrire les outputs sous `output/`.
- Ne pas écrire DB.

## 6. Troubleshooting

```powershell
.\run_hydration_failure_doctor.ps1 -CorePath .
```

Classifications possibles :
- CLI_SIGNATURE_MISMATCH
- DB_SCHEMA_OR_ACCESS
- PYTHON_IMPORT_DEPENDENCY
- RUNTIME_SCHEMA_DRIFT
- RUNNER_RUNTIME_ERROR
