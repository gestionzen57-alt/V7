# Run T0169 dashboard surfaces from Downloads/Core
$ErrorActionPreference = "Stop"

$Repo = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Write-Host "[T0169-RUN] Core: $Repo"
Set-Location -LiteralPath $Repo

python tools\build_t0169_b9_reality_board_surface_adapter_candidate.py --core-root . --output-root outputs

Write-Host "[T0169-RUN] Outputs:"
Write-Host " - outputs\b9_reality_board_read_model_v01\B9_REALITY_BOARD_READ_MODEL_V01.json"
Write-Host " - outputs\b9_reality_board_scene_panel_candidate_v01\B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json"
Write-Host " - outputs\b9_reality_board_surface_adapter_candidate_v0\B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json"
