Claude,

T0140 — B9 Scene Role Requalifier V0 est prêt.

Branche :
feat/t0140-b9-scene-role-requalifier

Commit proposé :
feat(t0140): add B9 scene role requalifier v0

Objectif :
Transformer les labels/moments B9 en rôles de scène : effort sans résultat, palier d'absorption, vague progressive, respiration corrective, migration de mémoire, retest échoué, réintégration échouée, etc.

Fichiers livrés :

pf_t009_scene_role_requalifier.py
tools/build_t0140_b9_scene_role_requalifier.py
scripts/RUN_T0140_B9_SCENE_ROLE_REQUALIFIER_FROM_DOWNLOADS.ps1
tests/test_t0140_b9_scene_role_requalifier.py
samples/b9_scene_role_requalifier_v0/sample_t009_sequence_summary_scene_roles.json
Docs/Reports/T0140_B9_SCENE_ROLE_REQUALIFIER_REPORT.md
Docs/Reports/T0140_B9_SCENE_ROLE_REQUALIFIER_MANIFEST.json
Docs/Reports/COMMANDES_T0140_B9_SCENE_ROLE_REQUALIFIER.md
Docs/Reports/MESSAGE_CLAUDE_T0140_B9_SCENE_ROLE_REQUALIFIER.md
outputs/b9_scene_role_requalifier_v0/*

Tests :

python -m py_compile pf_t009_scene_role_requalifier.py tools\build_t0140_b9_scene_role_requalifier.py
python -m pytest tests\test_t0140_b9_scene_role_requalifier.py

Résultat attendu :
2 passed

Commande CLI :

python tools\build_t0140_b9_scene_role_requalifier.py --sequence-summary-json samples\b9_scene_role_requalifier_v0\sample_t009_sequence_summary_scene_roles.json --output-dir outputs\b9_scene_role_requalifier_v0

Rôles protégés :

EFFORT_WITHOUT_RESULT_FRICTION
ABSORPTION_SHELF_FRICTION
PROGRESSIVE_FIRST_LEG
PROGRESSIVE_SECOND_LEG_CANDIDATE
CENTER_MIGRATION_DOWN_MEMORY_SHIFT
CENTER_MIGRATION_UP_MEMORY_SHIFT
CORRECTIVE_BREATH_NO_PROGRESS
RETEST_FAILED_REJECTION_NODE
FAILED_REINTEGRATION_NODE
HIGH_REJECTION_NODE
LOW_ZONE_DEFENDED_REACTION
PULLBACK_ABSORBED_RECONSTRUCTION
ZONE_DECISION_PENDING
SCENE_ROLE_REVIEW_REQUIRED

Doctrine :

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.

Limites :

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre directionnel.
Aucune statistique de réussite.
Une scène proxy reste proxy.
Un rôle de scène n'est pas une prédiction.

Prochain geste :
T0141 — B9 Zone Memory Object Builder V0.

Mode recommandé :
GPT Pro standard.
