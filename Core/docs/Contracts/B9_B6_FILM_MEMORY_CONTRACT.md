# B9 ↔ B6 Film Memory Contract — PowerFlow

Status: `B9_B6_FILM_MEMORY_CONTRACT_READY`
Scope: documentary + testable contract only
Runtime: none
DB writes: none

## 1. Purpose

This contract defines how B9 local scenes are transformed into B6 film-memory signatures.

B9 does not predict.
B6 does not predict.
B9 reads the local scene.
B6 asks whether a comparable film has already been observed, what confirmed it, what invalidated it, and what trap it contained.

```text
B9 raconte la scène.
B6 demande : avons-nous déjà vu ce film, et quel piège avait-il caché ?
```

## 2. Separation of roles

| Brick | Role | Must not do |
|---|---|---|
| B9 | Local trace of effort/result/progress in price | predict, decide, write DB, send Telegram |
| B6 | Memory of comparable films and traps | decide, predict as truth, replace trader |
| Perception Spine | Later synthesis of proofs | erase source limits or produce an order |

## 3. B9 payload consumed by B6

```json
{
  "symbol": "GBPUSD",
  "session_chapter": "London / US",
  "moments": [
    {
      "moment_id": "B9M_20260515_1720_001",
      "moment_type": "T009_MOMENT_CENTER_MIGRATION_DOWN",
      "label_fr": "Centre de gravité qui descend",
      "time_start": "2026-05-15T17:20:00Z",
      "time_end": "2026-05-15T17:47:00Z",
      "effort_role": "absorption_accompanying_pressure",
      "retest_status": "failed_retest",
      "memory_state": "shifted",
      "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
      "raw_coverage": "FULL",
      "source_profile": {
        "source_mode": "M1_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED",
        "confidence_cap": 0.35
      }
    }
  ],
  "parent_scene": {
    "scene_id": "B9S_GBPUSD_20260515_US_001",
    "scene_role": "projection_rejected_then_memory_shifted",
    "base": {},
    "reaction": {},
    "projection": {},
    "judgment": {
      "retest_status": "failed_retest"
    }
  },
  "zone_memory": {
    "zone_id": "B9Z_GBPUSD_20260515_001",
    "memory_state": "shifted",
    "retest_status": "failed_retest",
    "zone_low": 1.3346,
    "zone_high": 1.3364
  }
}
```

## 4. B6 output contract

```json
{
  "film_signature": "PROJECTION_REJECTED_MEMORY_SHIFTED_LOWER",
  "sequence_signature": [
    "BASE",
    "REACTION",
    "PROJECTION",
    "JUDGMENT"
  ],
  "dominant_zone_memory": "LOW_MEMORY_ACTIVE",
  "raw_confirmation_state": "RAW_CONFIRMED",
  "historical_analogy": "UNKNOWN",
  "false_positive_risks": [
    "PROXY_PROGRESSIVE_WAVE_OVERREAD",
    "ZERO_DURATION_ARTIFACT",
    "RAW_BROKER_RELATIVE"
  ],
  "confirmation_needed_fr": "Comparer avec films où un retest échoué a déplacé la mémoire basse.",
  "invalidation_needed_fr": "Réintégration propre de l’ancienne zone haute ou raw divergence persistante.",
  "limits": [
    "B6 compare des films ; il ne prédit pas la suite.",
    "Le raw tick MT5 reste broker-relative.",
    "La mémoire B6 doit conserver les films incomplets et les pièges."
  ]
}
```

## 5. Required B6 fields

| Field | Meaning |
|---|---|
| `film_signature` | Stable comparable name for the current B9 scene |
| `sequence_signature` | Ordered film grammar: base, reaction, projection, judgment |
| `dominant_zone_memory` | Zone memory role retained by B6 |
| `raw_confirmation_state` | `RAW_CONFIRMED`, `RAW_PARTIAL`, `RAW_UNAVAILABLE`, `RAW_DIVERGENCE` |
| `historical_analogy` | Matching status vs previous films |
| `false_positive_risks` | Explicit traps B6 must remember |
| `confirmation_needed_fr` | What would confirm the analogy |
| `invalidation_needed_fr` | What would break the analogy |
| `limits` | Source, coverage and causality limits |

## 6. Mapping rules

### 6.1 Scene to film signature

| B9 scene_role | B6 film_signature |
|---|---|
| `base_reaction_projection_judgment` | `BASE_REACTION_PROJECTION_JUDGMENT` |
| `projection_rejected_then_memory_shifted` | `PROJECTION_REJECTED_MEMORY_SHIFTED` |
| `absorption_shelf_then_second_leg` | `ABSORPTION_SHELF_SECOND_LEG_CANDIDATE` |
| `range_boundary_reaction` | `RANGE_BOUNDARY_REACTION_FILM` |
| `effort_without_result_near_memory` | `EFFORT_WITHOUT_RESULT_MEMORY_TEST` |

### 6.2 Raw confirmation state

| B9 proxy/raw condition | B6 raw_confirmation_state |
|---|---|
| `CONFIRMED_BY_RAW` + `raw_coverage=FULL` | `RAW_CONFIRMED` |
| `CONFIRMED_BY_RAW` + `raw_coverage=PARTIAL` | `RAW_PARTIAL` |
| `RAW_RECALIBRATION_NEEDED` | `RAW_DIVERGENCE` |
| `RAW_UNAVAILABLE` or `raw_coverage=MISSING` | `RAW_UNAVAILABLE` |

### 6.3 False-positive risks

B6 must store traps, not only clean wins.

Required risk vocabulary:

```text
PROXY_PROGRESSIVE_WAVE_OVERREAD
ZERO_DURATION_ARTIFACT
RAW_BROKER_RELATIVE
RAW_COVERAGE_PARTIAL
SOURCE_PROFILE_LIMITED
RETEST_NOT_JUDGED
MEMORY_SHIFT_INFERRED
B6_ANALOGY_TOO_WEAK
```

## 7. B6 memory behavior

B6 must preserve:

- clean films;
- partial films;
- failed analogies;
- raw divergence cases;
- data-limit cases;
- traps where B9 over-read a proxy wave;
- cases where raw confirmed the proxy scene.

B6 must not store only the “nice” films.
A memory that only stores clean confirmations becomes biased.

## 8. French rendering target

```text
Film mémoire : projection refusée puis mémoire déplacée.
B9 raconte une scène locale où la projection haute ne conserve pas son centre.
B6 la transforme en signature comparable.
Mémoire : zone basse active, retest haut échoué.
Raw : confirmation partielle ou complète selon couverture.
Piège à retenir : vague progressive proxy surlue ou raw broker-relative.
Limite : B6 compare, il ne prédit pas.
```

## 9. Interdits

```text
B6 ne produit pas de recommandation.
B6 ne prédit pas comme vérité.
B6 ne remplace pas le trader.
B6 n’écrit pas dans powerflow.db dans ce contrat.
B6 n’envoie pas Telegram.
B6 ne modifie pas le dashboard.
B6 ne fusionne pas B8.
B6 ne transforme pas RAW_CONFIRMED en certitude universelle.
```

## 10. Acceptance criteria

- `film_signature` is present.
- `sequence_signature` is present.
- `raw_confirmation_state` is present.
- `false_positive_risks` is present.
- `confirmation_needed_fr` is present.
- `invalidation_needed_fr` is present.
- Source and raw limits remain visible.
- No decision language is introduced.
- The contract is documentary-only.

B6 ne décide pas.

