Claude,

T0166 — B9 Live Data Freshness Guard V0 est prêt.

Branche :
feat/t0166-b9-live-data-freshness-guard

Commit proposé :
feat(t0166): add B9 live data freshness guard v0

Objectif :
Qualifier la fraîcheur live avant affichage dashboard / Reality Board / Telegram preview.

Fichiers livrés :
- pf_t009_live_data_freshness_guard.py
- tools/build_t0166_b9_live_data_freshness_guard.py
- scripts/RUN_T0166_B9_LIVE_DATA_FRESHNESS_GUARD_FROM_DOWNLOADS.ps1
- tests/test_t0166_b9_live_data_freshness_guard.py
- samples/b9_live_data_freshness_guard_v0/sample_latest_scene_candidate.json
- Docs/Reports/T0166_B9_LIVE_DATA_FRESHNESS_GUARD_REPORT.md
- Docs/Reports/T0166_B9_LIVE_DATA_FRESHNESS_GUARD_MANIFEST.json
- Docs/Reports/COMMANDES_T0166_B9_LIVE_DATA_FRESHNESS_GUARD.md
- Docs/Reports/MESSAGE_CLAUDE_T0166_B9_LIVE_DATA_FRESHNESS_GUARD.md
- outputs/b9_live_data_freshness_guard_v0/*

Tests :
python -m py_compile pf_t009_live_data_freshness_guard.py tools\build_t0166_b9_live_data_freshness_guard.py
python -m pytest tests\test_t0166_b9_live_data_freshness_guard.py

Commande CLI :
python tools\build_t0166_b9_live_data_freshness_guard.py --core-root . --output-dir outputs\b9_live_data_freshness_guard_v0 --freshness-seconds 300

États produits :
LIVE_FRESH, LIVE_STALE, DB_EMPTY, DB_MISSING, TABLE_MISSING, PROXY_ONLY, RAW_TEXTURE_MISSING, SOURCE_LIVE_UNQUALIFIED, LIVE_FRESH_WITH_LIMITS, LIVE_STALE_WITH_MEMORY_CONTEXT.

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Le guard qualifie la source, il ne décide pas.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard live.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.

Prochain geste :
T0167 — B9/B6 Auto Realignment Runner V0.
