# PowerFlow V7.2 — Lab TF Profiles V0.3

## Objectif

Ajouter une lecture par profils de timeframes et contrôler M1.

## Profils

```text
HTF = W / D / H4       = 10080,1440,240
MTF = H1 / M30 / M15   = 60,30,15
LTF = M15 / M5 / M1    = 15,5,1
FULL = all major TFs
```

M15 est une charnière :
- MTF : battle window
- LTF : contexte supérieur du microfilm

## Modes M1

```text
--m1 off
  M1 retiré du film principal.

--m1 full
  M1 inclus partout.

--m1 zoom
  M1 retiré du film principal,
  puis zoom M1 généré autour des key moments.
```

Doctrine :

```text
M1 n’est pas du bruit.
M1 est le microscope.
Mais le microscope ne doit pas remplacer la carte du champ.
```

## Validation

```powershell
.\scripts\validate_lab_tf_profiles_v72.ps1
```

## Utilisation recommandée

### 1. Lecture principale MTF sans M1

```powershell
python Core\run_lab_profile_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tf-profile MTF `
  --m1 off `
  --pretty
```

### 2. Zoom tactique LTF avec M1 isolé

```powershell
python Core\run_lab_profile_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tf-profile LTF `
  --m1 zoom `
  --max-m1-zooms 5 `
  --pretty
```

### 3. Microfilm complet LTF avec M1 partout

```powershell
python Core\run_lab_profile_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tf-profile LTF `
  --m1 full `
  --pretty
```

## Sorties ajoutées

Dans le run principal :

```text
lab_profile_summary.json
```

Si `--m1 zoom` :

```text
m1_zoom_index.json
film_m1_zoom.md
m1_zoom_runs/lab_runs/<zoom_run_id>/
```

Le run principal contient aussi les sorties V0.1/V0.2 :

```text
lab_report.html
lab_report_key_events.html
film_behavioral.md
film_key_events.md
key_events.csv
```

## Commit

```powershell
git add Core\pf_lab_tf_profiles_v72.py Core\run_lab_profile_v72_once.py scripts\validate_lab_tf_profiles_v72.ps1 README_LAB_TF_PROFILES_V72.md
git commit -m "Lab: add V7.2 timeframe profiles and M1 zoom mode"
git push origin main
```
