Claude,

T0174 — T0169 Import Path Hotfix V0 est prêt.

Objectif : corriger le bug T0169 où le builder `tools/build_t0169_b9_reality_board_surface_adapter_candidate.py` ne trouvait pas le module racine `pf_t009_reality_board_surface_adapter_candidate.py` quand il était lancé depuis `tools/`.

Patch : ajouter la racine du repo dans `sys.path` avant l'import du module racine.

États possibles :
- PATCH_APPLIED
- ALREADY_PATCHED
- BLOCKED_T0169_BUILDER_NOT_FOUND

Si le builder T0169 n'existe pas dans la branche courante, T0174 ne casse pas l'installation : il produit un rapport `BLOCKED_T0169_BUILDER_NOT_FOUND`.

Tests :
python -m py_compile tools\apply_t0174_t0169_import_path_hotfix.py
python -m pytest tests\test_t0174_t0169_import_path_hotfix.py

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ce hotfix corrige le contrat CLI ; il ne modifie ni DB, ni dashboard live, ni Telegram.
