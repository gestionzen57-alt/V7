# B9 Scheduler Window Dict Fix V1.3

Patch final pour le format attendu par `process_tick_window_b9()`.

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_b9_scheduler_window_dict_fix_v1_3.ps1"
```

## Test

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD --continue-on-error
python check_b9_live_nodes.py
```
