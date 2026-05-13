# Mission V7.4-EIE

## Objectif

Raccorder l'ancienne alerte EIE au socle V7.4.

EIE devient une brique de perception :
- tension elastique
- zone chargee
- fractalite M1/M5/M15
- confluence avec Daily, TopDown, B6, B8, Evidence et Phase

## Commande test dry-run

powershell:
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --dry-run

## Commande Telegram reel

powershell:
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --send

## Sorties attendues

- output/dashboard_surface/GBPUSD/eie_confluence.json
- output/dashboard_surface/GBPUSD/eie_confluence.txt
- output/dashboard_surface/GBPUSD/eie_gravity.json
- output/dashboard_surface/GBPUSD/eie_gravity.txt
- output/dashboard_surface/GBPUSD/eie_telegram_decision.json
- output/dashboard_surface/GBPUSD/eie_telegram_decision.txt
- output/dashboard_surface/eie_alert_queue.json

## Doctrine

EIE detecte.
Evidence Bus articule.
Phase nomme.
Telegram reveille si ACTIVE/HOT et non doublon.
Le trader decide.
