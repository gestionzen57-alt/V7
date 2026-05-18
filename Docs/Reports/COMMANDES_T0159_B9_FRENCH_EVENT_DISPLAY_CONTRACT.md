# Commandes T0159

## Tests

```powershell
python -m py_compile pf_b9_french_event_display_contract.py tools\build_t0159_b9_french_event_display_contract.py
python -m pytest tests\test_t0159_b9_french_event_display_contract.py
```

## CLI

```powershell
python tools\build_t0159_b9_french_event_display_contract.py --extra-events-json samples\b9_french_event_display_contract_v0\sample_extra_events.json --output-dir outputs\b9_french_event_display_contract_v0 --print-json
```
