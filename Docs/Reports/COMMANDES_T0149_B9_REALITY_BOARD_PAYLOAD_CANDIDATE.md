# Commandes T0149 — B9 Reality Board Payload Candidate V0

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0149_b9_reality_board_payload_candidate.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0149_b9_reality_board_payload_candidate.ps1"
```

## CLI sample

```powershell
python tools\build_t0149_b9_reality_board_payload_candidate.py --live-brief-json samples\b9_reality_board_payload_candidate_v0\sample_b9_live_brief_once_ready.json --output-dir outputs\b9_reality_board_payload_candidate_v0
```

## CLI runtime

```powershell
python tools\build_t0149_b9_reality_board_payload_candidate.py --live-brief-json outputs\b9_live_brief_once_runner_v0\B9_LIVE_BRIEF_ONCE_V0.json --output-dir outputs\b9_reality_board_payload_candidate_v0
```
