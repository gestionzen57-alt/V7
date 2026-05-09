# PowerFlow V6 — Telegram Agentic Nodes Loop V0.1
# Reads output/cockpit_agentic_state_v01.json and sends Telegram WATCH node alerts.
# Required env:
#   $env:TELEGRAM_BOT_TOKEN="xxxxx"
#   $env:TELEGRAM_CHAT_ID="xxxxx"

param(
    [string]$JsonPath = "output/cockpit_agentic_state_v01.json",
    [int]$SleepSeconds = 15,
    [string]$MinSeverity = "watch"
)

Write-Host "POWERFLOW TELEGRAM AGENTIC NODES LOOP"
Write-Host "JSON: $JsonPath"
Write-Host "SLEEP: $SleepSeconds sec"
Write-Host "MIN SEVERITY: $MinSeverity"

while ($true) {
    python run_telegram_agentic_nodes_once.py --json $JsonPath --min-severity $MinSeverity
    Start-Sleep -Seconds $SleepSeconds
}
