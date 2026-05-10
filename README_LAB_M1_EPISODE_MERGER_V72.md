# PowerFlow V7.2 — M1 Episode Merger V0.4

## Objectif

Fusionner les zooms M1 voisins en épisodes lisibles.

La V0.3 génère :

```text
m1_zoom_index.json
film_m1_zoom.md
```

La V0.4 ajoute :

```text
m1_episodes.json
film_m1_episodes.md
lab_report_m1_episodes.html
m1_episode_merger_metrics.json
```

## Doctrine

- M1 reste le microscope.
- Le microfilm complet n’est pas supprimé.
- `m1_zoom_index.json` reste intact.
- La fusion sert à lire, pas à filtrer.
- Aucun BUY/SELL.
- Aucune décision.
- Aucune écriture DB.

## Installation

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
Expand-Archive -Path C:\Users\User\Downloads\pf_lab_engine_v72_v04_m1_episode_merger_pack.zip -DestinationPath . -Force
```

## Validation

```powershell
.\scripts\validate_lab_m1_episode_merger_v72.ps1
```

## Utilisation

Sur le dernier run qui contient `m1_zoom_index.json` :

```powershell
python Core\run_lab_m1_episode_merger_v72_once.py --latest --pretty
```

Sur un run précis :

```powershell
python Core\run_lab_m1_episode_merger_v72_once.py `
  --lab-run output\lab_runs\20260510_145729_GBPUSD_0900_1100 `
  --pretty
```

## Réglage de fusion

```powershell
python Core\run_lab_m1_episode_merger_v72_once.py --latest --merge-gap-minutes 10 --pretty
```

Règle :

```text
Si deux zooms se chevauchent ou sont séparés de moins de N minutes,
ils deviennent un seul épisode.
```

## Lecture

Ouvrir :

```text
lab_report_m1_episodes.html
film_m1_episodes.md
m1_episodes.json
```

## Commit

```powershell
git add Core\pf_lab_m1_episode_merger_v72.py Core\run_lab_m1_episode_merger_v72_once.py scripts\validate_lab_m1_episode_merger_v72.ps1 README_LAB_M1_EPISODE_MERGER_V72.md

git commit -m "Lab: add V7.2 M1 episode merger"

git push origin main
```
