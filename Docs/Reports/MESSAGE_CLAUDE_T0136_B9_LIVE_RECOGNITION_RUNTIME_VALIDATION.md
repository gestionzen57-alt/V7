Claude,

T0136 — B9 Live Recognition Loop Runtime Validation V0 est prêt.

Branche :
feat/t0136-b9-live-recognition-runtime-validation

Commit proposé :
feat(t0136): add B9 live recognition runtime validation v0

Objectif :
Valider que T0135 fonctionne avec les vrais outputs du Core local : T0116 live scene, T0115 similarity query, T0117 false positive context, T0118 terrain synthesis, T0134 French trader report.

Fichiers livrés :

tools/build_t0136_b9_live_recognition_runtime_validation.py
scripts/RUN_T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_FROM_DOWNLOADS.ps1
tests/test_t0136_b9_live_recognition_runtime_validation.py
samples/b9_live_recognition_runtime_validation_v0/*
Docs/Reports/T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_REPORT.md
Docs/Reports/T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_MANIFEST.json
Docs/Reports/COMMANDES_T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION.md
Docs/Reports/MESSAGE_CLAUDE_T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION.md
outputs/b9_live_recognition_runtime_validation_v0/*

Tests :
python -m py_compile tools\build_t0136_b9_live_recognition_runtime_validation.py
python -m pytest tests\test_t0136_b9_live_recognition_runtime_validation.py

Résultat attendu :
2 passed

CLI sample :
python tools\build_t0136_b9_live_recognition_runtime_validation.py --mode sample --sample-dir samples\b9_live_recognition_runtime_validation_v0 --output-dir outputs\b9_live_recognition_runtime_validation_v0_sample

CLI runtime réel :
python tools\build_t0136_b9_live_recognition_runtime_validation.py --mode runtime --core-root . --output-dir outputs\b9_live_recognition_runtime_validation_v0 --execute-t0135

Doctrine :
B9 lit la scène.
B6 compare les films.
T0136 vérifie que la boucle T0135 fonctionne réellement dans le Core local.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre d'exécution.
Aucun taux de réussite.

Prochain geste :
T0137 — B9 Live Recognition Replay Day Validator V0.
