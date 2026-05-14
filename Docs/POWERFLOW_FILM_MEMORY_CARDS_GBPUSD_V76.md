# POWERFLOW FILM MEMORY CARDS GBPUSD V7.6

Ces cartes sont destinées à B6 Memory et à la QA V7.6. Elles ne décrivent pas des ordres. Elles décrivent des films calibrés.

## Film memory card — 2026-05-06

| Field | Value |
|---|---|
| Date | 2026-05-06 |
| Symbol | GBPUSD |
| Film name | `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION` |
| Film state | `HIGH_ZONE_EXHAUSTION_AFTER_RELEASE_UP` |
| Last structural event | `RELEASE_UP_VALIDATED_THEN_HIGH_ZONE_EXHAUSTION` |
| Dominant zone status | `LOW_ZONE_BUILDING_TO_HIGH_ZONE_CONSUMED` |
| Dominant move role | `UP_RELEASE_THEN_LATE_UP_CONSUMED` |
| Raw bias risks | `PAIR_UP_AFTER_HIGH_ALREADY_DONE`, `HOT_AFTER_EXTENSION`, `UP_SIGNAL_CONSUMED` |
| Expected qualified bias | `RELEASE_UP_VALIDATED`, `HIGH_ZONE_EXHAUSTION`, `UP_CONSUMED`, `POST_RELEASE_UNWIND` |
| Packet quality expected | `FRESH_WHEN_PRICE_ACCEPTS_UP_THEN_CONSUMED_AFTER_HIGH_ZONE` |
| Price confirmation expected | UP accepted while price holds/extends; late UP invalidated if high zone rejects or no further acceptance |
| Data visibility notes | Data must expose price acceptance, zone transition and propagation before release validation. |
| Memory signature | `LOW_ZONE_BUILDING -> RELEASE_UP_VALIDATED -> HIGH_ZONE_EXHAUSTION -> POST_RELEASE_UNWIND` |
| False positive risks | `Treating late PAIR_UP as fresh release`, `Ignoring consumed high zone`, `HOT after extension misread as new birth` |
| QA targets | `QA-FILM-20260506`, `QA-PATTERN-EXHAUSTION-CONSUMED`, `QA-PATTERN-RELEASE-VALIDATED` |

## Film memory card — 2026-05-07

| Field | Value |
|---|---|
| Date | 2026-05-07 |
| Symbol | GBPUSD |
| Film name | `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND` |
| Film state | `POST_HIGH_UNWIND_AFTER_LATE_HIGH_REJECTION` |
| Last structural event | `HIGH_ZONE_REJECTION` |
| Dominant zone status | `HIGH_ZONE_REJECTED_LATE_SESSION` |
| Dominant move role | `DEEP_POST_HIGH_UNWIND` |
| Raw bias risks | `PAIR_DOWN_GENERIC`, `LATE_UP_EXTENSION_MISREAD`, `HOT_WITHOUT_ACCEPTANCE` |
| Expected qualified bias | `HIGH_ZONE_REJECTION`, `POST_HIGH_UNWIND`, `DEEP_POST_HIGH_UNWIND` |
| Packet quality expected | `DOWN_PACKET_VALID_AS_UNWIND_ONLY_AFTER_HIGH_REJECTION_AND_PRICE_CONFIRMATION` |
| Price confirmation expected | High rejected; downside accepted by lower closes / unwind continuation. |
| Data visibility notes | Need enough price and zone visibility to distinguish rejection from normal pullback. |
| Memory signature | `POST_RELEASE_REBUILD -> LATE_UP_EXTENSION -> HIGH_ZONE_REJECTION -> DEEP_POST_HIGH_UNWIND` |
| False positive risks | `Calling every PAIR_DOWN fresh release`, `Missing late high rejection`, `Overweighting B3/B2 without price` |
| QA targets | `QA-FILM-20260507`, `QA-PATTERN-HIGH-REJECTION`, `QA-PATTERN-POST-HIGH-UNWIND` |

## Film memory card — 2026-05-08

| Field | Value |
|---|---|
| Date | 2026-05-08 |
| Symbol | GBPUSD |
| Film name | `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH` |
| Film state | `RELEASE_UP_ACCEPTED_CONTINUATION` |
| Last structural event | `RELEASE_UP_VALIDATED` |
| Dominant zone status | `LOW_ZONE_REBUILD_TO_HIGH_ACCEPTANCE` |
| Dominant move role | `UP_CONTINUATION_AFTER_PULLBACK_ABSORBED` |
| Raw bias risks | `PAIR_UP_GENERIC`, `PAIR_DOWN_PULLBACK_MISREAD_AS_REVERSAL`, `HOT_NEEDS_PRICE_ACCEPTANCE` |
| Expected qualified bias | `RELEASE_UP_VALIDATED`, `PULLBACK_ABSORBED`, `UP_CONTINUATION_ACCEPTED`, `CLOSE_NEAR_HIGH` |
| Packet quality expected | `HIGH_QUALITY_WHEN_PULLBACK_ABSORBED_AND_CLOSE_REMAINS_NEAR_HIGH` |
| Price confirmation expected | Higher acceptance; pullback fails to invalidate; close near high validates continuation. |
| Data visibility notes | Requires price acceptance plus propagation; no release validation from B3+B4+P1 alone. |
| Memory signature | `LOW_ZONE_REBUILD -> RELEASE_UP_VALIDATED -> PULLBACK_ABSORBED -> CONTINUATION_UP -> CLOSE_NEAR_HIGH` |
| False positive risks | `Treating pullback as structural reversal`, `Validating release without close/acceptance`, `Ignoring propagation state` |
| QA targets | `QA-FILM-20260508`, `QA-PATTERN-PULLBACK-ABSORBED`, `QA-PATTERN-UP-CONTINUATION-ACCEPTED` |

## Film memory card — 2026-05-11

| Field | Value |
|---|---|
| Date | 2026-05-11 |
| Symbol | GBPUSD |
| Film name | `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION` |
| Film state | `COMPRESSION_RELEASE_SECOND_LEG_EXHAUSTION` |
| Last structural event | `SECOND_LEG_UP_THEN_HIGH_ZONE_EXHAUSTION` |
| Dominant zone status | `COMPRESSION_TO_HIGH_ZONE_CONSUMED` |
| Dominant move role | `RELEASE_UP_THEN_SECOND_LEG_UP_THEN_EXHAUSTION` |
| Raw bias risks | `B3_B2_FALSE_BIRTH`, `EVENT_STACK_MISREAD_AS_BIRTH`, `LATE_UP_AFTER_SECOND_LEG` |
| Expected qualified bias | `EVENT_STACK`, `FALSE_BIRTH`, `RELEASE_UP_VALIDATED`, `POST_RELEASE_PULLBACK`, `SECOND_LEG_UP`, `HIGH_ZONE_EXHAUSTION` |
| Packet quality expected | `B3+B2_ONLY_EVENT_STACK; RELEASE_ONLY_AFTER_B4_P1_PRICE_B7; LATE_SECOND_LEG_CONSUMED` |
| Price confirmation expected | False births invalidated before London; later release requires acceptance; exhaustion after high zone consumes UP. |
| Data visibility notes | Need pre-London segmentation; session context matters; false births must stay labelled. |
| Memory signature | `PRE_LONDON_FALSE_BIRTHS -> MIDDAY_RELEASE_UP -> POST_RELEASE_PULLBACK -> SECOND_LEG_UP -> HIGH_ZONE_EXHAUSTION -> LATE_UNWIND` |
| False positive risks | `B3+B2 over-validation`, `Second leg mistaken for new fresh release`, `Late unwind ignored` |
| QA targets | `QA-FILM-20260511`, `QA-PATTERN-FALSE-BIRTH`, `QA-PATTERN-SECOND-LEG`, `QA-PATTERN-EXHAUSTION-CONSUMED` |

## Film memory card — 2026-05-12

| Field | Value |
|---|---|
| Date | 2026-05-12 |
| Symbol | GBPUSD |
| Film name | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH` |
| Film state | `RELEASE_DOWN_LOWER_LOCK_COUNTER_BREATH` |
| Last structural event | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK` |
| Dominant zone status | `LOWER_ZONE_ACCEPTED_LOCKED` |
| Dominant move role | `DOWN_RELEASE_THEN_COUNTER_BREATH_UP` |
| Raw bias risks | `PAIR_UP_AFTER_RELEASE_DOWN`, `POST_LOW_REACTION_MISREAD_AS_FRESH_UP`, `LATE_COUNTER_BOUNCE` |
| Expected qualified bias | `RELEASE_DOWN_VALIDATED`, `LOWER_LOCK`, `COUNTER_BREATH_UP`, `SECOND_LOW_TEST`, `LATE_COUNTER_BOUNCE` |
| Packet quality expected | `PAIR_UP_AFTER_RELEASE_DOWN_REACTION_NOT_NEW_RELEASE_UNLESS_PRICE_REINTEGRATES` |
| Price confirmation expected | Lower acceptance confirms down; PAIR_UP remains counter-breath until reintegration is accepted. |
| Data visibility notes | Must preserve last_structural_event; without it PAIR_UP becomes misleading. |
| Memory signature | `ASIA_HIGH_FAILURE -> LONDON_RELEASE_DOWN -> LOWER_PRICE_ACCEPTANCE -> POST_RELEASE_COUNTER_BREATH -> SECOND_LOW_TEST -> LATE_COUNTER_BOUNCE` |
| False positive risks | `Calling counter-breath a fresh UP release`, `Forgetting lower lock`, `Missing second low test` |
| QA targets | `QA-FILM-20260512`, `QA-PATTERN-LOWER-LOCK`, `QA-PATTERN-COUNTER-BREATH` |

## Film memory card — 2026-05-13

| Field | Value |
|---|---|
| Date | 2026-05-13 |
| Symbol | GBPUSD |
| Film name | `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN` |
| Film state | `COUNTER_BREATH_REJECTED_SECOND_LEG_DOWN` |
| Last structural event | `COUNTER_BREATH_REJECTED` |
| Dominant zone status | `LOWER_ACCEPTANCE_THEN_LOWER_LOW` |
| Dominant move role | `SECOND_LEG_DOWN_AFTER_REJECTED_COUNTER_BREATH` |
| Raw bias risks | `PAIR_UP_COUNTER_BREATH_MISREAD`, `PAIR_DOWN_GENERIC`, `LOWER_LOW_AFTER_REJECTION_UNQUALIFIED` |
| Expected qualified bias | `COUNTER_BREATH_UP`, `COUNTER_BREATH_REJECTED`, `SECOND_LEG_DOWN`, `LOWER_LOW`, `POST_LOW_COUNTER_BREATH`, `LATE_THIN_BOUNCE` |
| Packet quality expected | `DOWN_AFTER_COUNTER_BREATH_REJECTED_QUALIFIES_AS_SECOND_LEG_DOWN_IF_PRICE_BREAKS_LOWER` |
| Price confirmation expected | Counter-breath fails; lower acceptance / lower low confirms second leg down. |
| Data visibility notes | Need price arbitration and last structural state; data weakness should degrade confidence. |
| Memory signature | `POST_RELEASE_LOWER_ACCEPTANCE -> LONDON_COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> SECOND_LEG_DOWN -> LOWER_LOW -> POST_LOW_COUNTER_BREATH -> LATE_THIN_BOUNCE` |
| False positive risks | `Treating rejected counter-breath as neutral noise`, `Not upgrading to second leg after lower low`, `Late thin bounce overread` |
| QA targets | `QA-FILM-20260513`, `QA-PATTERN-COUNTER-BREATH-REJECTED`, `QA-PATTERN-SECOND-LEG-DOWN` |

## Film memory card — 2026-05-14

| Field | Value |
|---|---|
| Date | 2026-05-14 |
| Symbol | GBPUSD |
| Film name | `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL` |
| Film state | `LOWER_ZONE_RANGE_READING_PARTIAL` |
| Last structural event | `COUNTER_BREATH_REJECTED_IN_LOWER_ZONE_RANGE` |
| Dominant zone status | `LOWER_ZONE_RANGE_ACTIVE` |
| Dominant move role | `POST_LOW_REACTION_AFTER_REJECTED_COUNTER_BREATH` |
| Raw bias risks | `PAIR_UP_IN_LOWER_RANGE`, `STALE_PACKET`, `M1_MISSING`, `HOT_WITH_WEAK_VISIBILITY` |
| Expected qualified bias | `LOWER_ZONE_RANGE_ACTIVE`, `COUNTER_BREATH_UP`, `COUNTER_BREATH_REJECTED`, `LOW_RETEST`, `POST_LOW_REACTION`, `READING_PARTIAL` |
| Packet quality expected | `DEGRADED_WHEN_M1_MISSING_OR_PACKETS_STALE; OUTPUT_READING_PARTIAL_VISIBLE` |
| Price confirmation expected | Pending unless lower-zone break or reintegration acceptance; stale data prevents hard validation. |
| Data visibility notes | READING_PARTIAL / MICROFILM_MISSING / PACKETS_STALE must be visible at top of packet. |
| Memory signature | `LOWER_ZONE_RANGE_ACTIVE -> COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> LOW_RETEST -> POST_LOW_REACTION` |
| False positive risks | `Suppressing data warning`, `Reading PAIR_UP as fresh release despite lower range`, `Over-confirming with stale packet` |
| QA targets | `QA-FILM-20260514`, `QA-PATTERN-READING-PARTIAL`, `QA-PATTERN-LOWER-ZONE-RANGE` |
