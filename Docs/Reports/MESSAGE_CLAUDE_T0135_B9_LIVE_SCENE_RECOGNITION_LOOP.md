Claude,

T0135 — B9 Live Scene Recognition Loop V0 est prêt.

Branche :
feat/t0135-b9-live-scene-recognition-loop

Commit proposé :
feat(t0135): add B9 live scene recognition loop v0

Objectif :
Assembler scène live B9 + T0115 films proches + T0117 pièges techniques + T0118 synthèse terrain + T0134 rapport FR trader dans un paquet de reconnaissance read-only.

Fichiers livrés :

pf_t009_live_scene_recognition_loop.py
tools/build_t0135_b9_live_scene_recognition_loop.py
scripts/RUN_T0135_B9_LIVE_SCENE_RECOGNITION_LOOP_FROM_DOWNLOADS.ps1
tests/test_t0135_b9_live_scene_recognition_loop.py
samples/b9_live_scene_recognition_loop_v0/*
Docs/Reports/T0135_B9_LIVE_SCENE_RECOGNITION_LOOP_REPORT.md
Docs/Reports/T0135_B9_LIVE_SCENE_RECOGNITION_LOOP_MANIFEST.json
Docs/Reports/COMMANDES_T0135_B9_LIVE_SCENE_RECOGNITION_LOOP.md
Docs/Reports/MESSAGE_CLAUDE_T0135_B9_LIVE_SCENE_RECOGNITION_LOOP.md
outputs/b9_live_scene_recognition_loop_v0/*

Tests :
python -m py_compile pf_t009_live_scene_recognition_loop.py tools\build_t0135_b9_live_scene_recognition_loop.py
python -m pytest tests\test_t0135_b9_live_scene_recognition_loop.py

Résultat attendu :
2 passed

Commande CLI :
python tools\build_t0135_b9_live_scene_recognition_loop.py --live-scene-json samples\b9_live_scene_recognition_loop_v0\sample_b9_live_scene_query_payload.json --similarity-query-json samples\b9_live_scene_recognition_loop_v0\sample_t0115_similarity_query_result.json --false-positive-json samples\b9_live_scene_recognition_loop_v0\sample_t0117_false_positive_context.json --terrain-synthesis-json samples\b9_live_scene_recognition_loop_v0\sample_t0118_human_terrain_synthesis.json --french-report-json samples\b9_live_scene_recognition_loop_v0\sample_b9_french_trader_scene_report.json --output-dir outputs\b9_live_scene_recognition_loop_v0 --top-k 3

Résultat sample :
recognition_state = B9_LIVE_SCENE_RECOGNITION_READY
match_count = 3
top_match_film_id = B6FC_20260514_1903_E8F0918A
cross_family_match_count = 0
low_trust_in_results = false
raw_unavailable_in_results = false
false_positive_context_available = true
terrain_synthesis_available = true
forbidden_language_hit_count = 0

Doctrine :
B9 lit la scène.
B6 compare les films.
T0135 reconnaît une famille de scène et ses limites.
Le trader décide.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre d'exécution.
Aucun taux de réussite.
Une similarité reste une proximité de lecture, pas une répétition certaine.

Prochain geste :
T0136 — Live Loop Runtime Wiring Guard V0.
Mode recommandé : GPT Thinking étendue.
