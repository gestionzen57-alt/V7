# T0111 — B9 Sequence Summarizer Native Retest Source Fields — Report

## Résumé

T0111 intègre les champs retest source nativement dans le summarizer B9
(`pf_t009_sequence_summarizer.py`), au lieu de les reconstruire après coup
dans T0110 (`pf_t009_raw_calibration.py`).

## Chaîne B9 active

```
T0107  Natural Flow Reading
T0107A Gappy threshold hotfix
T0108  Natural Retest + FLOW_MIXED split
T0108A Metadata compatibility
T0109  Retest Source Signals
T0110  Retest Source Fields
T0110B Legacy metadata compatibility
T0111  Sequence Summarizer Native Retest Source Fields  ← NEW
```

## Runtime output

```
pf_t009_sequence_summarizer VERSION = V3.2.0_T0111
retest_source_fields_version = T0111_NATIVE_RETEST_SOURCE_FIELDS_V0
```

## Fichiers modifiés

| Fichier | Changement |
|---------|-----------|
| `Core/pf_t009_sequence_summarizer.py` | Version bump V3.2.0_T0111, import T0111 helper, enrichissement natif post-build_moments, validate_summary_contract étendu, markdown enrichi |
| `Core/run_t009_sequence_summarizer_once.py` | Bannière version mise à jour |
| `pf_t009_raw_calibration.py` | T0110 passthrough : si `retest_source_fields_version` commence par `T0111`, les champs natifs sont préservés, T0110 ne complète que les champs manquants |
| `pf_t0111_native_retest_source_fields.py` | Déjà en place via scaffold (inchangé) |

## Fichiers créés

| Fichier | Rôle |
|---------|------|
| `tests/test_t0111_sequence_summarizer_native_retest_source_fields.py` | 11 tests d'intégration |
| `Docs/Reports/T0111_B9_SEQUENCE_SUMMARIZER_NATIVE_RETEST_SOURCE_FIELDS_REPORT.md` | Ce rapport |
| `Docs/Contracts/B9_SEQUENCE_SUMMARIZER_NATIVE_RETEST_SOURCE_FIELDS_V0_CONTRACT.md` | Contrat champs |

## Champs T0111 émis nativement par le summarizer

```
retest_source_fields_version   = T0111_NATIVE_RETEST_SOURCE_FIELDS_V0
retest_touch_count             = int (0 si aucun retest visible)
retest_first_touch_time        = ISO8601 ou null
retest_last_touch_time         = ISO8601 ou null
retest_delay_seconds           = float ou null
retest_acceptance_dwell_seconds = float ou null (uniquement si ACCEPTED)
retest_rejection_speed_pips_per_min = float ou null (uniquement si REJECTED)
retest_zone_distance_pips      = float ou null
retest_outcome_hint            = enum RETEST_OUTCOME_*
retest_source_field_confidence = enum RETEST_SOURCE_FIELDS_*
retest_source_fields_limits    = list[str]
```

## Relation T0110 ↔ T0111

T0110 agit maintenant en mode passthrough quand le moment arrive déjà enrichi
par T0111 (`retest_source_fields_version.startswith("T0111")`).

Règle :
- T0110 ne ré-écrase jamais un champ non-null posé par T0111
- T0110 peut compléter les champs laissés à null par T0111
- Le `retest_source_fields_version` reste `T0111_...` dans le moment final

## zone_memory

Le helper T0111 enrichit `zone_memory` avec :
- `touch_count` (si absent)
- `last_tested` (si absent)
- `retest_status` (si absent et outcome != NOT_VISIBLE)

## Tests

```
tests/test_t0111_native_retest_source_fields.py              7 passed
tests/test_t0111_sequence_summarizer_native_retest_source_fields.py  11 passed
tests/test_t0107_*                                           10 passed
tests/test_t0108_*                                            8 passed
tests/test_t0109_*                                            7 passed
tests/test_t0110_*                                           14 passed
                                                     TOTAL  57 passed
```

## Contraintes respectées

- Read-only DB
- Aucune écriture powerflow.db
- Aucune écriture tick_archive.db
- Aucun dashboard
- Aucun Telegram
- Aucun BUY/SELL
- Aucune dépendance Temporalité externe
- Aucun claim de volume Forex global

## Doctrine

B9 ne doit pas deviner le retest après coup si le summarizer peut l'exposer
dès la scène source.
