@echo off
REM ============================================================================
REM TEST_TRADER_ALERT_STATE_WITH_FRESH_ALERTS.bat
REM
REM Test avec alertes ultra-fraîches
REM ============================================================================

echo.
echo ============================================================
echo TRADER ALERT STATE V0.1 - TEST AVEC ALERTES FRESH
echo ============================================================
echo.

REM Verifier fichiers
IF NOT EXIST "pf_trader_alert_state.py" (
    echo ERREUR: pf_trader_alert_state.py manquant
    pause
    exit /b 1
)

IF NOT EXIST "behavioral_alert_queue_TEST_FRESH.json" (
    echo ERREUR: behavioral_alert_queue_TEST_FRESH.json manquant
    echo Telecharge ce fichier de test dans core/
    pause
    exit /b 1
)

echo TEST: Utilisation de behavioral_alert_queue_TEST_FRESH.json
echo.

REM Executer avec fichier de test
python pf_trader_alert_state.py --behavioral behavioral_alert_queue_TEST_FRESH.json --cockpit output/cockpit_agentic_state_v01.json --runtime-status output/runtime_status.json --pipeline-trace output/pipeline_trace.json --dashboard-data dashboard_data.json --pretty

echo.
echo ============================================================
echo FIN DU TEST
echo ============================================================
echo.
echo Le fichier output\trader_alert_state.json a ete genere
echo avec les alertes de test ultra-fraiches.
echo.

pause
