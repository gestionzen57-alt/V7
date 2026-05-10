# PowerFlow B7 Fractal Resonance commit helper
# Run from repository root.

$ErrorActionPreference = "Stop"

python -m py_compile Core\pf_fractal_resonance.py Core\run_fractal_resonance_once.py
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --pretty
python -m json.tool .\output\fractal_resonance.json | Out-Null

git add Core\pf_fractal_resonance.py Core\run_fractal_resonance_once.py
git commit -m "B7: Fractal Resonance Detection"

git status
