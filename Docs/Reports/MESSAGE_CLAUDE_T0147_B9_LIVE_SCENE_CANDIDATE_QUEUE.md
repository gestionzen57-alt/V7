Claude,

T0147 — B9 Live Scene Candidate Queue V0 est prêt.

Branche :
feat/t0147-b9-live-scene-candidate-queue

Commit proposé :
feat(t0147): add B9 live scene candidate queue v0

Objectif :
Créer une file read-only de scènes candidates B9 live à partir des moments enrichis par T0128→T0146.

Fichiers livrés :

pf_t009_live_scene_candidate_queue.py
tools/build_t0147_b9_live_scene_candidate_queue.py
scripts/RUN_T0147_B9_LIVE_SCENE_CANDIDATE_QUEUE_FROM_DOWNLOADS.ps1
tests/test_t0147_b9_live_scene_candidate_queue.py
samples/b9_live_scene_candidate_queue_v0/sample_t009_sequence_summary_live_queue.json
Docs/Reports/T0147_B9_LIVE_SCENE_CANDIDATE_QUEUE_REPORT.md
Docs/Reports/T0147_B9_LIVE_SCENE_CANDIDATE_QUEUE_MANIFEST.json
Docs/Reports/COMMANDES_T0147_B9_LIVE_SCENE_CANDIDATE_QUEUE.md
Docs/Reports/MESSAGE_CLAUDE_T0147_B9_LIVE_SCENE_CANDIDATE_QUEUE.md
outputs/b9_live_scene_candidate_queue_v0/*

Tests :
python -m py_compile pf_t009_live_scene_candidate_queue.py tools\build_t0147_b9_live_scene_candidate_queue.py
python -m pytest tests\test_t0147_b9_live_scene_candidate_queue.py

Résultat attendu :
2 passed

Commande CLI :
python tools\build_t0147_b9_live_scene_candidate_queue.py --sequence-summary-json samples\b9_live_scene_candidate_queue_v0\sample_t009_sequence_summary_live_queue.json --output-dir outputs\b9_live_scene_candidate_queue_v0 --max-candidates 12

Sorties :
B9_LATEST_SCENE_CANDIDATE_V0.json
B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json
B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.md
B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.csv
B9_LIVE_SCENE_CANDIDATE_REJECTED_V0.csv
B9_LIVE_SCENE_CANDIDATE_LOW_SIGNAL_V0.csv
B9_LIVE_SCENE_CANDIDATE_QUEUE_MANIFEST.json
B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.zip

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
La queue prépare une scène candidate, pas une décision.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.
Une scène proxy reste proxy.
RAW_UNAVAILABLE est rejeté de la queue active.

Prochain geste :
T0148 — B9 Live Brief Once Runner V0.

Mode recommandé :
GPT Pro standard.
