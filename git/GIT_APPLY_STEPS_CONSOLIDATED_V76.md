# GIT APPLY STEPS — POWERFLOW V7.6 CONSOLIDATED PACK

## 1. Créer la branche

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feature/v76-terrain-consolidated
```

## 2. Copier les fichiers

Depuis le dossier `POWERFLOW_V76_CONSOLIDATED_DELIVERY_PACK`, copier dans la racine du repo :

```bash
cp -R Docs schema data patch tests git README_POWERFLOW_V76_CONSOLIDATED_DELIVERY_PACK.md /path/to/V7/
```

Ou appliquer le patch consolidé si fourni :

```bash
git apply POWERFLOW_V76_CONSOLIDATED.patch
```

## 3. Vérifier le patch minimal

```bash
python tests/test_packet_requalification_rules_v76.py
python -m py_compile patch/*.py
python -m json.tool schema/terrain_packet_enums_v76.json >/tmp/terrain_packet_enums_v76.checked.json
python -m json.tool schema/terrain_packet_v76.schema.json >/tmp/terrain_packet_v76_schema.checked.json
python -m json.tool schema/terrain_packet_examples/gbpusd_20260514_lower_zone_partial.json >/tmp/terrain_packet_example.checked.json
```

Résultat attendu :

```text
Ran 13 tests
OK
```

## 4. Commit

```bash
git add Docs schema data patch tests git README_POWERFLOW_V76_CONSOLIDATED_DELIVERY_PACK.md
git commit -F git/COMMIT_MESSAGE_CONSOLIDATED_V76.txt
```

## 5. Push branche

```bash
git push origin feature/v76-terrain-consolidated
```

## 6. Interdits avant QA terrain

Ne pas activer Telegram.
Ne pas brancher l'Alert Gate comme source sémantique.
Ne pas afficher `PAIR_UP` / `PAIR_DOWN` seul en cockpit principal.
Ne pas merger sur main avant replay des 7 journées GBPUSD.
