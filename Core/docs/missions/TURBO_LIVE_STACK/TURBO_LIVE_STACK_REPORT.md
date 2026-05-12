# PowerFlow Turbo Live Stack Report

- Created: `2026-05-12T14:54:59.581444+00:00`
- Mode: `ONE_SHOT_RUNNER`
- Verdict: `TURBO_STACK_OK`
- Primary symbol: `GBPUSD`

## Pipeline exécuté

- `OK` — daily_flow_packet_all
- `OK` — daily_flow_packet_normalize
- `OK` — topdown_market_reader
- `OK` — gbpusd_live_decision
- `OK` — cockpit_live_status
- `OK` — powerflow_live_brief
- `OK` — order_flow_proxy_all
- `OK` — b6_live_fusion
- `OK` — powerflow_telegram_gate
- `OK` — b6_telegram_gate

## Lecture primaire

### Daily
- `method`: `DAILY_FLOW_PACKET_V731`
- `intent`: `SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP`
- `prediction`: `WATCH_NEXT_SESSION_FOR_DOWNSIDE_ACCEPTANCE_AFTER_HIGH_SWEEP`
- `close_position`: `LOW_THIRD`
- `high`: `1.36111`
- `low`: `1.35025`
- `close`: `1.35353`
- `tested`: `8`
- `rejected`: `2`
- `sweeps`: `1`
- `technical_risks`: `[]`

### TopDown
- `flux`: `HTF_INSIDE_RANGE_OR_NEUTRAL`
- `zone`: `INSIDE_HTF_RANGE`
- `driver`: `USD_WEAKNESS_DOMINANT`
- `condition`: `HOT_ATTENTION_CONDITION_PRESENT`
- `machine_intention`: `REJECTION_OR_TRAP_WATCH`
- `ontology`: `INFLEXION`
- `technical_fragility`: `['DAILY_LOW_SAMPLE_FOR_ROTATION', 'WEEKLY_LOW_SAMPLE_FOR_ROTATION']`

### Live
- `state`: `LIVE_INFO`
- `level`: `WATCH`
- `bias`: `PAIR_DOWN`
- `message`: `None`
- `live_count`: `2`
- `expired_count`: `0`

### PowerFlow Brief
- `action`: `WAKE_TRADER`
- `synthesis`: `TRAP_CONTEXT_ALIGNED`
- `reading`: `Daily et topdown convergent vers un contexte piège/rejet. Attendre un paquet live plus chaud pour alerte forte.`

### B6 Microstructure
- `state`: `RELEASED`
- `level`: `None`
- `tension`: `32.2`
- `delta`: `-375.6886`
- `direction`: `SELL_SIDE`
- `absorption`: `PARTIAL_ABSORPTION`
- `imbalance`: `SELL_DOMINANT`
- `alerts`: `0`

### B6 Fusion
- `action`: `None`
- `synthesis`: `None`
- `message`: `None`

## Outputs contrôlés

- `output\dashboard_surface\GBPUSD\daily_flow_packet.json` exists=True size=5754
- `output\dashboard_surface\GBPUSD\topdown_market_reader.json` exists=True size=32737
- `output\dashboard_surface\GBPUSD\topdown_market_reading.json` exists=True size=32989
- `output\dashboard_surface\GBPUSD\live_decision.json` exists=True size=428
- `output\dashboard_surface\GBPUSD\cockpit_live_status.txt` exists=True size=72
- `output\dashboard_surface\GBPUSD\powerflow_live_brief.json` exists=True size=1718
- `output\dashboard_surface\GBPUSD\powerflow_live_brief.txt` exists=True size=1025
- `output\dashboard_surface\GBPUSD\microstructure_state.json` exists=True size=7074
- `output\dashboard_surface\GBPUSD\microstructure_state.txt` exists=True size=184
- `output\dashboard_surface\GBPUSD\b6_live_fusion.json` exists=True size=1517
- `output\dashboard_surface\GBPUSD\b6_live_fusion.txt` exists=True size=660
- `output\dashboard_surface\daily_flow_packet.json` exists=True size=1856
- `output\dashboard_surface\daily_flow_packets.json` exists=True size=17897
- `output\dashboard_surface\microstructure_states.json` exists=True size=26044

## Risques techniques

- `DAILY_LOW_SAMPLE_FOR_ROTATION`
- `WEEKLY_LOW_SAMPLE_FOR_ROTATION`

## Suite logique

1. Si `TURBO_STACK_OK`, lancer ce runner via tâche Windows 5 min ou l'intégrer dans `scheduler_powerflow_turbo_wrapper.py`.
2. Si `TURBO_STACK_PARTIAL`, lire les stderr_tail dans le JSON.
3. Garder M1 uniquement sur GBPUSD si objectif DB compacte.
4. Ne pas toucher `capture_bridge.py` ni écrire manuellement dans `powerflow.db`.