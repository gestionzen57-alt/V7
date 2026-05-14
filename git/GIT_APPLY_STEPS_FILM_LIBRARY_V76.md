# GIT APPLY STEPS — POWERFLOW FILM LIBRARY V7.6

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feature/v76-film-library

mkdir -p Docs data/film_memory tests git

# Copier les fichiers livrés :
# Docs/POWERFLOW_FILM_LIBRARY_GBPUSD_V76_FINAL.md
# Docs/POWERFLOW_FILM_MEMORY_CARDS_GBPUSD_V76.md
# Docs/POWERFLOW_FILM_PATTERN_INDEX_V76.md
# data/film_memory/gbpusd_v76_film_memory_cards.json
# tests/POWERFLOW_GBPUSD_FILM_LIBRARY_QA_V76.md
# git/COMMIT_MESSAGE_FILM_LIBRARY_V76.txt
# git/GIT_APPLY_STEPS_FILM_LIBRARY_V76.md

git status --short
git add Docs/POWERFLOW_FILM_LIBRARY_GBPUSD_V76_FINAL.md         Docs/POWERFLOW_FILM_MEMORY_CARDS_GBPUSD_V76.md         Docs/POWERFLOW_FILM_PATTERN_INDEX_V76.md         data/film_memory/gbpusd_v76_film_memory_cards.json         tests/POWERFLOW_GBPUSD_FILM_LIBRARY_QA_V76.md         git/COMMIT_MESSAGE_FILM_LIBRARY_V76.txt         git/GIT_APPLY_STEPS_FILM_LIBRARY_V76.md

git commit -F git/COMMIT_MESSAGE_FILM_LIBRARY_V76.txt
git push origin feature/v76-film-library
```

## Contrôle attendu

```bash
git diff --stat main..feature/v76-film-library
```

Attendu : 7 fichiers ajoutés, documentation + JSON memory + QA uniquement.
