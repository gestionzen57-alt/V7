# GIT APPLY STEPS — POWERFLOW V7.6 TERRAIN GRAMMAR

## 0. Branche

```bash
git checkout -b feature/v76-terrain-grammar
```

## 1. Créer les dossiers

```bash
mkdir -p Docs schema git
```

## 2. Copier les fichiers

Depuis le pack livré, copier :

```bash
cp Docs/POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md Docs/
cp Docs/POWERFLOW_TERRAIN_LEXICON_UPDATES_V76.md Docs/
cp Docs/POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md Docs/
cp schema/terrain_packet_enums_v76.json schema/
cp git/COMMIT_MESSAGE_GRAMMAR_V76.txt git/
cp git/GIT_APPLY_STEPS_GRAMMAR_V76.md git/
```

Alternative si le patch est disponible :

```bash
git apply POWERFLOW_V76_TERRAIN_GRAMMAR.patch
```

## 3. Vérifier le JSON

```bash
python -m json.tool schema/terrain_packet_enums_v76.json > /tmp/terrain_packet_enums_v76.validated.json
```

## 4. Vérifier le diff

```bash
git diff -- Docs schema git
```

## 5. Ajouter et committer

```bash
git add Docs/POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md \
        Docs/POWERFLOW_TERRAIN_LEXICON_UPDATES_V76.md \
        Docs/POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md \
        schema/terrain_packet_enums_v76.json \
        git/COMMIT_MESSAGE_GRAMMAR_V76.txt \
        git/GIT_APPLY_STEPS_GRAMMAR_V76.md

git commit -F git/COMMIT_MESSAGE_GRAMMAR_V76.txt
```

## 6. Push optionnel

Ne pas pousser sur `main`.

```bash
git push origin feature/v76-terrain-grammar
```

## 7. Contrôle attendu

```text
OK si :
- aucun packet terrain ne dépend de PAIR_UP/PAIR_DOWN seul comme message principal ;
- data_visibility est obligatoire ;
- price_confirmation est obligatoire ;
- UNKNOWN / HONEST_UNKNOWN / READING_PARTIAL existent ;
- aucun buy/sell/entry/exit/target/stop n'est introduit ;
- aucune activation Telegram ;
- aucune nouvelle spine.
```
