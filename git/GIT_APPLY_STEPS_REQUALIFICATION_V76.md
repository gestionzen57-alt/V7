# GIT APPLY STEPS — POWERFLOW PACKET REQUALIFICATION V7.6

Repo cible : `gestionzen57-alt/V7`

Branche recommandée : `feature/v76-packet-requalification`

## 1. Préparer la branche

```bash
git checkout -b feature/v76-packet-requalification
mkdir -p Docs schema/terrain_packet_examples patch tests git
```

## 2. Copier les fichiers

Copier les fichiers livrés aux chemins suivants :

```text
Docs/POWERFLOW_PACKET_REQUALIFICATION_RULES_V76_FINAL.md
schema/terrain_packet_v76.schema.json
schema/terrain_packet_examples/gbpusd_20260514_lower_zone_partial.json
patch/pf_packet_requalification_once.py
patch/pf_terrain_context_once.py
patch/pf_film_memory_reader_once.py
tests/test_packet_requalification_rules_v76.py
tests/POWERFLOW_TERRAIN_QA_GRID_V76.md
git/COMMIT_MESSAGE_REQUALIFICATION_V76.txt
git/GIT_APPLY_STEPS_REQUALIFICATION_V76.md
```

Ou appliquer le diff livré :

```bash
git apply powerflow_v76_packet_requalification.diff
```

## 3. Lancer les tests

```bash
python -m unittest tests/test_packet_requalification_rules_v76.py
```

Option pytest si disponible :

```bash
python -m pytest tests/test_packet_requalification_rules_v76.py
```

## 4. Tester le CLI minimal

```bash
python patch/pf_packet_requalification_once.py \
  --input schema/terrain_packet_examples/gbpusd_20260514_lower_zone_partial.json \
  --output /tmp/terrain_packet.json \
  --audit /tmp/terrain_packet_audit.jsonl

cat /tmp/terrain_packet.json
cat /tmp/terrain_packet_audit.jsonl
```

## 5. Commit

```bash
git add Docs/POWERFLOW_PACKET_REQUALIFICATION_RULES_V76_FINAL.md \
  schema/terrain_packet_v76.schema.json \
  schema/terrain_packet_examples/gbpusd_20260514_lower_zone_partial.json \
  patch/pf_packet_requalification_once.py \
  patch/pf_terrain_context_once.py \
  patch/pf_film_memory_reader_once.py \
  tests/test_packet_requalification_rules_v76.py \
  tests/POWERFLOW_TERRAIN_QA_GRID_V76.md \
  git/COMMIT_MESSAGE_REQUALIFICATION_V76.txt \
  git/GIT_APPLY_STEPS_REQUALIFICATION_V76.md

git commit -F git/COMMIT_MESSAGE_REQUALIFICATION_V76.txt
```

## 6. Push branche

```bash
git push origin feature/v76-packet-requalification
```

## 7. Contrôle avant PR

Vérifier :

```text
raw_bias conservé
qualified_bias présent
packet_quality présent
price_confirmation présent
data_visibility visible
technical_risks array
evidence_refs array
B3+B2 jamais RELEASE_VALIDATED
B3+B4+P1 validé seulement avec prix acceptable + B7 non failed + data acceptable
aucune dépendance dashboard
aucune dépendance Telegram
aucune stratégie trading
```
