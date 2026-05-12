# REGISTRE BRIQUES — PATCH V7.3.1 DAILY_FLOW_PACKET

## pf_daily_flow_packet.py

Type : moteur PowerFlow / lecture quotidienne  
Préfixe : pf_*  
DB : read-only  
Rôle : construire une fiche quotidienne concrète à partir des niveaux OHLC et des sorties V7.3.

Entrées :

- `powerflow.db`
- `output/dashboard_surface/topdown_market_reader.json`
- `output/dashboard_surface/topdown_reader.json`
- `output/dashboard_surface/data_health.json`
- `output/dashboard_surface/signal_adaptive.json`
- `output/dashboard_surface/flow_ontology_cycle_summary.json`

Sorties :

- `output/dashboard_surface/<SYMBOL>/daily_flow_packet.json`

## run_daily_flow_packet_once.py

Runner symbole unique.

## run_daily_flow_packet_all_once.py

Runner multi-symbol.

Sortie :

- `output/dashboard_surface/daily_flow_packets.json`

## dashboard_normalize_daily_flow_packet.py

Normaliseur dashboard contractuel.

Sortie :

- `output/dashboard_surface/daily_flow_packet.json`

## dashboard_daily_flow_packet_card_patch.html

Carte dashboard : lecture courte du daily packet.

## dashboard_inject_daily_flow_packet_card.py

Injection idempotente de la carte dashboard.
