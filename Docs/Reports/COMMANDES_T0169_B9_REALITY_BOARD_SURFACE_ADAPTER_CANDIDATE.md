# Commandes T0169 — B9 Reality Board Surface Adapter Candidate V0

## Tests

```powershell
python -m py_compile pf_t009_reality_board_surface_adapter_candidate.py tools\build_t0169_b9_reality_board_surface_adapter_candidate.py
python -m pytest tests\test_t0169_b9_reality_board_surface_adapter_candidate.py
```

## CLI runtime

```powershell
python tools\build_t0169_b9_reality_board_surface_adapter_candidate.py --read-model-json outputs\b9_reality_board_read_model_v01\B9_REALITY_BOARD_READ_MODEL_V01.json --panel-json outputs\b9_reality_board_scene_panel_candidate_v01\B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json --payload-json outputs\b9_reality_board_integration_candidate_v0\B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json --display-contract-json outputs\b9_french_event_display_contract_v0\B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json --output-dir outputs\b9_reality_board_surface_adapter_candidate_v0 --print-json
```
