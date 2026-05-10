# Install/copy helper for PowerFlow V7.2 batch tester
# Usage from repo root:
#   .\install_batch_tester.ps1

$ErrorActionPreference = "Stop"

Write-Host "Installing test_batch_all_bricks.py in current directory..."
Copy-Item -Path "$PSScriptRoot\test_batch_all_bricks.py" -Destination ".\test_batch_all_bricks.py" -Force

Write-Host "Compile..."
python -m py_compile .\test_batch_all_bricks.py

Write-Host "Done. Run:"
Write-Host "python .\test_batch_all_bricks.py"
