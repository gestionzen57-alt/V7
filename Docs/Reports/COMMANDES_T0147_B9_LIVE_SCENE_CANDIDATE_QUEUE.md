# Commandes T0147

## Tests

```powershell
python -m py_compile pf_t009_live_scene_candidate_queue.py tools\build_t0147_b9_live_scene_candidate_queue.py
python -m pytest tests\test_t0147_b9_live_scene_candidate_queue.py
```

## CLI

```powershell
python tools\build_t0147_b9_live_scene_candidate_queue.py --sequence-summary-json samples\b9_live_scene_candidate_queue_v0\sample_t009_sequence_summary_live_queue.json --output-dir outputs\b9_live_scene_candidate_queue_v0 --max-candidates 12
```
