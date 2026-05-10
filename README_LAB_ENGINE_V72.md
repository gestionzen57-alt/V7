# PowerFlow V7.2 — Lab Engine

## Rôle

Le Lab Engine V7.2 rejoue une séquence historique depuis `powerflow.db` en read-only, enrichit les frames avec une lecture PowerFlow V7.2, détecte les scènes, mesure causes / conséquences, puis produit un dossier de lab complet.

Il remplace l’ancien duo `lab_replay.py` / `lab_film.py` comme point d’entrée moderne.

## Doctrine

- Pas de BUY/SELL.
- Pas de décision trade.
- Pas de filtrage.
- Pas d’écriture dans `powerflow.db`.
- Ne dépend pas de `pf_flow_nodes.py` car ce module est legacy/write-aware.
- Les footprints institutionnels sont des candidats, jamais des certitudes.

## Fichiers

- `Core/pf_lab_engine_v72.py`
- `Core/run_lab_engine_v72_once.py`
- `scripts/validate_lab_engine_v72.ps1`

## Validation

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
.\scripts\validate_lab_engine_v72.ps1
```

Le self-test crée une DB synthétique dans `output/lab_engine_v72_selftest.db`, puis produit un run complet dans :

```text
output/lab_runs/<run_id>/
```

## Utilisation sur DB réelle

```powershell
python Core\run_lab_engine_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tfs 1,5,15,30,60 `
  --pretty
```

## Sorties

Chaque run crée :

```text
output/lab_runs/<run_id>/replay_raw.json
output/lab_runs/<run_id>/replay_enriched.json
output/lab_runs/<run_id>/scene_timeline.json
output/lab_runs/<run_id>/cause_consequence.json
output/lab_runs/<run_id>/lab_metrics.json
output/lab_runs/<run_id>/film_behavioral.md
output/lab_runs/<run_id>/lab_report.md
output/lab_runs/<run_id>/lab_report.html
```

## Lecture recommandée

Ouvrir d’abord :

```text
lab_report.html
```

Puis :

```text
film_behavioral.md
cause_consequence.json
lab_metrics.json
```

## Ce que mesure la V0.1

- Replay raw par minute / timeframe.
- Force diff base - quote.
- B1 régime proxy.
- B3 angle/speed/noise proxy.
- B4 cycle compression proxy.
- B5 Spearman relation proxy.
- EIE z-score proxy.
- B7 resonance proxy.
- Scene Registry si disponible.
- Structural Flow Footprint Candidate.
- Cause window -15m.
- Consequence window +N bars.
- Outcome observé via force_diff proxy.

## Limites V0.1

- Les métriques enrichies sont des proxies si les runners B1/B3/B4/B5/B7 complets ne sont pas rejoués par frame.
- B4 Wavelet n’est pas recalculé frame par frame en V0.1.
- HMM n’est pas recalculé frame par frame en V0.1.
- EIE complet est approximé par z-score force_diff.
- Les footprints restent `INFERENCE_ONLY`.

Ces limites sont exposées dans `technical_risks`.

## Commit

```powershell
git add Core\pf_lab_engine_v72.py Core\run_lab_engine_v72_once.py scripts\validate_lab_engine_v72.ps1 README_LAB_ENGINE_V72.md
git commit -m "Lab: add V7.2 replay and cause-consequence engine"
git push origin main
```
