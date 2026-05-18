Claude,

T0153 — B9 Scene State Machine V0 est prêt.

Branche :
feat/t0153-b9-scene-state-machine

Commit proposé :
feat(t0153): add B9 scene state machine v0

Objectif :
Transformer les rôles/verdicts/nodes/mémoire B9 en états de scène : construction, test, acceptation, rejet, déconstruction, reconstruction, mémoire déplacée, raw unavailable bloqué, revue technique.

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Une mémoire B6 proche avec false-positive HIGH reste une mémoire proche avec piège technique, pas une absence de mémoire.

Tests :
python -m py_compile pf_t009_scene_state_machine.py tools\build_t0153_b9_scene_state_machine.py
python -m pytest tests\test_t0153_b9_scene_state_machine.py

Résultat attendu :
2 passed

Commande CLI :
python tools\build_t0153_b9_scene_state_machine.py --sequence-summary-json samples\b9_scene_state_machine_v0\sample_t009_sequence_summary_scene_state.json --output-dir outputs\b9_scene_state_machine_v0

Limites :
Read-only. Aucune DB. Aucun dashboard. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite. Une scène proxy reste proxy. RAW_UNAVAILABLE est bloqué.

Prochain geste :
T0154 — B9 Scene Transition Detector V0.
