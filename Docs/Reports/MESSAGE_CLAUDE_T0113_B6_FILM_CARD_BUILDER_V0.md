Claude,

T0113 — B6 Film Card Builder V0 est prêt en pack one-shot Windows.

Branche :
feat/t0113-b6-film-card-builder-v0

Commit proposé :
feat(t0113): add B6 film card builder v0

Fichiers livrés :

tools/build_t0113_b6_film_card_builder_v0.py
scripts/RUN_T0113_B6_FILM_CARD_BUILDER_V0_FROM_DOWNLOADS.ps1
tests/test_t0113_b6_film_card_builder_v0_contract.py
docs/Reports/T0113_B6_FILM_CARD_BUILDER_V0_REPORT.md
docs/Reports/MESSAGE_CLAUDE_T0113_B6_FILM_CARD_BUILDER_V0.md
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_BOARD_V0.csv
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.csv
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.json
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.md
outputs/b6_film_library_v0/B6_FILM_CARD_LOW_TRUST_AUDIT_V0.csv
outputs/b6_film_library_v0/B6_FILM_CARD_REJECTED_RAW_UNAVAILABLE_V0.csv
outputs/b6_film_library_v0/B6_FILM_LIBRARY_V0_MANIFEST.json
outputs/b6_film_library_v0/B6_FILM_LIBRARY_V0.zip

Tests passés :
python -m py_compile toolsuild_t0113_b6_film_card_builder_v0.py
python -m pytest tests	est_t0113_b6_film_card_builder_v0_contract.py

Commande CLI :
python toolsuild_t0113_b6_film_card_builder_v0.py --input-csv outputs6_memory_candidate_board_v0\B6_MEMORY_CANDIDATE_BOARD_V0.csv --output-dir outputs6_film_library_v0_regenerated

Résultat analytique :
Input board rows: 174
Active film cards KEEP/REVIEW: 151
Low trust audit rows: 2
Rejected RAW_UNAVAILABLE rows: 21

Limites / blockers :
- Read-only.
- Aucune écriture powerflow.db.
- Aucune écriture tick_archive.db.
- Aucun dashboard.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilité de succès.
- Les champs base/reaction/projection/judgment sont une normalisation de lecture, pas une nouvelle preuve raw.
- FORCE_SNAPSHOT_DERIVED reste séparé de RECOVERED_EXISTING_B9_SUMMARY.
- NUANCED_BY_RAW n'est jamais durci en CONFIRMED_BY_RAW.
- LOW_TRUST reste audit.
- RAW_UNAVAILABLE est rejeté de la mémoire active.

Prochain geste attendu côté architecte :
Relire et valider la structure des cartes film, puis lancer T0114 — B6 Similarity Index V0.
