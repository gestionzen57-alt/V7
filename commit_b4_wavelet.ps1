# Run from repository root or from Core parent.
# PowerFlow B4 Wavelet commit helper.

$ErrorActionPreference = "Stop"

if (Test-Path ".\Core\pf_wavelet_density.py") {
    $root = Get-Location
} elseif (Test-Path ".\pf_wavelet_density.py") {
    $root = (Get-Location).Parent
    Set-Location $root
} else {
    throw "Cannot find Core\pf_wavelet_density.py. Run this from the V7 repo root after copying the delivered files."
}

python -m py_compile .\Core\pf_wavelet_density.py .\Core\run_wavelet_density_once.py
python .\Core\run_wavelet_density_once.py --db .\Core\powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty --output .\Core\output\wavelet_density.json
python -m json.tool .\Core\output\wavelet_density.json > $null

git status
git add .\Core\pf_wavelet_density.py .\Core\run_wavelet_density_once.py
if (Test-Path ".\Core\output\wavelet_density.json") {
    git add -f .\Core\output\wavelet_density.json 2>$null
}
git commit -m "B4: Morlet Wavelet CWT upgrade"
git push

Write-Host "B4 Wavelet commit complete."
