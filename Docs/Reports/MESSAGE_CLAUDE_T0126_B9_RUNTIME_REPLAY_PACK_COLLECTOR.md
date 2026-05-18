Claude,

T0126 — B9 V4 Runtime Replay Pack Collector V0 est prêt.

Branche :
feat/t0126-b9-runtime-replay-pack-collector

Commit proposé :
feat(t0126): add B9 runtime replay pack collector

Objectif :
Scanner le Core local, trouver les vrais summaries B9/T009, exclure samples et outputs validation/regenerated, puis produire un lot réel exploitable par T0125.

Fichiers livrés :

tools/build_t0126_b9_runtime_replay_pack_collector.py
scripts/RUN_T0126_B9_RUNTIME_REPLAY_PACK_COLLECTOR_FROM_DOWNLOADS.ps1
tests/test_t0126_b9_runtime_replay_pack_collector.py
samples/b9_runtime_replay_pack_collector_v0/t009_sequence_summary_real_candidate.json
Docs/Reports/T0126_B9_RUNTIME_REPLAY_PACK_COLLECTOR_REPORT.md
Docs/Reports/T0126_B9_RUNTIME_REPLAY_PACK_COLLECTOR_MANIFEST.json
Docs/Reports/COMMANDES_T0126_B9_RUNTIME_REPLAY_PACK_COLLECTOR.md
Docs/Reports/MESSAGE_CLAUDE_T0126_B9_RUNTIME_REPLAY_PACK_COLLECTOR.md
outputs/b9_runtime_replay_pack_collector_v0/*

Tests :
python -m py_compile tools\build_t0126_b9_runtime_replay_pack_collector.py
python -m pytest tests\test_t0126_b9_runtime_replay_pack_collector.py

Résultat attendu :
2 passed

CLI :
python tools\build_t0126_b9_runtime_replay_pack_collector.py --scan-root . --output-dir outputs\b9_runtime_replay_pack_collector_v0

Validation sample :
files_discovered = 1
candidates_keep = 1
candidates_review = 0
candidates_rejected = 0
files_with_v4_fields = 1
files_with_source_quality = 1
files_with_timestamp_policy = 1
forbidden_language_files = 0

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
T0126 ne prédit rien, il prépare un lot replay propre.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.

Prochain geste :
Lancer T0127 — B9 Timestamp Remap Guard V0.
