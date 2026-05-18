# Commandes T0157

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0157_b9_telegram_fr_gate_candidate.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0157_b9_telegram_fr_gate_candidate.ps1"
```

## CLI sample

```powershell
python tools\build_t0157_b9_telegram_fr_gate_candidate.py --reality-board-payload-json samples\b9_telegram_fr_gate_candidate_v0\sample_b9_reality_board_integration_candidate.json --output-dir outputs\b9_telegram_fr_gate_candidate_v0
```

## CLI runtime

```powershell
python tools\build_t0157_b9_telegram_fr_gate_candidate.py --reality-board-payload-json outputs\b9_reality_board_integration_candidate_v0\B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json --output-dir outputs\b9_telegram_fr_gate_candidate_v0
```
