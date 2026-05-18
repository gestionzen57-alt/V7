Claude,

T0146 — B9 Memory Confidence Ladder V0 est prêt.

Branche :
feat/t0146-b9-memory-confidence-ladder

Commit proposé :
feat(t0146): add B9 memory confidence ladder v0

Objectif :
Transformer les pièges T0145 en échelle de comparabilité mémoire : forte, partielle, source limitée, session différente, retest manquant ou raw unavailable rejeté.

Tests :
python -m py_compile pf_t009_memory_confidence_ladder.py tools\build_t0146_b9_memory_confidence_ladder.py
python -m pytest tests\test_t0146_b9_memory_confidence_ladder.py

Résultat attendu :
2 passed

Doctrine :
B9 lit la scène.
B6 compare les films.
T0146 qualifie la comparabilité technique.
Aucune probabilité de résultat.
Aucun ordre directionnel.

Prochain geste :
T0147 — B9 Live Scene Candidate Queue V0.
