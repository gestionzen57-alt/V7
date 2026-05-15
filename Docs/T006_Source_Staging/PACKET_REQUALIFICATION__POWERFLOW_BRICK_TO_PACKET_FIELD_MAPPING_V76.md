# POWERFLOW BRICK TO PACKET FIELD MAPPING V7.6

## 0. Principe

Chaque brique supporte un ou plusieurs champs du `terrain_packet`. Aucune brique ne décide seule du film complet. Les champs critiques doivent être arbitrés par prix, zone, propagation, texture et data visibility.

```text
BRICK SUPPORTS FIELD.
BRICK DOES NOT DECIDE FINAL SEMANTICS ALONE.
```

## 1. Mapping global

| BRICK | SUPPORTS FIELD | DOES NOT DECIDE | REQUIRED CROSSCHECK | FAILURE MODE |
|---|---|---|---|---|
| B2 event stack | `event_stack_state`, `event_density`, `birth_attempt` | `release_validation`, `qualified_bias` | B3, price, zone, B7, data_visibility | `B3_B2_FALSE_BIRTH` |
| B3 detachment / birth attempt | `detachment_state`, `raw_bias`, support `current_move_role` | `RELEASE_VALIDATED`, structural direction | B7+, price confirmation, current_zone, last_structural_event | Directionnel sans prix |
| B4 compression | `compression_state`, `temporal_density`, `pressure_pending` | Release, outcome, trade direction | P1, B3, price, propagation | Compression prise pour cassure |
| P1 energy / elastic load | `energy_state`, `elastic_load`, `freshness_state` | Release validation | B4, B3, price, zone, freshness | Charge late/consumed prise pour fresh |
| B3+B4+P1 | `release_candidate_state`, `packet_quality` | `RELEASE_VALIDATED` | price accepted, zone coherent, B7 relay, data acceptable | Candidate rejeté par prix |
| B5 relational gravity | `relational_context`, `leader_follower_state` | Driver final, outcome | B8, coverage, price, B7 | Fausse certitude relationnelle |
| B8 cross-symbol validation | `cross_validation_state`, `driver_context` | Vraie force GBP/USD si coverage faible | coverage map, symbol freshness, B5 | `B8_DEGRADED` |
| B6 film memory | `memory_match`, `known_false_positive`, `next_expected_behavior`, `invalidation_reference` | Prediction, outcome certain | current film, price arbiter, guards | Événement isolé confondu avec film |
| B7 propagation | `propagation_state`, `relay_quality` | Trade, release alone, qualified_bias alone | B3, price, zone, B7+, data | `LTF_ONLY` pris pour structure |
| B7+ detachment texture | `detachment_texture`, support `current_move_role` | Direction finale | price, last_structural_event, B7, B6 | Texture floue / UNKNOWN masqué |
| Guards data/session/entropy | `data_visibility`, `session_context`, `entropy_state`, `packet_quality` | Market role unless degraded constraints | all fields, timestamps, source freshness | Stale packet pris pour live |
| Time Profiles LTF/MTF/HTF | `time_profile_state`, support `propagation_state` | Release validation | B7, B3, price | LTF fort sans MTF pris pour validé |
| Evidence Bus | `evidence_refs` | Any semantic role | field_supported required | Evidence spam |
| Perception Spine actuelle | `spine_summary` | Override terrain_packet | terrain_packet | Spine contredit packet |
| Trader Packet | `terrain_packet` | Trade decision | all source fields | Packet trop brut |
| Alert Gate | `alert_gate_state`, `dedupe_state` | Semantic invention | terrain_packet | Gate renomme le signal |
| Dashboard | `dashboard_surface` | Business logic | terrain_packet readonly | Dashboard décide |
| Telegram | `telegram_packet` if enabled later | Activation V7.6 | QA pass + feature flag | Transmission prématurée |

## 2. Champs terrain_packet et briques support

| FIELD | PRIMARY SUPPORT | SECONDARY SUPPORT | HARD BLOCKERS |
|---|---|---|---|
| `film_state` | B6, terrain grammar | price, zone | `READING_PARTIAL` must be shown |
| `last_structural_event` | B6, price history | B7, B7+ | missing history => `UNKNOWN` |
| `current_zone` | price/zone context | B4, P1 | stale price => `UNKNOWN` |
| `current_move_role` | B7+, B6, price | B3, B7 | B3 alone cannot decide |
| `raw_bias` | B3, packet raw | B2 | raw only, no final meaning |
| `qualified_bias` | packet requalification | B6, B7+, price, zone | no price arbiter => not validated |
| `packet_quality` | Guards, price, B7 | Evidence Bus | degraded data must downgrade |
| `price_confirmation` | price arbiter | zone, B6 | missing price => `PENDING` or `UNKNOWN` |
| `propagation_state` | B7 | Time Profiles | no MTF => `LTF_ONLY` or `UNKNOWN` |
| `detachment_texture` | B7+ | B3, B6 | texture unknown must be explicit |
| `data_visibility` | Guards | timestamps, source freshness | degraded must display first |
| `watch_condition` | terrain grammar | B6, price | cannot be empty if packet is WATCH |
| `invalidation_condition` | terrain grammar, B6 | price | cannot be vague for high-priority packet |
| `memory_match` | B6 | film library | no match => `NO_FILM_MATCH` |
| `evidence_refs` | Evidence Bus | all bricks | no orphan evidence |

## 3. Non-décision par brique

### B3

B3 supports `current_move_role` but does not decide release validation.

### B7

B7 supports `propagation_state` but does not decide trade or outcome.

### B6

B6 supports `memory_match` but does not decide outcome.

### Guards

Guards support `data_visibility` and must be displayed first if degraded.

### Dashboard

Dashboard displays `terrain_packet`. It does not modify `qualified_bias`, `price_confirmation`, `packet_quality`, or `current_move_role`.

## 4. Required crosscheck rules

```text
RELEASE_VALIDATED requires:
- release_candidate_state = RELEASE_CANDIDATE
- price_confirmation = ACCEPTED
- current_zone coherent with direction
- propagation_state in [LTF_MTF_RELAY, MTF_HTF_RELAY]
- data_visibility not in [READING_PARTIAL, MICROFILM_MISSING, M1_MISSING, PACKETS_STALE]
```

```text
COUNTER_BREATH requires:
- last_structural_event opposite or lower/higher lock context
- B7+ texture = COUNTER_BREATH_DETACHMENT or POST_RELEASE_DETACHMENT
- price_confirmation pending or rejected until acceptance proves reintegration
```

```text
HONEST_UNKNOWN requires:
- B5/B8 coverage insufficient
- stale or missing cross-symbol data
- relational conflict unresolved
```

## 5. Failure mode vocabulary

```text
B3_B2_FALSE_BIRTH
DIRECTIONAL_WITHOUT_PRICE
HOT_WITHOUT_PRICE_MOVE
RELEASE_CANDIDATE_PRICE_REJECTED
B8_DEGRADED
B5_B8_HONEST_UNKNOWN
LTF_ONLY_MISREAD_AS_STRUCTURE
STALE_PACKET_MISREAD_AS_LIVE
EVENT_TIME_OFFSET
EVIDENCE_SPAM
DASHBOARD_LOGIC_LEAK
TELEGRAM_PREMATURE
```
