# Commandes T0123 — B9 V4 Replay Runtime Comparison

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core

python -m py_compile tools\build_t0123_b9_v4_replay_runtime_comparison.py
python -m pytest tests\test_t0123_b9_v4_replay_runtime_comparison.py

python tools\build_t0123_b9_v4_replay_runtime_comparison.py `
  --before-summary-json samples\b9_v4_replay_runtime_comparison_v0\sample_t009_sequence_summary_before_v4.json `
  --output-dir outputs\b9_v4_replay_runtime_comparison_v0
```
