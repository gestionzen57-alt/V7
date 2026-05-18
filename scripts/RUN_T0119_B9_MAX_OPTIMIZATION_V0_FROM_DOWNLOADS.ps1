param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$Downloads = "C:\Users\User\Downloads",
  [string]$OutputDir = "outputs\b9_max_optimization_v0"
)

$ErrorActionPreference = "Stop"
Set-Location $Core

$Script = Join-Path $Core "tools\build_t0119_b9_max_optimization_v0.py"
$Sample = Join-Path $Core "samples\b9_max_optimization_v0\sample_t009_sequence_summary_raw_calibrated.json"

$Docs = @(
  (Join-Path $Core "Docs\Reports"),
  (Join-Path $Core "docs\Reports")
) | Where-Object { Test-Path $_ }

$Args = @($Script, "--sequence-summary-json", $Sample, "--output-dir", $OutputDir)
if ($Docs.Count -gt 0) {
  $Args += "--analysis-docs"
  $Args += $Docs
}

Write-Host "=== RUN T0119 B9 MAX OPTIMIZATION V0 ==="
python @Args
