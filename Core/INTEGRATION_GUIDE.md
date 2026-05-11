# INTEGRATION GUIDE - Session Overlay + Dashboard Dual Display

Run depuis Core ou racine GPT :

```powershell
powershell -ExecutionPolicy Bypass -File .\git_deploy_session_overlay_dashboard_v3.ps1
```

Validation manuelle :

```powershell
python -m py_compile pf_session_overlay.py run_session_overlay_once.py patch_behavioral_alert_mapper.py test_session_overlay.py
python test_session_overlay.py
python run_session_overlay_once.py --at 2026-05-11T13:30:00Z --pretty
```

Regles :
- pf_session_overlay.py ne lit pas la DB.
- pf_session_overlay.py n'ecrit pas la DB.
- pas d'import cockpit/dashboard/telegram dans pf_session_overlay.py.
- le mapper enrichit les alertes, il ne decide pas.

