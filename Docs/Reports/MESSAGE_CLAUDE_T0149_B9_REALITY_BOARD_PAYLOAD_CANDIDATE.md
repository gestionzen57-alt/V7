Claude,

T0149 — B9 Reality Board Payload Candidate V0 est prêt.

Branche :
feat/t0149-b9-reality-board-payload-candidate

Commit proposé :
feat(t0149): add B9 Reality Board payload candidate v0

Objectif :
Transformer le brief live T0148 en payload candidat Reality Board, sans brancher le dashboard live.

Fichiers livrés :

- pf_t009_reality_board_payload_candidate.py
- tools/build_t0149_b9_reality_board_payload_candidate.py
- scripts/RUN_T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE_FROM_DOWNLOADS.ps1
- tests/test_t0149_b9_reality_board_payload_candidate.py
- samples/b9_reality_board_payload_candidate_v0/sample_b9_live_brief_once_ready.json
- Docs/Reports/T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REPORT.md
- Docs/Reports/T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE_MANIFEST.json
- Docs/Reports/COMMANDES_T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE.md
- Docs/Reports/MESSAGE_CLAUDE_T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE.md
- outputs/b9_reality_board_payload_candidate_v0/*

Tests :

python -m py_compile pf_t009_reality_board_payload_candidate.py tools\build_t0149_b9_reality_board_payload_candidate.py
python -m pytest tests\test_t0149_b9_reality_board_payload_candidate.py

Résultat attendu :
2 passed

Commande CLI runtime :

python tools\build_t0149_b9_reality_board_payload_candidate.py --live-brief-json outputs\b9_live_brief_once_runner_v0\B9_LIVE_BRIEF_ONCE_V0.json --output-dir outputs\b9_reality_board_payload_candidate_v0

États possibles :

- B9_REALITY_BOARD_PAYLOAD_CANDIDATE_READY
- B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REVIEW_LIMITED_SOURCE
- BLOCKED_MISSING_LIVE_BRIEF_INPUT
- BLOCKED_LIVE_BRIEF_NOT_READY
- BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS
- BLOCKED_FORBIDDEN_LANGUAGE

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Le payload Reality Board expose une scène candidate, il ne décide pas.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard live.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.
Une scène proxy reste proxy.
Si le brief T0148 manque, T0149 retourne BLOCKED_MISSING_LIVE_BRIEF_INPUT.

Prochain geste :
T0151 — B9 Daily Replay Audit Report V0, ou T0150/T0151 consolidation terrain si T0150 doc est validé.
