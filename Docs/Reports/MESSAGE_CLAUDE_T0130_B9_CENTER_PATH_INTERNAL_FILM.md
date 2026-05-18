Claude,

T0130 — B9 Center Path Internal Film V0 est prêt.

Branche :
feat/t0130-b9-center-path-internal-film

Commit proposé :
feat(t0130): add B9 center path internal film

Objectif :
Faire lire à B9 le film interne du centre, pas seulement `center_start -> center_end`.

Fichiers livrés :

pf_t009_center_path_internal_film.py
tools/build_t0130_b9_center_path_internal_film.py
scripts/RUN_T0130_B9_CENTER_PATH_INTERNAL_FILM_FROM_DOWNLOADS.ps1
tests/test_t0130_b9_center_path_internal_film.py
samples/b9_center_path_internal_film_v0/sample_t009_sequence_summary_center_path.json
Docs/Reports/T0130_B9_CENTER_PATH_INTERNAL_FILM_REPORT.md
Docs/Reports/T0130_B9_CENTER_PATH_INTERNAL_FILM_MANIFEST.json
Docs/Reports/COMMANDES_T0130_B9_CENTER_PATH_INTERNAL_FILM.md
Docs/Reports/MESSAGE_CLAUDE_T0130_B9_CENTER_PATH_INTERNAL_FILM.md
outputs/b9_center_path_internal_film_v0/*

Tests :

python -m py_compile pf_t009_center_path_internal_film.py tools\build_t0130_b9_center_path_internal_film.py
python -m pytest tests\test_t0130_b9_center_path_internal_film.py

Résultat attendu :
2 passed

Commande CLI :

python tools\build_t0130_b9_center_path_internal_film.py --sequence-summary-json samples\b9_center_path_internal_film_v0\sample_t009_sequence_summary_center_path.json --output-dir outputs\b9_center_path_internal_film_v0

Résultat sample :

moments = 5
total_missing_required_fields = 0
forbidden_language_hit_count = 0
preserved_field_changes = 0

États protégés :

CENTER_PATH_VISIBLE
CENTER_PATH_PROXY_EXTREMES
CENTER_PATH_START_END_ONLY
CENTER_PATH_NOT_VISIBLE
STRAIGHT_PROGRESS_UP / DOWN
STAIR_STEP_PROGRESS_UP / DOWN
ROUND_TRIP_NO_PROGRESS
SPIKE_AND_RETRACE
CENTER_DRIFT_UP / DOWN
CENTER_LOCKED

Doctrine :

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Ne lis pas l’absorption comme une direction.
Lis où elle déplace la mémoire.

Limites :

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre d’exécution.
Aucune probabilité de succès.
Les chemins proxy ne deviennent jamais une chronologie raw.

Prochain geste :
T0131 — B9 Memory Brief Injector V0.
Mode recommandé : GPT Pro étendue.
