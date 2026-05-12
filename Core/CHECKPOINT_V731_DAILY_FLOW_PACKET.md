# CHECKPOINT — V7.3.1 DAILY_FLOW_PACKET

## État

V7.3.1 ajoute le Daily Flow Packet.

## But

Créer une fiche quotidienne alignée avec les besoins du trader :

- noter niveaux
- repérer sweeps
- lire intention
- préparer la session
- comparer prédiction / résultat réel

## Fichiers

- pf_daily_flow_packet.py
- run_daily_flow_packet_once.py
- run_daily_flow_packet_all_once.py
- dashboard_normalize_daily_flow_packet.py
- dashboard_daily_flow_packet_card_patch.html
- dashboard_inject_daily_flow_packet_card.py

## Sorties

- output/dashboard_surface/daily_flow_packets.json
- output/dashboard_surface/daily_flow_packet.json
- output/dashboard_surface/<SYMBOL>/daily_flow_packet.json

## Prochaine étape

Intégrer V7.3.1 dans `scheduler_powerflow_turbo_wrapper.py` après validation manuelle.
