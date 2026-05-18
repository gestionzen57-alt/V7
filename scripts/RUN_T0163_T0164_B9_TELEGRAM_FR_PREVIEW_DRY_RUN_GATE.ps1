param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string]$OutputDir = "outputs\b9_telegram_fr_preview_v0"
)
$ErrorActionPreference = "Stop"
Write-Host "=== RUN T0163/T0164 B9 TELEGRAM FR PREVIEW + DRY RUN GATE ===" -ForegroundColor Cyan
if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
Set-Location $RepoRoot
$Tool = ".\tools\b9_telegram_fr_preview_dry_run_gate.py"
if (!(Test-Path $Tool)) { throw "Tool not found: $Tool" }
python $Tool `
  --gate-candidate "outputs\b9_telegram_fr_gate_candidate_v0\B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json" `
  --reality-board "outputs\b9_reality_board_integration_candidate_v0\B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json" `
  --attention-packet "outputs\b9_trader_attention_packet_v0\B9_TRADER_ATTENTION_PACKET_V0.json" `
  --display-contract "outputs\b9_french_event_display_contract_v0\B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json" `
  --output-dir $OutputDir
if ($LASTEXITCODE -ne 0) { throw "Preview/gate failed. Check forbidden language or missing required sections." }
Write-Host "Done." -ForegroundColor Green
