# README — M1_CONTEXT_SCORE

## Rôle

`M1_CONTEXT_SCORE` calcule un score d’exploitabilité contextuelle M1.

Doctrine :

```text
M1 jamais censuré.
M1 qualifié.
Le score n’est pas un risque financier.
Le score indique la qualité contextuelle de lecture/intervention du microfilm.
```

## Fichiers

```text
pf_m1_context_score.py
run_m1_context_score_once.py
dashboard_normalize_m1_context.py
install_m1_context.ps1
README_M1_CONTEXT.md
```

## Inputs

Le module lit :

```text
powerflow.db / force_snapshots TF1             read-only
output/force_kinematics_state.json             noise_ratio, first_detachment
output/dashboard_surface/{symbol}/node.json    capture_quality, relay_quality
output/session_overlay.json                    session_phase
output/dashboard_surface/{symbol}/regime_hmm.json
output/dashboard_surface/{symbol}/regime_legacy.json
```

Tous les chemins sont surchargeables depuis le runner.

## Score

Poids :

```text
capture_quality      0.30
noise_ratio_score    0.20
relay_quality        0.20
session_phase_score  0.15
regime_score         0.15
```

Labels :

```text
score >= 0.7  HIGH
0.4–0.7       MEDIUM
< 0.4         LOW
```

## Commandes

```powershell
python run_m1_context_score_once.py --db powerflow.db --symbol GBPUSD --output output/m1_context_score.json --pretty
python dashboard_normalize_m1_context.py --input output/m1_context_score.json --output output/dashboard_surface/m1_context_score.json --pretty
```

Installation :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_m1_context.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -Symbol GBPUSD
```

## Output moteur

```json
{
  "timestamp_utc": "2026-05-11T22:05:00Z",
  "currencies": {
    "GBP": {
      "m1_context_score": 0.82,
      "breakdown": {
        "capture_quality": 0.8,
        "noise_ratio_score": 1.0,
        "relay_quality": 0.6,
        "session_phase_score": 1.0,
        "regime_score": 1.0
      },
      "exploitability": "HIGH",
      "intervention_window": "IGNITION_CLEAN"
    }
  }
}
```

## Output dashboard normalized

```json
{
  "currencies": [
    {
      "currency": "GBP",
      "m1_score": 0.82,
      "exploitability": "HIGH",
      "intervention_window": "IGNITION_CLEAN"
    }
  ]
}
```

## Risques techniques possibles

```text
KINEMATICS_JSON_MISSING
TEMPORAL_NODE_JSON_MISSING
SESSION_OVERLAY_JSON_MISSING
REGIME_JSON_MISSING
NO_TF1_ROWS_FOR_SYMBOL
CAPTURE_QUALITY_MISSING_DEFAULT_MINIMAL
NOISE_RATIO_MISSING_DEFAULT_0_4
RELAY_QUALITY_MISSING_DEFAULT_M5_MISSING
SESSION_PHASE_MISSING_DEFAULT_DEAD_ZONE
REGIME_MISSING_DEFAULT_UNKNOWN
```

Ces risques qualifient la lecture. Ils ne bloquent pas M1.
