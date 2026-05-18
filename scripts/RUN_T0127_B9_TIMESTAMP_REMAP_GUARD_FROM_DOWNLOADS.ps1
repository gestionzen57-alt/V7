param(
  [string]$SequenceSummaryJson = "samples\b9_timestamp_remap_guard_v0\sample_t009_sequence_summary_shifted.json",
  [string]$ReplayReportJson = "samples\b9_timestamp_remap_guard_v0\sample_t009_replay_sequence_report.json",
  [string]$OutputDir = "outputs\b9_timestamp_remap_guard_v0"
)
$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
$cmd = @("tools\build_t0127_b9_timestamp_remap_guard_v0.py", "--sequence-summary-json", $SequenceSummaryJson, "--output-dir", $OutputDir)
if ($ReplayReportJson -and (Test-Path $ReplayReportJson)) {
  $cmd += @("--replay-report-json", $ReplayReportJson)
}
python @cmd
