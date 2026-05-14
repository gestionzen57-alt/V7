# POWERFLOW TERRAIN QA GRID V7.6

## Objectif

Valider que PowerFlow V7.6 transforme les fragments (`PAIR_UP`, `PAIR_DOWN`, `HOT`, `WATCH`, `ACTIVE`) en packet terrain qualifié sans créer de stratégie, sans refaire le dashboard, sans activer Telegram et sans masquer la visibilité data.

## Contrat QA

Chaque test doit vérifier au minimum :

```text
raw_bias conservé
qualified_bias principal
packet_quality présent
price_confirmation présent
data_visibility visible
technical_risks explicites si données dégradées
watch_condition et invalidation_condition présents sans buy/sell/entry/exit/target/stop
```

## Grille obligatoire

| QA_ID | Input terrain | Conditions minimales | Sortie attendue | Refus attendu |
|---|---|---|---|---|
| `QA-01` | B3+B2 actif seul | `b3_active=true`, `b2_active=true`, pas B4/P1/prix | `qualified_bias=EVENT_STACK`, `packet_quality=EVENT_STACK_NOT_RELEASE` | Pas `RELEASE_VALIDATED`. |
| `QA-02` | B3+B4+P1 + prix accepté | `b3_active=true`, `b4_active=true`, `p1_active=true`, `price=PRICE_ACCEPTED_*`, B7 non failed, data OK | `RELEASE_VALIDATED` | Pas validation si B7 failed ou stale. |
| `QA-03` | Release UP puis `PAIR_DOWN` | `last_structural_event=RELEASE_UP_VALIDATED`, `raw_bias=PAIR_DOWN` | `POST_RELEASE_PULLBACK` | Pas `PAIR_DOWN` brut affiché seul. |
| `QA-04` | Pullback absorbé | `PAIR_DOWN`, `PRICE_ABSORBED_PULLBACK` ou close high ensuite | `PULLBACK_ABSORBED` | Pas pression down validée. |
| `QA-05` | High rejeté puis DOWN | `last_structural_event=HIGH_ZONE_REJECTION`, `raw_bias=PAIR_DOWN` | `POST_HIGH_UNWIND` | Pas `PAIR_DOWN` générique. |
| `QA-06` | Release DOWN puis `PAIR_UP` | `last_structural_event=RELEASE_DOWN_VALIDATED`, `raw_bias=PAIR_UP` | `POST_RELEASE_COUNTER_BREATH` / `COUNTER_BREATH_UP` | Pas nouvelle release up sans acceptance. |
| `QA-07` | Counter-breath échoue | `PAIR_UP` puis lower low / invalidation prix | `COUNTER_BREATH_REJECTED` | Pas maintien en UP. |
| `QA-08` | Après rejet counter-breath | `last_structural_event=COUNTER_BREATH_REJECTED`, `raw_bias=PAIR_DOWN` | `SECOND_LEG_DOWN` | Pas direction brute seule. |
| `QA-09` | HOT sans déplacement prix | `raw_bias=HOT`, `no_price_displacement=true` | `PRESSURE_PENDING`, `PRICE_PENDING` | Pas `EVENT_CONFIRMED`. |
| `QA-10` | HOT après extension | `raw_bias=HOT`, `after_extension=true` | `EXHAUSTION_OR_CONSUMED` | Pas fresh release. |
| `QA-11` | B8 coverage faible | `b8_degraded=true` | `HONEST_UNKNOWN` si aucune preuve plus forte, risque `B8_DEGRADED` | Pas confirmation dure via B8 faible. |
| `QA-12` | M1 absent/stale | `m1_missing=true` ou `packets_stale=true` | `READING_PARTIAL` visible ou `M1_MISSING_PACKETS_STALE` | Pas lecture complète. |
| `QA-13` | `event_at` offset | `event_time_offset=true` | `EVENT_TIME_OFFSET` dans visibility/risks | Pas horodatage silencieux. |
| `QA-14` | LTF contre MTF | `propagation_state=COUNTERFLOW_AGAINST_STRUCTURE` | Risque/info qualitative, pas blocage automatique | Pas censure de l'alerte. |

## Tests historiques GBPUSD calibrés

| Date | Film | Points QA |
|---|---|---|
| 2026-05-06 | `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION` | UP après high-zone devient suspect / consumed. |
| 2026-05-07 | `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND` | DOWN après high rejeté devient `POST_HIGH_UNWIND`. |
| 2026-05-08 | `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH` | Acceptance prix peut valider continuation. |
| 2026-05-11 | `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION` | B3+B2 seul produit false birth / event stack. |
| 2026-05-12 | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH` | PAIR_UP après release down = counter-breath par défaut. |
| 2026-05-13 | `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN` | Counter-breath rejeté devient carburant du second leg. |
| 2026-05-14 | `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL` | M1 absent + packets stale = data visibility en haut. |

## Commandes QA

```bash
python -m unittest tests/test_packet_requalification_rules_v76.py
python patch/pf_packet_requalification_once.py \
  --input schema/terrain_packet_examples/gbpusd_20260514_lower_zone_partial.json \
  --output /tmp/terrain_packet.json \
  --audit /tmp/terrain_packet_audit.jsonl
```

## Critères de refus release

La release V7.6 doit être refusée si :

```text
PAIR_UP / PAIR_DOWN apparaît comme lecture principale sans qualified_bias.
price_confirmation est absent.
data_visibility est absent ou masqué.
B3+B2 peut produire RELEASE_VALIDATED.
B3+B4+P1 produit RELEASE_VALIDATED sans prix acceptable.
HOT sans prix devient EVENT_CONFIRMED.
B8 faible confirme dur.
M1 absent/stale n'apparaît pas en haut.
Le patch dépend du dashboard ou de Telegram.
Le patch introduit buy/sell/entry/exit/target/stop.
```

## Résultat attendu

Un packet terrain V7.6 utile doit raconter :

```text
DATA=M1_MISSING_PACKETS_STALE
FILM=LOWER_ZONE_ACTIVE
LAST_EVENT=COUNTER_BREATH_REJECTED
MOVE=POST_LOW_REACTION
RAW_BIAS=PAIR_UP
QUALIFIED_BIAS=POST_LOW_COUNTER_BREATH
QUALITY=REACTION_NOT_RELEASE
PRICE=PRICE_PENDING
WATCH=ACCEPTANCE_ABOVE_1.3532_OR_BREAK_BELOW_1.3504
INVALIDATION=NEW_LOWER_LOW_OR_REJECTION_BELOW_1.3504
```

Pas seulement :

```text
PAIR_UP WATCH
```
