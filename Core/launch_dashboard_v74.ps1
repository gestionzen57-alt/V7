param(
  [int]$Port = 8787,
  [string]$Page = "dashboard_powerflow_v74.html"
)

$Core = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Core

Write-Host "POWERFLOW V7.4 DASHBOARD SERVER" -ForegroundColor Cyan
Write-Host "Core=$Core"
Write-Host "Port=$Port"
Write-Host "Page=$Page"

$Url = "http://localhost:$Port/$Page"

$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $existing) {
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$Core`"; python -m http.server $Port"
  Start-Sleep -Seconds 2
}

Start-Process $Url

Write-Host "OPENED: $Url" -ForegroundColor Green
