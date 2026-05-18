# B9 MARKET COMPARE BOARD V0

Doctrine: comparer n est pas predire. B9 montre la proximite terrain, les ecarts et les risques techniques.

## Scene actuelle

- symbol: GBPUSD
- timestamp: 2026-05-18T09:15:00Z
- current_scene: LOWER_ZONE_RANGE_ACTIVE_WITH_COUNTER_BREATH_RETEST
- memory_family: LOWER_LOCK_COUNTER_BREATH_FAMILY
- source_quality: PARTIAL_RAW_PROXY_MEMORY_MIXED
- retest: RETEST_PENDING
- session: LONDON_IGNITION
- center_path: CENTER_OF_GRAVITY_STILL_LOW

## Top films proches

| rank | type | source | score compare | marqueurs communs | frontiere |
|---:|---|---|---:|---|---|
| 1 | B6_MEMORY_FILM | counter-breath rejected after lower acceptance | 0.2589 | breath / center_path / counter / lower / lower_lock_counter_breath_family / retest / session / source_quality | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |
| 2 | B6_MEMORY_FILM | lower lock then counter-breath pressure | 0.2504 | breath / counter / london_ignition / lower / lower_lock_counter_breath_family / retest / retest_pending / source_quality | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |
| 3 | B6_MEMORY_FILM | lower zone range with rejected counter-breath | 0.2291 | breath / center_path / counter / lower / session / source_quality / zone | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |
| 4 | GOLDEN_TERRAIN_CASE | Lower lock counter-breath rejected | 0.0974 | breath / center_path / corrective / counter / lower / lower_lock_counter_breath_family / release / retest / session / source_quality | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |
| 5 | B6_MEMORY_FILM | counter-breath mistaken as release | 0.0634 | breath / counter / lower_lock_counter_breath_family / release / retest_pending / source_quality | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |
| 6 | GOLDEN_TERRAIN_CASE | Pullback absorbed after validated release | 0.0469 | center_path / comme / release / session / source_quality | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |
| 7 | GOLDEN_TERRAIN_CASE | Proxy only reading partial | 0.0390 | center_path / proxy / session / source_quality | COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION |

## Golden terrain proche

- Lower lock counter-breath rejected (GT_001)
- score compare: 0.0974
- similarites: breath | center_path | corrective | counter | lower | lower_lock_counter_breath_family | release | retest | session | source_quality
- differences reference absentes: case_id | case_label | center_low | center_stays_low | confondre | counter_breath | failed_reintegration | family | golden_cases_csv | gt_001 | lock | london

## Differences clefs

- REFERENCE_MARKER_ABSENT_FROM_CURRENT: acceptance | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent
- REFERENCE_MARKER_ABSENT_FROM_CURRENT: after | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent
- REFERENCE_MARKER_ABSENT_FROM_CURRENT: b6_20260513_counter_breath_rejected_second_leg_down | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent
- REFERENCE_MARKER_ABSENT_FROM_CURRENT: center_low | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent
- REFERENCE_MARKER_ABSENT_FROM_CURRENT: center_stays_low | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent
- CURRENT_MARKER_ABSENT_FROM_REFERENCE: absorption | impact: Scene actuelle partiellement hors film reference | risque: comparaison incomplete
- CURRENT_MARKER_ABSENT_FROM_REFERENCE: acceptation | impact: Scene actuelle partiellement hors film reference | risque: comparaison incomplete
- CURRENT_MARKER_ABSENT_FROM_REFERENCE: cannot | impact: Scene actuelle partiellement hors film reference | risque: comparaison incomplete
- CURRENT_MARKER_ABSENT_FROM_REFERENCE: cannot_conclude | impact: Scene actuelle partiellement hors film reference | risque: comparaison incomplete
- CURRENT_MARKER_ABSENT_FROM_REFERENCE: center_of_gravity_still_low | impact: Scene actuelle partiellement hors film reference | risque: comparaison incomplete
- REFERENCE_MARKER_ABSENT_FROM_CURRENT: center_low | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent
- REFERENCE_MARKER_ABSENT_FROM_CURRENT: center_of_gravity_low | impact: Ne pas sur-lire la proximite memoire | risque: film proche mais marqueur terrain absent

## Pieges techniques

- counter-breath ne doit pas etre lu comme release
- absorption inverse possible si lower zone reste defendue
- vague inverse potentiellement corrective
- source proxy ne valide pas une phase

## Risques techniques board

- [P1] SOURCE_QUALITY_LIMIT: PARTIAL_RAW_PROXY_MEMORY_MIXED -> Source quality limitee: B9 garde la conclusion courte.
- [P1] PROXY_SOURCE_PRESENT: proxy marker detected -> Source proxy: comparer la forme, pas conclure le film dur.

## Ce que B9 ne peut pas conclure

- direction finale
- outcome du retest
- force dure sans raw complet
- raw nuance le film mais ne tranche pas le retest
- proxy memory cannot confirm current source
