param(
    [string]$CorePath = ".",
    [string]$PythonPath = "python",
    [switch]$SkipGitPush
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Core = (Resolve-Path $CorePath).Path
$Report = New-Object System.Collections.Generic.List[Object]

function Add-Result($Step, $Status, $Detail) {
    $Report.Add([pscustomobject]@{ Step=$Step; Status=$Status; Detail=$Detail }) | Out-Null
    Write-Host "$Status`t$Step`t$Detail"
}

function Run-Step($Step, [scriptblock]$Block) {
    try {
        & $Block
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { throw "LASTEXITCODE=$LASTEXITCODE" }
        Add-Result $Step "PASS" "ok"
    } catch {
        Add-Result $Step "FAIL" $_.Exception.Message
    }
}

Push-Location $Root

$PyFiles = @(
    "pf_cross_symbol_validation.py",
    "run_cross_symbol_validation_once.py",
    "scheduler_powerflow.py"
) + (Get-ChildItem -Path "PATCHED_RUNNERS" -Filter "*.py" | ForEach-Object { $_.FullName }) + (Get-ChildItem -Path "PATCHED_MODULES" -Filter "*.py" | ForEach-Object { $_.FullName })

Run-Step "py_compile delivered python" {
    foreach ($f in $PyFiles) { & $PythonPath -m py_compile $f }
}

Run-Step "copy pf_cross_symbol_validation.py" {
    Copy-Item "pf_cross_symbol_validation.py" (Join-Path $Core "pf_cross_symbol_validation.py") -Force
    Copy-Item "run_cross_symbol_validation_once.py" (Join-Path $Core "run_cross_symbol_validation_once.py") -Force
}

Run-Step "copy patched runners" {
    Copy-Item "PATCHED_RUNNERS\*.py" $Core -Force
}

Run-Step "copy patched pf modules" {
    Copy-Item "PATCHED_MODULES\*.py" $Core -Force
}

Run-Step "copy scheduler files" {
    Copy-Item "scheduler_powerflow.py" (Join-Path $Core "scheduler_powerflow.py") -Force
    Copy-Item "scheduler_config.json" (Join-Path $Core "scheduler_config.json") -Force
    Copy-Item "setup_windows_task_scheduler.ps1" (Join-Path $Core "setup_windows_task_scheduler.ps1") -Force
}

Run-Step "copy docs and dashboard patch" {
    Copy-Item "dashboard_multisymbol_patch.html" (Join-Path $Core "dashboard_multisymbol_patch.html") -Force
    Copy-Item "INTEGRATION_GUIDE.md" (Join-Path $Core "INTEGRATION_GUIDE_MULTISYMBOL.md") -Force
    Copy-Item "LEXIQUE_PATCH_MULTISYMBOL.md" (Join-Path $Core "LEXIQUE_PATCH_MULTISYMBOL.md") -Force
    Copy-Item "REGISTRE_BRIQUES_PATCH_MULTISYMBOL.md" (Join-Path $Core "REGISTRE_BRIQUES_PATCH_MULTISYMBOL.md") -Force
    Copy-Item "validation_checklist.md" (Join-Path $Core "validation_checklist_multisymbol.md") -Force
}

Push-Location $Core

Run-Step "test GBPUSD temporal node" {
    & $PythonPath run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --pretty
}

Run-Step "test cross-validation GBPUSD only" {
    & $PythonPath run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD --pretty
}

Run-Step "test scheduler once GBPUSD" {
    & $PythonPath scheduler_powerflow.py --once --symbols GBPUSD
}

Run-Step "verify GBPUSD dashboard outputs" {
    $Required = @(
        "output\dashboard_surface\GBPUSD\node.json",
        "output\dashboard_surface\GBPUSD\energy.json",
        "output\dashboard_surface\GBPUSD\regime_legacy.json"
    )
    foreach ($r in $Required) {
        if (-not (Test-Path $r)) { throw "Missing $r" }
    }
}

Run-Step "git add" {
    git add pf_cross_symbol_validation.py run_cross_symbol_validation_once.py scheduler_powerflow.py scheduler_config.json setup_windows_task_scheduler.ps1 `
        run_temporal_node_state_once.py run_currency_energy_probe_once.py run_regime_engine_once.py run_temporal_density_once.py run_spearman_gravity_once.py run_behavioral_alert_mapper_once.py `
        pf_temporal_density.py pf_spearman_gravity.py dashboard_multisymbol_patch.html INTEGRATION_GUIDE_MULTISYMBOL.md LEXIQUE_PATCH_MULTISYMBOL.md REGISTRE_BRIQUES_PATCH_MULTISYMBOL.md validation_checklist_multisymbol.md
}

Run-Step "git commit" {
    git commit -m "MultiSymbol: parametric symbol extension + cross-validation + scheduler"
}

if (-not $SkipGitPush) {
    Run-Step "git push" { git push }
} else {
    Add-Result "git push" "SKIP" "SkipGitPush enabled"
}

Pop-Location
Pop-Location

$ReportPath = Join-Path $Root "deploy_multisymbol_report.json"
$Report | ConvertTo-Json -Depth 4 | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host "REPORT $ReportPath"
$FailCount = ($Report | Where-Object { $_.Status -eq "FAIL" }).Count
if ($FailCount -gt 0) { exit 1 }
exit 0
