# POWERFLOW GBPUSD FILM LIBRARY QA V7.6

Ces tests valident que les 7 films calibrés GBPUSD sont reconnus comme séquences terrain et non comme signaux de trading.

## QA doctrine

- La QA teste une requalification de film.
- La QA ne produit jamais d'ordre.
- Le prix arbitre toujours la validation ou l'invalidation.
- Une visibilité data faible doit sortir explicitement en `READING_PARTIAL` / `DEGRADED`.

## QA-FILM-20260506

- input pattern: `LOW_ZONE_BUILDING -> RELEASE_UP_VALIDATED -> HIGH_ZONE_EXHAUSTION -> POST_RELEASE_UNWIND`
- expected film_state: `HIGH_ZONE_EXHAUSTION_AFTER_RELEASE_UP`
- expected last_structural_event: `RELEASE_UP_VALIDATED_THEN_HIGH_ZONE_EXHAUSTION`
- expected qualified_bias: `RELEASE_UP_VALIDATED`, `HIGH_ZONE_EXHAUSTION`, `UP_CONSUMED`, `POST_RELEASE_UNWIND`
- expected packet_quality: `FRESH_WHEN_PRICE_ACCEPTS_UP_THEN_CONSUMED_AFTER_HIGH_ZONE`
- expected price_confirmation: UP accepted while price holds/extends; late UP invalidated if high zone rejects or no further acceptance
- expected data_visibility: Data must expose price acceptance, zone transition and propagation before release validation.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data

## QA-FILM-20260507

- input pattern: `POST_RELEASE_REBUILD -> LATE_UP_EXTENSION -> HIGH_ZONE_REJECTION -> DEEP_POST_HIGH_UNWIND`
- expected film_state: `POST_HIGH_UNWIND_AFTER_LATE_HIGH_REJECTION`
- expected last_structural_event: `HIGH_ZONE_REJECTION`
- expected qualified_bias: `HIGH_ZONE_REJECTION`, `POST_HIGH_UNWIND`, `DEEP_POST_HIGH_UNWIND`
- expected packet_quality: `DOWN_PACKET_VALID_AS_UNWIND_ONLY_AFTER_HIGH_REJECTION_AND_PRICE_CONFIRMATION`
- expected price_confirmation: High rejected; downside accepted by lower closes / unwind continuation.
- expected data_visibility: Need enough price and zone visibility to distinguish rejection from normal pullback.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data

## QA-FILM-20260508

- input pattern: `LOW_ZONE_REBUILD -> RELEASE_UP_VALIDATED -> PULLBACK_ABSORBED -> CONTINUATION_UP -> CLOSE_NEAR_HIGH`
- expected film_state: `RELEASE_UP_ACCEPTED_CONTINUATION`
- expected last_structural_event: `RELEASE_UP_VALIDATED`
- expected qualified_bias: `RELEASE_UP_VALIDATED`, `PULLBACK_ABSORBED`, `UP_CONTINUATION_ACCEPTED`, `CLOSE_NEAR_HIGH`
- expected packet_quality: `HIGH_QUALITY_WHEN_PULLBACK_ABSORBED_AND_CLOSE_REMAINS_NEAR_HIGH`
- expected price_confirmation: Higher acceptance; pullback fails to invalidate; close near high validates continuation.
- expected data_visibility: Requires price acceptance plus propagation; no release validation from B3+B4+P1 alone.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data

## QA-FILM-20260511

- input pattern: `PRE_LONDON_FALSE_BIRTHS -> MIDDAY_RELEASE_UP -> POST_RELEASE_PULLBACK -> SECOND_LEG_UP -> HIGH_ZONE_EXHAUSTION -> LATE_UNWIND`
- expected film_state: `COMPRESSION_RELEASE_SECOND_LEG_EXHAUSTION`
- expected last_structural_event: `SECOND_LEG_UP_THEN_HIGH_ZONE_EXHAUSTION`
- expected qualified_bias: `EVENT_STACK`, `FALSE_BIRTH`, `RELEASE_UP_VALIDATED`, `POST_RELEASE_PULLBACK`, `SECOND_LEG_UP`, `HIGH_ZONE_EXHAUSTION`
- expected packet_quality: `B3+B2_ONLY_EVENT_STACK; RELEASE_ONLY_AFTER_B4_P1_PRICE_B7; LATE_SECOND_LEG_CONSUMED`
- expected price_confirmation: False births invalidated before London; later release requires acceptance; exhaustion after high zone consumes UP.
- expected data_visibility: Need pre-London segmentation; session context matters; false births must stay labelled.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data

## QA-FILM-20260512

- input pattern: `ASIA_HIGH_FAILURE -> LONDON_RELEASE_DOWN -> LOWER_PRICE_ACCEPTANCE -> POST_RELEASE_COUNTER_BREATH -> SECOND_LOW_TEST -> LATE_COUNTER_BOUNCE`
- expected film_state: `RELEASE_DOWN_LOWER_LOCK_COUNTER_BREATH`
- expected last_structural_event: `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK`
- expected qualified_bias: `RELEASE_DOWN_VALIDATED`, `LOWER_LOCK`, `COUNTER_BREATH_UP`, `SECOND_LOW_TEST`, `LATE_COUNTER_BOUNCE`
- expected packet_quality: `PAIR_UP_AFTER_RELEASE_DOWN_REACTION_NOT_NEW_RELEASE_UNLESS_PRICE_REINTEGRATES`
- expected price_confirmation: Lower acceptance confirms down; PAIR_UP remains counter-breath until reintegration is accepted.
- expected data_visibility: Must preserve last_structural_event; without it PAIR_UP becomes misleading.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data

## QA-FILM-20260513

- input pattern: `POST_RELEASE_LOWER_ACCEPTANCE -> LONDON_COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> SECOND_LEG_DOWN -> LOWER_LOW -> POST_LOW_COUNTER_BREATH -> LATE_THIN_BOUNCE`
- expected film_state: `COUNTER_BREATH_REJECTED_SECOND_LEG_DOWN`
- expected last_structural_event: `COUNTER_BREATH_REJECTED`
- expected qualified_bias: `COUNTER_BREATH_UP`, `COUNTER_BREATH_REJECTED`, `SECOND_LEG_DOWN`, `LOWER_LOW`, `POST_LOW_COUNTER_BREATH`, `LATE_THIN_BOUNCE`
- expected packet_quality: `DOWN_AFTER_COUNTER_BREATH_REJECTED_QUALIFIES_AS_SECOND_LEG_DOWN_IF_PRICE_BREAKS_LOWER`
- expected price_confirmation: Counter-breath fails; lower acceptance / lower low confirms second leg down.
- expected data_visibility: Need price arbitration and last structural state; data weakness should degrade confidence.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data

## QA-FILM-20260514

- input pattern: `LOWER_ZONE_RANGE_ACTIVE -> COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> LOW_RETEST -> POST_LOW_REACTION`
- expected film_state: `LOWER_ZONE_RANGE_READING_PARTIAL`
- expected last_structural_event: `COUNTER_BREATH_REJECTED_IN_LOWER_ZONE_RANGE`
- expected qualified_bias: `LOWER_ZONE_RANGE_ACTIVE`, `COUNTER_BREATH_UP`, `COUNTER_BREATH_REJECTED`, `LOW_RETEST`, `POST_LOW_REACTION`, `READING_PARTIAL`
- expected packet_quality: `DEGRADED_WHEN_M1_MISSING_OR_PACKETS_STALE; OUTPUT_READING_PARTIAL_VISIBLE`
- expected price_confirmation: Pending unless lower-zone break or reintegration acceptance; stale data prevents hard validation.
- expected data_visibility: READING_PARTIAL / MICROFILM_MISSING / PACKETS_STALE must be visible at top of packet.
- must_not_output:
  - `BUY`
  - `SELL`
  - `ENTRY`
  - `EXIT`
  - `TARGET`
  - `STOP`
  - `PAIR_UP` or `PAIR_DOWN` without contextual requalification
  - `RELEASE_VALIDATED` without price + zone + propagation + acceptable data
