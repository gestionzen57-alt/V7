Claude,

T0116 — B6 Live Scene Adapter V0 est prêt.

Branche :
feat/t0116-b6-live-scene-adapter-v0

Commit proposé :
feat(t0116): add B6 live scene adapter v0

Fichiers livrés :

tools/build_t0116_b6_live_scene_adapter_v0.py
scripts/RUN_T0116_B6_LIVE_SCENE_ADAPTER_V0_FROM_DOWNLOADS.ps1
tests/test_t0116_b6_live_scene_adapter_v0_contract.py
samples/b6_live_scene_adapter_v0/sample_b9_live_scene_v0.json
docs/Reports/T0116_B6_LIVE_SCENE_ADAPTER_V0_REPORT.md
docs/Reports/T0116_B6_LIVE_SCENE_ADAPTER_V0_MANIFEST.json
docs/Reports/COMMANDES_T0116_B6_LIVE_SCENE_ADAPTER_V0.md
docs/Reports/MESSAGE_CLAUDE_T0116_B6_LIVE_SCENE_ADAPTER_V0.md
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_ADAPTER_REPORT_V0.md
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_ADAPTER_MANIFEST_V0.json
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_ADAPTER_V0.zip

Tests passés :

python -m py_compile tools\build_t0116_b6_live_scene_adapter_v0.py
python -m pytest tests\test_t0116_b6_live_scene_adapter_v0_contract.py

Résultat :
2 passed

Commande CLI :

python tools\build_t0116_b6_live_scene_adapter_v0.py --input-json samples\b6_live_scene_adapter_v0\sample_b9_live_scene_v0.json --output-dir outputs\b6_live_scene_adapter_v0

Sortie :

film_id = LIVE_SCENE_F4930E9A5C
memory_family = DIRECTIONAL_PROGRESS_MEMORY
memory_family_origin = heuristic_text_directional_progress
adapter_state = ADAPTER_READY_HEURISTIC_FAMILY
t0115_compatible = true

Commande de compatibilité T0115 :

python tools\build_t0115_b6_similarity_query_v0.py --similarity-index outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json --query-json outputs\b6_live_scene_adapter_v0\B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json --output-dir outputs\b6_live_scene_adapter_v0_t0115_query_validation --top-k 5

Limites / blockers :

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
T0116 ne reconstruit pas l’index T0114.
T0116 ne compare pas les films directement.
Si memory_family n’est pas fournie par B9, elle est inférée et marquée dans memory_family_origin.

Prochain geste attendu côté architecte :

Valider le format du payload live, puis lancer T0117 — B6 False Positive Context V0 pour expliquer les pièges de similarité.
