# auto_verify_b9_health.ps1
# Verification sante B9 en debut de session

$CORE = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $CORE

Write-Host "=== VERIFICATION SANTE B9 ===" -ForegroundColor Cyan

# Modules presents
$modules = @(
    "pf_data_visibility_guard.py",
    "pf_false_birth_filter.py",
    "pf_b6_field_memory_reader.py",
    "pf_b9_source_constants.py",
    "pf_price_verdict.py",
    "pf_zone_context_reader.py",
    "pf_terrain_node_snapshot.py",
    "pf_packet_requalifier_v767.py",
    "pf_engine_b9.py",
    "telegram_alert_sender_b9.py",
    "persist_node_b9.py"
)

foreach ($mod in $modules) {
    if (Test-Path $mod) {
        Write-Host "  OK $mod" -ForegroundColor Green
    } else {
        Write-Host "  MANQUANT : $mod" -ForegroundColor Red
    }
}

Write-Host "`nTests B9..." -ForegroundColor Yellow
python -m pytest tests\ -q --tb=no 2>&1

Write-Host "`n=== FIN VERIFICATION ===" -ForegroundColor Cyan
