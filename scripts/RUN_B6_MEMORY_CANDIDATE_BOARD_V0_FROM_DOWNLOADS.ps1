param(
  [string]$Downloads = "C:\Users\User\Downloads",
  [string]$OutputDir = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\outputs\b6_memory_candidate_board_v0_regenerated"
)

$ErrorActionPreference = "Stop"
$Repo = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
$ForceZip = Join-Path $Downloads "B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.zip"
$RecoveredZip = Join-Path $Downloads "B9_RAW_CALIBRATION_OUTPUTS_20260506_0001_0055_SHIFT0_RAW.zip"
$Script = Join-Path $Repo "tools\build_b6_memory_candidate_board_v0_from_uploads.py"

if (!(Test-Path $Repo)) { throw "Repo Core introuvable: $Repo" }
if (!(Test-Path $Script)) { throw "Script B6 introuvable: $Script" }
if (!(Test-Path $ForceZip)) { throw "ZIP FORCE introuvable dans Downloads: $ForceZip" }
if (!(Test-Path $RecoveredZip)) { throw "ZIP 06/05 introuvable dans Downloads: $RecoveredZip" }

Set-Location $Repo
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

python -m py_compile $Script
python $Script --force-zip $ForceZip --recovered-zip $RecoveredZip --output-dir $OutputDir

Write-Host "" 
Write-Host "B6 Memory Candidate Board V0 régénéré avec succès." -ForegroundColor Green
Write-Host "OutputDir: $OutputDir" -ForegroundColor Cyan
