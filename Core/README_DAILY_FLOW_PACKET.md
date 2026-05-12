# PowerFlow V7.3.1 — DAILY_FLOW_PACKET

## Mission

Transformer les briques V7.3 en lecture quotidienne exploitable :

- High du jour
- Low du jour
- Close position
- Niveaux testés
- Niveaux rejetés
- Liquidity sweep candidat
- Intention détectée
- Prédiction de session suivante
- Conditions LTF
- Comparaison trader / machine

## Doctrine

Le module ne donne pas de trade.
Il produit une lecture de flux et un support de journal.

M1 n'est jamais censuré.
HTF structure le contexte.
MTF prépare le plan.
LTF qualifie l'entrée.

## Fichiers

- `pf_daily_flow_packet.py`
- `run_daily_flow_packet_once.py`
- `run_daily_flow_packet_all_once.py`
- `dashboard_normalize_daily_flow_packet.py`
- `dashboard_daily_flow_packet_card_patch.html`
- `dashboard_inject_daily_flow_packet_card.py`

## Commandes

```powershell
python run_daily_flow_packet_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/daily_flow_packets.json --pretty

python dashboard_normalize_daily_flow_packet.py --input output/dashboard_surface/daily_flow_packets.json --output output/dashboard_surface/daily_flow_packet.json --pretty
```

## Sorties

- `output/dashboard_surface/daily_flow_packets.json`
- `output/dashboard_surface/daily_flow_packet.json`
- `output/dashboard_surface/<SYMBOL>/daily_flow_packet.json`

## Risques techniques

- OHLC absent
- M1 trop fin
- référence previous day manquante
- pas de niveau testé
- pas de sweep détecté
