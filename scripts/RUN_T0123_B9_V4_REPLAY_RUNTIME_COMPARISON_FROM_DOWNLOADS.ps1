param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$BeforeSummary = "samples\b9_v4_replay_runtime_comparison_v0\sample_t009_sequence_summary_before_v4.json",
  [string]$AfterSummary = "",
  [string]$OutputDir = "outputs\b9_v4_replay_runtime_comparison_v0"
)

Write-Host "=== RUN T0123 B9 V4 REPLAY RUNTIME COMPARISON ===" -ForegroundColor Cyan
Set-Location $Core
$cmd = @("tools\build_t0123_b9_v4_replay_runtime_comparison.py", "--before-summary-json", $BeforeSummary, "--output-dir", $OutputDir)
if ($AfterSummary -and (Test-Path $AfterSummary)) { $cmd += @("--after-summary-json", $AfterSummary) }
python @cmd
