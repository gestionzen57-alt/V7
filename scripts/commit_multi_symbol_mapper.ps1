# Commit 1 — mapper + DB helpers + tests
$ErrorActionPreference = "Stop"
python -m py_compile Core\pf_symbol_mapper.py Core\pf_multi_symbol_db.py Core\run_multi_symbol_smoke_tests.py
python Core\run_multi_symbol_smoke_tests.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --tfs 1,5,15 --pretty
python -m json.tool .\output\multi_symbol_smoke_test.json | Out-Null
git add Core\pf_symbol_mapper.py Core\pf_multi_symbol_db.py Core\run_multi_symbol_smoke_tests.py Core\tests\test_pf_symbol_mapper.py
git commit -m "Multi-Symbol: add pf_symbol_mapper universal mapper"
