$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0159_b9_french_event_display_contract.py --extra-events-json samples\b9_french_event_display_contract_v0\sample_extra_events.json --output-dir outputs\b9_french_event_display_contract_v0 --print-json
