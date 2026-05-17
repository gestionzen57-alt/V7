# B9 ↔ B6 Film Memory Contract Report

Status: `READY_FOR_REVIEW`
Branch: `docs/b9-b6-film-memory-contract`
Commit proposal: `docs(t009): add B9 to B6 film memory contract`

## 1. Executive summary

This delivery creates a documentary and testable contract for transforming B9 local scenes into B6 memory signatures.

```text
B9 raconte la scène.
B6 demande : avons-nous déjà vu ce film, et quel piège avait-il caché ?
```

## 2. Why this contract is needed

B9 now exports local scene objects:

- moments;
- parent_scene;
- zone_memory;
- effort_role;
- retest_status;
- memory_state;
- source_profile;
- proxy_vs_raw_verdict;
- raw_coverage.

B6 needs these objects as stable film-memory inputs. The goal is not prediction. The goal is historical comparison and trap memory.

## 3. B9 side

B9 says what is printed in the local scene:

```text
effort → result → progress → retest → memory shift
```

B9 must preserve:

- `source_mode`;
- `data_visibility`;
- `confidence_cap`;
- raw coverage;
- proxy/raw verdict;
- limits.

## 4. B6 side

B6 transforms B9 scenes into comparable memory records:

- `film_signature`;
- `sequence_signature`;
- `dominant_zone_memory`;
- `raw_confirmation_state`;
- `historical_analogy`;
- `false_positive_risks`;
- `confirmation_needed_fr`;
- `invalidation_needed_fr`;
- `limits`.

## 5. Core rule

B6 compares.
B6 does not predict.
B6 does not decide.
B6 stores traps, invalidations, missing confirmations, and data limits.

## 6. Example memory reading

```text
Film mémoire : projection refusée puis mémoire déplacée.
Le film courant ressemble à une scène où le haut projeté ne conserve pas son centre.
La mémoire basse devient active après retest échoué.
Raw state : RAW_CONFIRMED si couverture complète ; RAW_PARTIAL si couverture partielle ; RAW_UNAVAILABLE si la preuve manque.
Piège : ne pas confondre vague progressive proxy et vraie progression raw.
```

## 7. Constraints respected

- documentary-only;
- read-only;
- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard mutation;
- no Telegram;
- no premature B8 fusion;
- no directional order;
- no B6 prediction.

## 8. Recommended next step

Later, if approved, create a pure read-only mapper:

```python
map_b9_scene_to_b6_film_memory(b9_payload) -> b6_memory_payload
```

This future module must remain deterministic, testable, and free of DB writes by default.
