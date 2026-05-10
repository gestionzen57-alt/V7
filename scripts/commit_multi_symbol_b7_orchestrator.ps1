# Commit 2 — B7 + orchestrator multi-symbol patch
$ErrorActionPreference = "Stop"
python -m py_compile Core\run_fractal_resonance_once.py Core\run_powerflow_cycle_once.py
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
python -m json.tool .\output\fractal_resonance_GBPUSD.json | Out-Null
python Core\run_powerflow_cycle_once.py --db Core\powerflow.db --symbols GBPUSD,EURUSD,USDJPY,XAUUSD --dry-run --pretty
git add Core\run_fractal_resonance_once.py Core\run_powerflow_cycle_once.py
git commit -m "Multi-Symbol: refactor B7 and orchestrator for symbol parameter"
