# T009 Sequence Summarizer — Patch V0.1 London Validation Hotfix

## Objectif

Corriger les écarts observés sur la validation London 08:00–12:00 : timestamps historiques, lecture du chemin interne du centre, progression suivie de retracement, split des grands groupes et labels français accentués.

Phrase de cap :

```text
Ne juge pas seulement le début et la fin. Lis le chemin du centre dans le groupe.
```

## Corrections livrées

### 1. Timestamps historiques

Le normaliseur préfère maintenant :

```text
evidence.L1_raw.first_ts_utc
```

Fallback :

```text
ts_utc / timestamp / time / created_at / bucket.timestamp
```

Le CLI accepte aussi :

```powershell
--replay-report replay_report.json
```

Ce fichier peut contenir :

```json
{
  "shifted_start_utc": "2026-05-16T23:11:00Z",
  "original_start_utc": "2026-05-15T08:00:00Z"
}
```

Le remap n'est appliqué qu'aux timestamps replay/top-level lorsque `evidence.L1_raw.first_ts_utc` n'est pas disponible.

### 2. Chemin interne du centre

Chaque moment expose maintenant :

```text
center_min
center_max
center_range_pips
max_favorable_excursion_pips
max_adverse_excursion_pips
```

La classification ne juge plus uniquement `center_start -> center_end`.

### 3. Progression suivie de retracement

Une progression forte puis un retracement ne doit plus être classée automatiquement en `T009_MOMENT_EFFORT_WITHOUT_RESULT` quand le net final est faible.

La règle V0.1 :

```text
si le chemin interne montre une excursion favorable forte,
ne pas écraser la scène en effort sans résultat.
```

### 4. Split d'inflexion

Le regroupement initial est maintenant suivi d'un split si le centre montre :

```text
migration forte -> retracement / stabilisation
```

Objectif London :

```text
11:00–11:31 : Centre de gravité qui descend
11:37–12:00 : Respiration basse / retour partiel sans progrès durable
```

### 5. Français accentué

Labels corrigés :

```text
Centre de gravité qui descend
Effort sans résultat
Vague progressive
Zone de friction locale
```

## Tests ajoutés

```text
test_prefers_l1_raw_first_ts_for_time_start
test_replay_report_time_remap
test_progressive_wave_with_retrace_not_effort_without_result
test_split_large_group_on_center_inflexion
test_french_labels_have_accents
```

## Validation

```powershell
python -m py_compile Core/pf_t009_sequence_summarizer.py Core/run_t009_sequence_summarizer_once.py
python -m pytest Core/tests/test_t009_sequence_summarizer_v0.py -v
```

Résultat attendu :

```text
31 passed
```

## Limites

- V0.1 reste heuristique.
- Le split d'inflexion lit le chemin du centre, pas un footprint raw tick complet.
- `M1_BAR_PROXY` reste une lecture reconstruite.
- `delta proxy` reste une limite visible.
- Aucun moteur, aucune DB, aucun Telegram, aucun dashboard.
