# PowerFlow V7.2 — Scene Memory Enrichment

This pack adds an additive layer around B6 Memory.

It does not replace B6.
It does not break the 6D tuple.
It enriches alerts with:
- scene_id
- scene_family
- scene_confidence_non_blocking
- scene_context
- memory_tuple_6d
- B3_noise_ratio
- B7_state
- outcome
- bars_to_move

## Validate

```powershell
.\scripts\validate_scene_memory_enrichment.ps1
```

## Run

```powershell
python Core\run_scene_memory_enrichment_once.py --pretty
```

## Outputs

- output/behavioral_alert_queue_scene_enriched.json
- output/scene_memory_enrichment_report.json
- output/scene_memory_enrichment_report.md

## Doctrine

The scene registry names behavior.
B6 remembers behavior.
The trader decides.
