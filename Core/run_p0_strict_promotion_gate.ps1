param(
    [string]$Root = ".",
    [switch]$RunP0,
    [switch]$PromoteFinal,
    [string]$Symbol = "GBPUSD"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Core = Resolve-Path $Root
Set-Location $Core

if ($RunP0) {
    Write-Host "RUN P0 final auto"
    .\run_p0_final_auto.ps1 -Symbol $Symbol
}

$cmd = @(".\p0_strict_promotion_gate.py", "--root", ".")
if ($PromoteFinal) {
    $cmd += "--in-place"
}

python @cmd

Write-Host ""
Write-Host "Promotion report:"
Get-Content .\output\P0_STRICT_PROMOTION_DECISION.md
