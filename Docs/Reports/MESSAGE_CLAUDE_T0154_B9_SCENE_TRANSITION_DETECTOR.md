Claude,

T0154 — B9 Scene Transition Detector V0 est prêt.

Branche :
feat/t0154-b9-scene-transition-detector

Commit proposé :
feat(t0154): add B9 scene transition detector v0

Objectif :
Transformer les états de scène B9 T0153 en transitions explicites : BUILD_TO_TEST, TEST_TO_ACCEPTED, TEST_TO_REJECTED, ACCEPTED_TO_MEMORY_SHIFTED, MEMORY_SHIFT_TO_NEW_TEST, RAW_UNAVAILABLE_TRANSITION_BLOCKED.

Point T0148 :
Après patch contrat JSON, T0148 lit similar_films et false_positive_contexts. Un false-positive HIGH reste une mémoire comparable avec piège technique fort, pas une absence de mémoire.

Tests :
python -m py_compile pf_t009_scene_transition_detector.py tools\build_t0154_b9_scene_transition_detector.py
python -m pytest tests\test_t0154_b9_scene_transition_detector.py

Résultat attendu :
2 passed

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Une transition de scène qualifie le film, elle ne produit pas une décision d’exécution.

Limites :
Read-only. Aucune DB. Aucun dashboard. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.

Prochain geste :
T0155 — B9 Trader Attention Packet V0.
