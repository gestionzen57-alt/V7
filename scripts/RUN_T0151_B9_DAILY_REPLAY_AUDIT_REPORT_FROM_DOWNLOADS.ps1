$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core

$ReplayCsv = "outputs\b9_real_replay_day_pack_runner_v0\B9_REAL_REPLAY_DAY_RESULTS_V0.csv"
$SessionCsv = "outputs\b9_session_replay_scorecard_v0\B9_SESSION_REPLAY_SCORECARD_ROWS_V0.csv"
$GoldenCsv = "Docs\Reports\T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv"
$OutputDir = "outputs\b9_daily_replay_audit_report_v0"

$Args = @("tools\build_t0151_b9_daily_replay_audit_report.py", "--output-dir", $OutputDir)
if (Test-Path $ReplayCsv) { $Args += @("--replay-results-csv", $ReplayCsv) }
if (Test-Path $SessionCsv) { $Args += @("--session-scorecard-csv", $SessionCsv) }
if (Test-Path $GoldenCsv) { $Args += @("--golden-cases-csv", $GoldenCsv) }

python @Args
