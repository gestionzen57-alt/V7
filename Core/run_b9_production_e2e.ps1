param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT",
    [switch]$RunScheduler5Min,
    [switch]$SkipFlask
)

$ErrorActionPreference = "Stop"

function Log($msg) { Write-Host "[B9-PROD-E2E] $msg" }

$RepoRoot = (Resolve-Path $RepoRoot).Path
$CorePath = Join-Path $RepoRoot "Core"

Set-Location $CorePath

$argsList = @("validate_b9_production_final.py")
if ($RunScheduler5Min) {
    $argsList += "--run-scheduler"
    $argsList += "--duration-seconds"
    $argsList += "300"
    $argsList += "--interval-seconds"
    $argsList += "60"
}
if ($SkipFlask) {
    $argsList += "--skip-flask"
}

Log "running python $($argsList -join ' ')"
python @argsList

if ($LASTEXITCODE -eq 0) {
    Log "E2E validation OK"
} else {
    Log "E2E validation partial/fail; inspect Core\docs\Reports\RAPPORT_VALIDATION_B9_PRODUCTION_FINAL.md"
    exit $LASTEXITCODE
}
