# Commandes T0156

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0156_b9_reality_board_integration_candidate.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0156_b9_reality_board_integration_candidate.ps1"
```

## Tests

```powershell
python -m py_compile pf_t009_reality_board_integration_candidate.py tools\build_t0156_b9_reality_board_integration_candidate.py
python -m pytest tests\test_t0156_b9_reality_board_integration_candidate.py
```

## CLI sample

```powershell
python tools\build_t0156_b9_reality_board_integration_candidate.py --attention-packet-json samples\b9_reality_board_integration_candidate_v0\sample_b9_trader_attention_packet.json --output-dir outputs\b9_reality_board_integration_candidate_v0
```

## CLI runtime candidate

```powershell
python tools\build_t0156_b9_reality_board_integration_candidate.py --attention-packet-json outputs\b9_trader_attention_packet_v0\B9_TRADER_ATTENTION_PACKET_V0.json --output-dir outputs\b9_reality_board_integration_candidate_v0
```
