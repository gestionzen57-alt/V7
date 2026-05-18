Claude,

T0138 — B9 Real Replay Day Pack Runner V0 est prêt.

Branche :
feat/t0138-b9-real-replay-day-pack-runner

Commit proposé :
feat(t0138): add B9 real replay day pack runner v0

Objectif :
Appliquer les guards B9 V4 sur les vrais summaries replay trouvés par T0126 ou par scan local, en excluant samples, validation, regenerated et _extract.

Fichiers livrés :

tools/build_t0138_b9_real_replay_day_pack_runner.py
scripts/RUN_T0138_B9_REAL_REPLAY_DAY_PACK_RUNNER_FROM_DOWNLOADS.ps1
tests/test_t0138_b9_real_replay_day_pack_runner.py
samples/b9_real_replay_day_pack_runner_v0/*
Docs/Reports/T0138_B9_REAL_REPLAY_DAY_PACK_RUNNER_REPORT.md
Docs/Reports/T0138_B9_REAL_REPLAY_DAY_PACK_RUNNER_MANIFEST.json
Docs/Reports/COMMANDES_T0138_B9_REAL_REPLAY_DAY_PACK_RUNNER.md
Docs/Reports/MESSAGE_CLAUDE_T0138_B9_REAL_REPLAY_DAY_PACK_RUNNER.md

Tests :
python -m py_compile tools\build_t0138_b9_real_replay_day_pack_runner.py
python -m pytest tests\test_t0138_b9_real_replay_day_pack_runner.py

CLI :
python tools\build_t0138_b9_real_replay_day_pack_runner.py --scan-root . --input-index-csv outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv --output-dir outputs\b9_real_replay_day_pack_runner_v0

Sorties :
B9_REAL_REPLAY_DAY_RUNNER_V0.md/json
B9_REAL_REPLAY_DAY_RESULTS_V0.csv
B9_REAL_REPLAY_DAY_KEEP_V0.csv
B9_REAL_REPLAY_DAY_REVIEW_V0.csv
B9_REAL_REPLAY_DAY_FAILURES_V0.csv
B9_REAL_REPLAY_DAY_COVERAGE_V0.csv

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
T0138 valide des replays, il ne prédit rien.

Limites :
Read-only. Aucune DB. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucun taux de réussite.

Prochain geste :
T0139 — B9 London / NY / Asian Replay Scorecard V0.


## Correction V2

Le test sample accepte maintenant les candidats KEEP ou REVIEW selon la couverture réelle des champs locaux. RAW_UNAVAILABLE-only reste rejeté. Pytest et CLI restent bloquants.
