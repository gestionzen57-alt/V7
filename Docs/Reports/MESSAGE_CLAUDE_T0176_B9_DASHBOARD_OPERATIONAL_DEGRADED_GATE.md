Claude,

T0176 — B9 Dashboard Operational Degraded Gate V0 est prêt.

Objectif : transformer le verrou T0175 en surface dashboard opérationnelle dégradée. Si des inputs obligatoires manquent mais qu'il n'y a ni source error ni langage interdit, le dashboard peut afficher ce qui existe et des cartes techniques pour ce qui manque.

Tests : py_compile, pytest, CLI.

Contraintes : read-only, aucune DB, aucun cockpit live modifié, aucun Telegram, aucune décision.
