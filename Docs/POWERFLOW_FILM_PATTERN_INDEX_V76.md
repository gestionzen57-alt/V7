# POWERFLOW FILM PATTERN INDEX V7.6

Cet index relie les films calibrés GBPUSD aux patterns récurrents que B6 et la QA doivent reconnaître.

| PATTERN_ID | FILM_PATTERN | SEEN_ON_DATES | RAW_SIGNAL_RISK | EXPECTED_REQUALIFICATION | QA_CASES |
|---|---|---|---|---|---|
| `FP-001` | `RELEASE_CANDIDATE_VALIDATED` | 2026-05-06, 2026-05-08, 2026-05-11 | B3+B4+P1 without price | `RELEASE_VALIDATED only if price + zone + B7 confirm` | QA-FILM-20260506, QA-FILM-20260508, QA-FILM-20260511 |
| `FP-002` | `FALSE_BIRTH_EVENT_STACK` | 2026-05-11 | B3+B2 over-nervous | `EVENT_STACK / FALSE_BIRTH` | QA-FILM-20260511 |
| `FP-003` | `HIGH_ZONE_REJECTION` | 2026-05-06, 2026-05-07, 2026-05-11 | PAIR_UP late after high | `HIGH_ZONE_REJECTION / EXHAUSTION / CONSUMED` | QA-FILM-20260506, QA-FILM-20260507, QA-FILM-20260511 |
| `FP-004` | `LOWER_LOCK` | 2026-05-12, 2026-05-13 | PAIR_UP after release down | `LOWER_LOCK then COUNTER_BREATH_UP unless reintegration accepted` | QA-FILM-20260512, QA-FILM-20260513 |
| `FP-005` | `COUNTER_BREATH` | 2026-05-12, 2026-05-13, 2026-05-14 | Reverse raw bias treated as new phase | `COUNTER_BREATH / POST_LOW_REACTION` | QA-FILM-20260512, QA-FILM-20260513, QA-FILM-20260514 |
| `FP-006` | `COUNTER_BREATH_REJECTED` | 2026-05-13, 2026-05-14 | Failed reaction ignored | `COUNTER_BREATH_REJECTED` | QA-FILM-20260513, QA-FILM-20260514 |
| `FP-007` | `SECOND_LEG` | 2026-05-11, 2026-05-13 | PAIR_UP/PAIR_DOWN generic after pullback/rejection | `SECOND_LEG_UP / SECOND_LEG_DOWN` | QA-FILM-20260511, QA-FILM-20260513 |
| `FP-008` | `PULLBACK_ABSORBED` | 2026-05-08, 2026-05-11 | Post-release pullback misread as reversal | `PULLBACK_ABSORBED` | QA-FILM-20260508, QA-FILM-20260511 |
| `FP-009` | `LATE_THIN_BOUNCE` | 2026-05-12, 2026-05-13 | Late bounce overvalidated | `LATE_THIN_BOUNCE` | QA-FILM-20260512, QA-FILM-20260513 |
| `FP-010` | `EXHAUSTION_CONSUMED` | 2026-05-06, 2026-05-11 | HOT/PAIR_UP after extension | `EXHAUSTION / CONSUMED / EXHAUSTION_RISK` | QA-FILM-20260506, QA-FILM-20260511 |
| `FP-011` | `READING_PARTIAL` | 2026-05-14 | Stale packet or M1 missing treated as normal | `READING_PARTIAL / DEGRADED` | QA-FILM-20260514 |

## Notes d'indexation

- Un pattern peut apparaître dans plusieurs films avec un rôle différent.
- L'index ne remplace pas la film card : il accélère le matching B6.
- `RAW_SIGNAL_RISK` décrit le piège du signal brut.
- `EXPECTED_REQUALIFICATION` décrit le nom terrain attendu dans `terrain_packet_v76_0`.
- `QA_CASES` indique les cas de validation minimaux.
