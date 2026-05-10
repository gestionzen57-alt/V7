param(
    [string]$Db = "Core\powerflow.db",
    [switch]$Commit
)

$ErrorActionPreference = "Stop"

function Step($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
}

Step "PowerFlow V7.2 B1/B4/B6 validation"

$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo
Write-Host "Repo: $repo"

Step "Install/check dependencies"
python -c "import importlib.util, subprocess, sys; needed=[]; [needed.append(pkg) for mod,pkg in [('numpy','numpy'),('pywt','PyWavelets')] if importlib.util.find_spec(mod) is None]; subprocess.check_call([sys.executable,'-m','pip','install',*needed]) if needed else None"

Step "py_compile"
python -m py_compile Core\pf_hmm_regime.py
python -m py_compile Core\run_hmm_regime_once.py
python -m py_compile Core\pf_wavelet_density.py
python -m py_compile Core\run_wavelet_density_once.py
python -m py_compile Core\pf_memory_engine.py
python -m py_compile Core\run_memory_query_once.py

Step "Run B1 HMM train + predict"
python Core\run_hmm_regime_once.py --db $Db --train --predict --model output\hmm.pkl --output output\hmm_regime_result.json --pretty
python -m json.tool output\hmm_regime_result.json | Out-Null

Step "Run B4 Wavelet"
python Core\run_wavelet_density_once.py --db $Db --output output\wavelet_density.json --pretty
python -m json.tool output\wavelet_density.json | Out-Null

Step "Run B6 Memory self-test"
python Core\run_memory_query_once.py --self-test --output output\memory_query_results.json --pretty
python -m json.tool output\memory_query_results.json | Out-Null

Step "Optional legacy comparisons"
if (Test-Path Core\run_regime_engine_once.py) {
    python Core\run_regime_engine_once.py --db $Db --pretty
}
if (Test-Path Core\run_temporal_density_once.py) {
    python Core\run_temporal_density_once.py --db $Db --tfs 5 --pretty
}

if ($Commit) {
    Step "Commit via pf_close_session"
    if (Test-Path .\pf_close_session.ps1) {
        .\pf_close_session.ps1 "V7.2: finalize B1 HMM, B4 Wavelet, B6 Memory"
    } else {
        git add Core\pf_hmm_regime.py Core\run_hmm_regime_once.py Core\pf_wavelet_density.py Core\run_wavelet_density_once.py Core\pf_memory_engine.py Core\run_memory_query_once.py scripts\validate_b1_b4_b6.ps1
        git commit -m "V7.2: finalize B1 HMM, B4 Wavelet, B6 Memory"
        git push origin main
    }
}

Step "Final status"
git status
