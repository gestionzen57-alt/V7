# POWERFLOW V7.6.6 POLISH REPORT

Scope strict : lisibilite francaise, warning cleanup, Telegram court/live.

Architecture non modifiee. GBPUSD only conserve. Format long V7.6 conserve pour debug/calibration.

Ajouts :
- patch/pf_telegram_short_live_v766.py
- run_powerflow_v766_telegram_short_live.ps1
- tests/test_v766_polish_static.py

Corrections :
- labels FR restants
- accents FR playbook/dashboard ciblés
- docstring raw pour eviter SyntaxWarning invalid escape sequence
