Claude,

T0148 — B9 Live Brief Once Runner V0 est prêt.

Branche :
feat/t0148-b9-live-brief-once-runner

Commit proposé :
feat(t0148): add B9 live brief once runner v0

Objectif :
Orchestrer une exécution CLI unique qui consomme T0147, T0116, T0115, T0117/T0145, T0118 et T0134 pour produire un brief B9/B6 live read-only.

Fichiers livrés :

pf_t009_live_brief_once_runner.py
tools/build_t0148_b9_live_brief_once_runner.py
scripts/RUN_T0148_B9_LIVE_BRIEF_ONCE_RUNNER_FROM_DOWNLOADS.ps1
tests/test_t0148_b9_live_brief_once_runner.py
samples/b9_live_brief_once_runner_v0/*
Docs/Reports/T0148_B9_LIVE_BRIEF_ONCE_RUNNER_REPORT.md
Docs/Reports/T0148_B9_LIVE_BRIEF_ONCE_RUNNER_MANIFEST.json
Docs/Reports/COMMANDES_T0148_B9_LIVE_BRIEF_ONCE_RUNNER.md
Docs/Reports/MESSAGE_CLAUDE_T0148_B9_LIVE_BRIEF_ONCE_RUNNER.md
outputs/b9_live_brief_once_runner_v0/*

Tests :
python -m py_compile pf_t009_live_brief_once_runner.py tools\build_t0148_b9_live_brief_once_runner.py
python -m pytest tests\test_t0148_b9_live_brief_once_runner.py

Résultat attendu :
2 passed

CLI sample :
python tools\build_t0148_b9_live_brief_once_runner.py --latest-scene-json samples\b9_live_brief_once_runner_v0\sample_latest_scene_candidate.json --queue-json samples\b9_live_brief_once_runner_v0\sample_live_scene_queue.json --adapter-json samples\b9_live_brief_once_runner_v0\sample_adapter_payload.json --similarity-query-json samples\b9_live_brief_once_runner_v0\sample_similarity_query_result.json --false-positive-json samples\b9_live_brief_once_runner_v0\sample_false_positive_context.json --terrain-synthesis-json samples\b9_live_brief_once_runner_v0\sample_terrain_synthesis.json --french-report-json samples\b9_live_brief_once_runner_v0\sample_french_report.json --output-dir outputs\b9_live_brief_once_runner_v0

Résultat sample attendu :
brief_state = B9_LIVE_BRIEF_READY
match_count = 3
top_match_film_id = B6FC_20260514_1903_E8F0918A
false_positive_context_available = true
terrain_synthesis_available = true
forbidden_language_hits = []

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
B6 compare les films.
Le brief transmet une mémoire comparable, pas une décision d'exécution.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.
Une scène proxy reste proxy.
Si une entrée manque, T0148 retourne BLOCKED_MISSING_INPUTS.

Prochain geste :
T0149 — B9 Reality Board Payload Candidate V0.

Mode recommandé :
GPT Thinking étendue.
