# T0113 — B6 Film Card Builder V0 — Rapport d'installation

## Résumé

T0113 transforme le `B6_MEMORY_CANDIDATE_BOARD_V0.csv` en cartes film comparables pour B6.

Le board B6 sélectionne les scènes. T0113 construit une mémoire exploitable sous forme de cartes film.

```text
B9 lit la scène.
T0112 qualifie la fiabilité.
B6 mémorise des films comparables.
T0113 fabrique les cartes film.
```

## Doctrine

```text
B6 ne prédit pas.
B6 compare des films.
Une carte film conserve une scène passée avec sa provenance, son accord raw et ses limites.
```

## Entrée

```text
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_BOARD_V0.csv
```

## Sorties

```text
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.csv
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.json
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.md
outputs/b6_film_library_v0/B6_FILM_CARD_LOW_TRUST_AUDIT_V0.csv
outputs/b6_film_library_v0/B6_FILM_CARD_REJECTED_RAW_UNAVAILABLE_V0.csv
outputs/b6_film_library_v0/B6_FILM_LIBRARY_V0_MANIFEST.json
outputs/b6_film_library_v0/B6_FILM_LIBRARY_V0.zip
```

## Counts générés

```text
Input board rows: 174
Active film cards KEEP/REVIEW: 151
Low trust audit rows: 2
Rejected RAW_UNAVAILABLE rows: 21
```

## Tests

```powershell
python -m py_compile toolsuild_t0113_b6_film_card_builder_v0.py
python -m pytest tests	est_t0113_b6_film_card_builder_v0_contract.py
```

## CLI

```powershell
python toolsuild_t0113_b6_film_card_builder_v0.py `
  --input-csv "outputs6_memory_candidate_board_v0\B6_MEMORY_CANDIDATE_BOARD_V0.csv" `
  --output-dir "outputs6_film_library_v0_regenerated"
```

## Contraintes respectées

```text
no DB write
no dashboard
no Telegram
no BUY/SELL
no probability of success
FORCE_SNAPSHOT_DERIVED != RECOVERED_EXISTING_B9_SUMMARY
NUANCED_BY_RAW reste nuancé
RAW_UNAVAILABLE rejeté de la mémoire active
LOW_TRUST conservé en audit
```

## Prochaine brique

```text
T0114 — B6 Similarity Index V0
```

Objectif : comparer une scène actuelle aux cartes film, afficher similarités, différences et risques techniques de faux positif, sans prédiction.
