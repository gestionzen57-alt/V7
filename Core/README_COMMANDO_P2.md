# README — COMMANDO P2 M1 Noise + USDJPY Audit + Dashboard M1 Context

## Mission

Fermer les trois priorités logiques :

1. Produire `noise_ratio` pour passer M1_CONTEXT_SCORE de `IGNITION_NOISY` vers `IGNITION_CLEAN` quand le bruit est réellement faible.
2. Auditer USDJPY capture/data freshness.
3. Préparer une card dashboard `M1_CONTEXT_SCORE`.

## Fichiers

```text
pf_m1_noise_ratio_probe.py
run_m1_noise_ratio_once.py
run_usdjpy_capture_diagnostic_once.py
dashboard_m1_context_card_patch.html
dashboard_inject_m1_context_card.py
test_commando_p2_pipeline.py
install_commando_p2.ps1
```

## Pipeline

```powershell
python run_m1_noise_ratio_once.py --db powerflow.db --symbol GBPUSD --output output/force_kinematics_state.json --pretty

python run_m1_context_score_once.py --db powerflow.db --symbol GBPUSD --output output/m1_context_score.json --pretty

python dashboard_normalize_m1_context.py --input output/m1_context_score.json --output output/dashboard_surface/m1_context_score.json --pretty

python run_usdjpy_capture_diagnostic_once.py --db powerflow.db --symbol USDJPY --pretty
```

## Installation

Sans injection dashboard :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_commando_p2.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -Symbol GBPUSD
```

Avec injection dashboard :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_commando_p2.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -Symbol GBPUSD -InjectDashboard
```

Avec commit/push :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_commando_p2.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -Symbol GBPUSD -InjectDashboard -CommitPush
```

## Subtilité

`noise_ratio` ne censure pas M1. Il qualifie la fenêtre.

```text
HIGH + IGNITION_NOISY = M1 exploitable, bruit non confirmé propre
HIGH + IGNITION_CLEAN = M1 exploitable, bruit faible confirmé
```
