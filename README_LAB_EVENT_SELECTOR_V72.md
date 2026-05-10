# PowerFlow V7.2 — Lab Event Selector V0.2

## Objectif

Condense le Lab V7.2 sans censurer.

La V0.1 produit le microfilm complet. La V0.2 ajoute une couche lisible :

```text
events_index_full.json       = tous les événements, gardés ou non
key_events.json              = événements clés pour lecture
key_events.csv               = Excel
key_scene_clusters.json      = groupes de scènes consécutives
film_key_events.md           = film condensé
lab_report_key_events.html   = rapport lisible navigateur
event_selector_metrics.json  = métriques du sélecteur
```

## Doctrine

- Le microfilm complet reste intact.
- Aucun événement n’est supprimé.
- La sélection est une aide de lecture, pas un filtrage.
- Aucun BUY/SELL.
- Aucune décision.
- Aucune écriture DB.

## Installation

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
Expand-Archive -Path C:\Users\User\Downloads\pf_lab_engine_v72_v02_selector_pack.zip -DestinationPath . -Force
```

## Validation

```powershell
.\scripts\validate_lab_event_selector_v72.ps1
```

## Utilisation sur le dernier run Lab

```powershell
python Core\run_lab_event_selector_v72_once.py --latest --pretty
```

## Utilisation sur un run précis

```powershell
python Core\run_lab_event_selector_v72_once.py `
  --lab-run output\lab_runs\20260510_143532_GBPUSD_0900_1100 `
  --pretty
```

## Réglages

```powershell
python Core\run_lab_event_selector_v72_once.py --latest --warmup-index 15 --min-confidence 0.60 --pretty
```

- `--warmup-index 15` ignore les 15 premières frames pour les key events.
- `--min-confidence 0.60` garde les scènes suffisamment lisibles.
- `--no-scene-change` désactive la conservation automatique des changements de scène.

## Lecture recommandée

Ouvrir d’abord :

```text
output/lab_runs/<run_id>/lab_report_key_events.html
```

Puis :

```text
output/lab_runs/<run_id>/film_key_events.md
output/lab_runs/<run_id>/key_events.csv
```

Pour audit complet :

```text
output/lab_runs/<run_id>/events_index_full.json
```

## Commit

```powershell
git add Core\pf_lab_event_selector_v72.py Core\run_lab_event_selector_v72_once.py scripts\validate_lab_event_selector_v72.ps1 README_LAB_EVENT_SELECTOR_V72.md

git commit -m "Lab: add V7.2 key event selector"

git push origin main
```
