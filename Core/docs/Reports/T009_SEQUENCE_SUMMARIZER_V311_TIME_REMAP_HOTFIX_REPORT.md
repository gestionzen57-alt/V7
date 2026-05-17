# T009_SEQUENCE_SUMMARIZER_V3.1.1_TIME_REMAP_HOTFIX_REPORT

## Objet

Patch court V3.1.1 pour corriger uniquement le remap horaire des exports B9 Sequence Summarizer quand `--replay-report` est fourni.

## Branche

```text
fix/t009-sequence-summarizer-v31-time-remap-hotfix
```

## Base

```text
commit V3.1 sécurisé : 54b57c1
branche sécurité : fix/t009-sequence-summarizer-v31-local-54b57c1
```

## Problème corrigé

V3.1 construisait correctement les objets enrichis :

```text
source_profile
zone_memory
parent_scene
center_path
effort_role
retest_status
memory_state
```

Mais les exports JSON/Markdown pouvaient garder les timestamps `shifted/replay`.
Exemple observé : fenêtre `1000_1100` affichée en `22:xx UTC` au lieu de `10:xx UTC` le `2026-05-15`.

## Correction V3.1.1

Quand `--replay-report` est fourni, le module lit :

```text
shifted_start_utc
original_start_utc
```

Puis calcule :

```text
shift_delta = shifted_start_utc - original_start_utc
original_ts = shifted_ts - shift_delta
```

Le remap est appliqué au niveau du résumé exporté, juste avant écriture JSON/Markdown, pour ne modifier ni les scores, ni les labels, ni les classifications, ni les zones.

## Champs remappés

- `moment.time_start`
- `moment.time_end`
- `zone_memory.first_seen`
- `zone_memory.last_seen`
- `zone_memory.last_tested`
- tout champ temps connu dans les objets imbriqués si présent

## Robustesse replay report

Le parser accepte les structures :

```text
shifted_start_utc
original_start_utc
replay.shifted_start_utc
replay.original_start_utc
time_remap.shifted_start_utc
time_remap.original_start_utc
metadata.shifted_start_utc
metadata.original_start_utc
sequence.shifted_start_utc
sequence.original_start_utc
window.shifted_start_utc
window.original_start_utc
```

Il recherche aussi récursivement les deux clés si le rapport est encapsulé.

## Tests ajoutés

```text
test_cli_replay_report_remaps_exported_json_moment_times_real_pack
test_cli_replay_report_remaps_exported_markdown_times_real_pack
test_no_shifted_dates_remain_when_replay_report_is_provided
```

## Validation

```powershell
python -m py_compile Core/pf_t009_sequence_summarizer.py Core/run_t009_sequence_summarizer_once.py
python -m pytest Core/tests/test_t009_sequence_summarizer_v0.py -v
```

Résultat local :

```text
44 passed
```

## Non-régression terrain

- 10:00–10:23 reste une vague progressive.
- 11:00–12:00 reste splitté en plusieurs moments.
- `M1_BAR_PROXY` reste une lecture reconstruite prudente.
- Les limites source restent visibles.
- Aucun score, label, moment, scène ou zone n'est reclassifié par ce patch.

## Contraintes respectées

```text
read-only
aucune DB modifiée
aucun moteur
aucun Telegram
aucun dashboard
aucun B8
aucun BUY/SELL
aucun langage décisionnel
```

## Phrase de cap

```text
Ne corrige pas la scène.
Corrige seulement l'horloge de la scène.
```
