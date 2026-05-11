<#
PowerFlow V7.2.1 one-click deploy
B1+ HMM MTF regime engine + B4+ Wavelet Morlet density

Usage from PowerFlow Core:
  powershell -ExecutionPolicy Bypass -File .\powerflow_v721_oneclick_deploy.ps1

Usage with ZIP next to script:
  powershell -ExecutionPolicy Bypass -File .\powerflow_v721_oneclick_deploy.ps1 -PackageZip .\powerflow_v721_b1hmm_mtf_b4wavelet_oneclick.zip -CorePath C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
#>

param(
  [string]$CorePath = ".",
  [string]$PackageZip = "",
  [string]$DbPath = "powerflow.db",
  [string]$Symbol = "GBPUSD",
  [string]$HMMTfs = "60,30,15",
  [string]$WaveletTfs = "1,5,15",
  [string]$CommitMessage = "B1+: HMM MTF regime engine + B4+: Wavelet Morlet density - dual architecture",
  [switch]$SkipInstall,
  [switch]$SkipRuntime,
  [switch]$SkipTests,
  [switch]$SkipGit,
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$script:Report = New-Object System.Collections.Generic.List[object]
$script:FinalStatus = "PASS"
$script:TempExtract = $null

function Add-Result {
  param([string]$Step, [string]$Status, [string]$Detail)
  $entry = [pscustomobject]@{
    step = $Step
    status = $Status
    detail = $Detail
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
  }
  $script:Report.Add($entry) | Out-Null
  Write-Host ("[{0}] {1} - {2}" -f $Status, $Step, $Detail)
}

function Invoke-Checked {
  param([string]$Step, [scriptblock]$Action)
  try {
    & $Action
    Add-Result $Step "PASS" "ok"
  } catch {
    Add-Result $Step "FAIL" $_.Exception.Message
    $script:FinalStatus = "FAIL"
    throw
  }
}

function Invoke-Soft {
  param([string]$Step, [scriptblock]$Action)
  try {
    & $Action
    Add-Result $Step "PASS" "ok"
  } catch {
    Add-Result $Step "WARN" $_.Exception.Message
  }
}

function Resolve-FullPath {
  param([string]$Path)
  if ([System.IO.Path]::IsPathRooted($Path)) { return $Path }
  return (Join-Path (Get-Location) $Path)
}

function Test-PackageFiles {
  param([string]$Root)
  $required = @(
    "pf_hmm_regime_engine.py",
    "pf_wavelet_density.py",
    "run_hmm_regime_once.py",
    "run_wavelet_density_once.py",
    "test_hmm_regime.py",
    "test_wavelet_density.py"
  )
  foreach ($f in $required) {
    if (-not (Test-Path (Join-Path $Root $f))) { return $false }
  }
  return $true
}

function Get-PackageRoot {
  $scriptDir = Split-Path -Parent $MyInvocation.ScriptName
  if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

  if (Test-PackageFiles $scriptDir) {
    Add-Result "locate package" "PASS" "using extracted package folder: $scriptDir"
    return $scriptDir
  }

  $zipCandidate = $PackageZip
  if ([string]::IsNullOrWhiteSpace($zipCandidate)) {
    $matches = Get-ChildItem -Path $scriptDir -Filter "powerflow_v721*b4wavelet*.zip" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($matches.Count -gt 0) { $zipCandidate = $matches[0].FullName }
  }

  if ([string]::IsNullOrWhiteSpace($zipCandidate)) {
    throw "Package files not found and no ZIP found next to script. Pass -PackageZip or extract the ZIP first."
  }

  if (-not [System.IO.Path]::IsPathRooted($zipCandidate)) {
    $zipCandidate = Join-Path $scriptDir $zipCandidate
  }
  if (-not (Test-Path $zipCandidate)) { throw "Package ZIP not found: $zipCandidate" }

  $temp = Join-Path $env:TEMP ("powerflow_v721_patch_" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Force -Path $temp | Out-Null
  Expand-Archive -Force -Path $zipCandidate -DestinationPath $temp
  $script:TempExtract = $temp

  if (-not (Test-PackageFiles $temp)) { throw "ZIP extracted, but required package files are missing: $zipCandidate" }
  Add-Result "extract package zip" "PASS" "extracted to $temp"
  return $temp
}

function Invoke-PipInstall {
  param([string[]]$Packages)
  if ($SkipInstall) {
    Add-Result "install python dependencies" "SKIP" "SkipInstall set"
    return
  }
  try {
    python -m pip install @Packages --break-system-packages
  } catch {
    Write-Host "pip with --break-system-packages failed; retrying without it"
    python -m pip install @Packages
  }
}

function Assert-NoForbiddenImports {
  param([string]$Root)
  $pfFiles = @("pf_hmm_regime_engine.py", "pf_wavelet_density.py")
  foreach ($f in $pfFiles) {
    $path = Join-Path $Root $f
    $content = Get-Content -Raw -Path $path
    if ($content -match "(?m)^\s*(from|import)\s+(cockpit_|dashboard_|telegram_)") {
      throw "forbidden cockpit/dashboard/telegram import found in $f"
    }
  }
}

function Assert-ReadonlyDbPattern {
  param([string]$Root)
  $pfFiles = @("pf_hmm_regime_engine.py", "pf_wavelet_density.py")
  foreach ($f in $pfFiles) {
    $path = Join-Path $Root $f
    $content = Get-Content -Raw -Path $path
    if ($content -notmatch "mode=ro") {
      throw "read-only SQLite mode pattern not found in $f"
    }
  }
}

try {
  $PackageRoot = Get-PackageRoot
  $Core = Resolve-FullPath $CorePath
  if (-not (Test-Path $Core)) { throw "CorePath not found: $Core" }
  $Core = (Resolve-Path $Core).Path

  Invoke-Checked "preflight CorePath" {
    Set-Location $Core
    if (-not (Test-Path $DbPath)) { throw "DB not found at $DbPath from CorePath $Core" }
  }

  Invoke-Checked "architecture guards on package" {
    Assert-NoForbiddenImports $PackageRoot
    Assert-ReadonlyDbPattern $PackageRoot
  }

  Invoke-Checked "py_compile package files" {
    python -m py_compile `
      (Join-Path $PackageRoot "pf_hmm_regime_engine.py") `
      (Join-Path $PackageRoot "pf_wavelet_density.py") `
      (Join-Path $PackageRoot "run_hmm_regime_once.py") `
      (Join-Path $PackageRoot "run_wavelet_density_once.py") `
      (Join-Path $PackageRoot "test_hmm_regime.py") `
      (Join-Path $PackageRoot "test_wavelet_density.py")
  }

  Invoke-Checked "copy package files to Core" {
    $files = @(
      "pf_hmm_regime_engine.py",
      "pf_wavelet_density.py",
      "run_hmm_regime_once.py",
      "run_wavelet_density_once.py",
      "test_hmm_regime.py",
      "test_wavelet_density.py",
      "dashboard_surface_dual_patch.html",
      "INSTALL_REQUIREMENTS.txt",
      "INTEGRATION_GUIDE.md",
      "LEXIQUE_PATCH_B1HMM_B4WAVELET.md",
      "REGISTRE_BRIQUES_PATCH_B1HMM_B4WAVELET.md",
      "validation_checklist.md",
      "PACK_MANIFEST.json",
      "powerflow_v721_oneclick_deploy.ps1"
    )
    foreach ($f in $files) {
      $src = Join-Path $PackageRoot $f
      if (Test-Path $src) { Copy-Item -Force $src (Join-Path $Core $f) }
    }
  }

  Invoke-Checked "install python dependencies" {
    Invoke-PipInstall -Packages @("numpy", "hmmlearn", "PyWavelets")
  }

  Invoke-Checked "py_compile Core files" {
    python -m py_compile .\pf_hmm_regime_engine.py .\pf_wavelet_density.py .\run_hmm_regime_once.py .\run_wavelet_density_once.py .\test_hmm_regime.py .\test_wavelet_density.py
  }

  if (-not $SkipRuntime) {
    Invoke-Checked "run B1+ HMM MTF once" {
      python .\run_hmm_regime_once.py --db $DbPath --symbol $Symbol --tfs $HMMTfs --pretty
    }

    Invoke-Checked "run B4+ Wavelet once" {
      python .\run_wavelet_density_once.py --db $DbPath --symbol $Symbol --tfs $WaveletTfs --pretty
    }

    Invoke-Checked "verify dashboard surface outputs" {
      if (-not (Test-Path ".\output\dashboard_surface\regime_hmm.json")) { throw "missing output/dashboard_surface/regime_hmm.json" }
      if (-not (Test-Path ".\output\dashboard_surface\wavelet.json")) { throw "missing output/dashboard_surface/wavelet.json" }
    }
  } else {
    Add-Result "runtime runners" "SKIP" "SkipRuntime set"
  }

  if (-not $SkipTests) {
    Invoke-Checked "run unit tests" {
      python .\test_hmm_regime.py
      python .\test_wavelet_density.py
    }
  } else {
    Add-Result "unit tests" "SKIP" "SkipTests set"
  }

  if (-not $SkipGit) {
    Invoke-Checked "git status preflight" {
      git status --short | Out-Null
    }

    Invoke-Checked "git add delivered files" {
      git add pf_hmm_regime_engine.py pf_wavelet_density.py run_hmm_regime_once.py run_wavelet_density_once.py test_hmm_regime.py test_wavelet_density.py dashboard_surface_dual_patch.html INSTALL_REQUIREMENTS.txt INTEGRATION_GUIDE.md LEXIQUE_PATCH_B1HMM_B4WAVELET.md REGISTRE_BRIQUES_PATCH_B1HMM_B4WAVELET.md validation_checklist.md PACK_MANIFEST.json powerflow_v721_oneclick_deploy.ps1
    }

    $hasStaged = $true
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { $hasStaged = $false }

    if ($hasStaged) {
      Invoke-Checked "git commit" {
        git commit -m $CommitMessage
      }
      if (-not $NoPush) {
        Invoke-Checked "git push" {
          git push
        }
      } else {
        Add-Result "git push" "SKIP" "NoPush set"
      }
    } else {
      Add-Result "git commit" "SKIP" "no staged changes"
      Add-Result "git push" "SKIP" "no commit created"
    }
  } else {
    Add-Result "git" "SKIP" "SkipGit set"
  }

} catch {
  $script:FinalStatus = "FAIL"
} finally {
  try {
    Set-Location $Core
    $jsonPath = Join-Path $Core "deploy_powerflow_v721_oneclick_report.json"
    $mdPath = Join-Path $Core "deploy_powerflow_v721_oneclick_report.md"
    $script:Report | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $jsonPath
    $lines = @()
    $lines += "# PowerFlow V7.2.1 One-Click Deploy Report"
    $lines += ""
    $lines += "FINAL: $script:FinalStatus"
    $lines += "UTC: $((Get-Date).ToUniversalTime().ToString('o'))"
    $lines += "Symbol: $Symbol"
    $lines += "HMM TFs: $HMMTfs"
    $lines += "Wavelet TFs: $WaveletTfs"
    $lines += ""
    foreach ($r in $script:Report) { $lines += ("- [{0}] {1}: {2}" -f $r.status, $r.step, $r.detail) }
    $lines | Out-File -Encoding utf8 $mdPath
    Write-Host "FINAL: $script:FinalStatus"
    Write-Host "Report JSON: $jsonPath"
    Write-Host "Report MD:   $mdPath"
  } catch {
    Write-Host "Could not write final report: $($_.Exception.Message)"
  }

  if ($script:TempExtract -and (Test-Path $script:TempExtract)) {
    Remove-Item -Recurse -Force $script:TempExtract -ErrorAction SilentlyContinue
  }

  if ($script:FinalStatus -eq "FAIL") { exit 1 } else { exit 0 }
}
