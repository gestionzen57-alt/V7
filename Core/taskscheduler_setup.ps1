<#
PowerFlow V7.2 — Windows Task Scheduler setup
Creates an hourly P0 monitoring task.
Run from Core/ as Administrator if needed.
#>

param(
  [string]$TaskName = "PowerFlow_P0_Full_Workflow",
  [string]$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core",
  [string]$Symbol = "GBPUSD"
)

$Action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$CorePath\run_p0_full_workflow.ps1`" -Symbol $Symbol -Once" `
  -WorkingDirectory $CorePath

$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "PowerFlow V7.2 P0 hourly monitoring" -Force
Write-Host "Scheduled task created: $TaskName"
