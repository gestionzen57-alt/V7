# Commandes T0173

```powershell
python -m py_compile pf_t009_live_chain_runtime_missing_input_resolver.py tools\build_t0173_b9_live_chain_missing_input_resolver.py
python -m pytest tests\test_t0173_b9_live_chain_missing_input_resolver.py
python tools\build_t0173_b9_live_chain_missing_input_resolver.py --core-root . --output-dir outputs\b9_live_chain_missing_input_resolver_v0 --print-json
```
