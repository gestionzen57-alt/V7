# T009 Sequence Summarizer V3.1 — Replay Time & Parent Scenes

**Branche :** `fix/t009-sequence-summarizer-v31-replay-time-and-parent-scenes`  
**Nature :** patch court V3.1, pas V4  
**Statut :** prêt pour installation / validation locale  
**Commit proposé :** `fix(t009): add B9 V3.1 replay time and parent scenes`

---

## 1. Objectif

V3.1 corrige les dernières limites terrain du Sequence Summarizer après validation London.

Le cap reste :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
```

Phrase de contrôle du patch :

```text
Ne juge pas seulement le début et la fin.
Lis le chemin du centre dans le groupe.
```

---

## 2. Corrections apportées

### 2.1 Timestamps replay corrigés

Le module continue de préférer :

```text
evidence.L1_raw.first_ts_utc
```

puis fallback :

```text
timestamp / ts_utc
```

Le CLI accepte aussi :

```text
--replay-report
```

pour remapper :

```text
shifted_start_utc -> original_start_utc
```

Le test `test_cli_replay_report_remaps_exported_moment_times` valide que le JSON et le Markdown exportés utilisent l’heure originale.

### 2.2 `source_profile` obligatoire

Chaque summary et chaque moment exposent maintenant :

```json
{
  "source_mode": "M1_BAR_PROXY",
  "data_visibility": "RECONSTRUCTED",
  "confidence_cap": 0.35,
  "quality": "PROXY_CAUTION",
  "language_fr": "Lecture reconstruite M1_BAR_PROXY...",
  "limitations": []
}
```

But : empêcher toute confusion entre `M1_BAR_PROXY` et footprint raw tick complet.

### 2.3 Moment B9 enrichi

Chaque moment expose maintenant :

```text
center_min
center_max
center_range_pips
center_path
max_favorable_excursion_pips
max_adverse_excursion_pips
effort_role
retest_status
memory_state
```

`center_path` permet de lire le trajet interne, pas seulement `center_start -> center_end`.

### 2.4 `zone_memory` minimal read-only

Chaque moment contient un objet minimal :

```json
{
  "zone_low": 0.0,
  "zone_high": 0.0,
  "zone_center_start": 0.0,
  "zone_center_end": 0.0,
  "state": "LOCAL_MEMORY_ACTIVE",
  "event_count": 0,
  "source_mode": "M1_BAR_PROXY",
  "data_visibility": "RECONSTRUCTED",
  "confidence_cap": 0.35
}
```

C’est une mémoire de lecture locale, non persistée en DB.

### 2.5 `parent_scene` read-only

Chaque moment est relié à un parent scene minimal :

```text
base -> réaction -> projection -> jugement
```

Objet :

```json
{
  "scene_id": "B9SESSION-001",
  "model": "base -> réaction -> projection -> jugement",
  "base_fr": "zone de mémoire locale",
  "reaction_fr": "réaction du centre et du chemin interne",
  "projection_fr": "extension ou respiration mesurée par le centre",
  "judgment_fr": "jugement par retest ou par absence de progrès durable",
  "read_only": true
}
```

### 2.6 Langage source-aware M1 proxy

Le Markdown affiche maintenant explicitement :

```text
Lecture reconstruite M1_BAR_PROXY : utile pour scène, centre et effort/résultat ; pas un footprint raw tick complet.
```

### 2.7 Non-régression terrain

Tests ajoutés :

```text
test_london_1000_1023_progressive_wave_preserved_v31
test_london_11_12_split_preserved_v31
```

Ils valident :

```text
10:00–10:23 reste vague progressive.
11:00–12:00 reste splitté en plusieurs moments.
```

---

## 3. Tests ajoutés V3.1

```text
test_cli_replay_report_remaps_exported_moment_times
test_parent_scene_base_reaction_projection_judgment_v31
test_zone_memory_object_minimal_fields_v31
test_effort_role_fuel_brake_absorption_v31
test_retest_status_pending_failed_accepted_v31
test_source_profile_is_mandatory_and_cautious_for_m1_proxy
test_no_decision_language_in_export_v31
test_no_db_write_no_telegram_dashboard_b8_imports_v31
test_london_11_12_split_preserved_v31
test_london_1000_1023_progressive_wave_preserved_v31
```

---

## 4. Validation locale

Commandes :

```powershell
python -m py_compile Core/pf_t009_sequence_summarizer.py Core/run_t009_sequence_summarizer_once.py
python -m pytest Core/tests/test_t009_sequence_summarizer_v0.py -v
```

Résultat local :

```text
41 passed
```

---

## 5. Contraintes respectées

```text
read-only
aucune DB modifiée
aucun moteur modifié
aucune surface externe
aucun langage décisionnel
aucune fusion B8 prématurée
M1 proxy formulé comme lecture reconstruite
source quality visible
limites visibles
```

---

## 6. Limite volontaire

V3.1 ne crée pas de V4.

Il ajoute uniquement les objets nécessaires pour stabiliser le replay time, la mémoire locale, le parent scene et la lecture source-aware.

Le prochain vrai saut serait une V4 seulement après validation sur plusieurs journées replay.
