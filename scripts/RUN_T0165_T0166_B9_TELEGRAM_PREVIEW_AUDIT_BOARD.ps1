param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string]$PreviewRoot = "outputs\b9_telegram_fr_preview_v0",
    [string]$OutputDir = "outputs\b9_telegram_preview_audit_board_v0",
    [switch]$StrictExit
)
$ErrorActionPreference = "Stop"
Write-Host "=== RUN T0165A B9 TELEGRAM PREVIEW AUDIT BOARD ===" -ForegroundColor Cyan
if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
Set-Location $RepoRoot
$Tool = ".\tools\b9_telegram_preview_audit_board.py"
if (!(Test-Path $Tool)) { throw "Tool not found: $Tool" }
$Args = @("--preview-root", $PreviewRoot, "--output-dir", $OutputDir)
if ($StrictExit) { $Args += "--strict-exit" }
python $Tool @Args
if ($LASTEXITCODE -ne 0) { throw "Audit board strict failure. Inspect output board." }
Write-Host "Done." -ForegroundColor Green
