# PowerFlow V7.3.3 — LIVE_FLOW_BRIEF_AND_TELEGRAM_GATE

Objectif: intégrer la couche live sans créer de scheduler parallèle.

## Modules

- `pf_telegram_memory_gate.py`
- `dashboard_normalize_live_brief.py`
- `dashboard_live_brief_card_patch.html`
- `dashboard_inject_live_brief_card.py`
- `patch_scheduler_turbo_live_brief_v733.py`

## Commandes

Test sans Telegram:

```powershell
python pf_flow_packet_once.py
python pf_packet_live_gate_once.py
python pf_gbpusd_live_decision_once.py
python pf_cockpit_live_status_once.py
python pf_powerflow_live_brief_once.py
python dashboard_normalize_live_brief.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/live_brief_dashboard.json --pretty
```

Mémoire Telegram dry-run:

```powershell
python pf_telegram_memory_gate.py --symbol GBPUSD --cooldown-min 10 --pretty
```

Envoi réel avec mémoire:

```powershell
python pf_telegram_memory_gate.py --symbol GBPUSD --cooldown-min 10 --execute --pretty
```
