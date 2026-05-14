# GIT APPLY STEPS — POWERFLOW V7.6 BRICK AUDIT

## 0. Branche cible

```bash
git checkout main
git pull origin main
git checkout -b feature/v76-brick-audit
```

## 1. Créer les répertoires

```bash
mkdir -p Docs tests git
```

## 2. Ajouter les fichiers

Créer/copier les fichiers suivants :

```text
Docs/POWERFLOW_BRICK_AUDIT_TERRAIN_V76_FINAL.md
Docs/POWERFLOW_BRICK_TO_PACKET_FIELD_MAPPING_V76.md
Docs/POWERFLOW_BRICK_FALSE_POSITIVES_V76.md
tests/POWERFLOW_BRICK_AUDIT_QA_CASES_V76.md
git/COMMIT_MESSAGE_BRICK_AUDIT_V76.txt
git/GIT_APPLY_STEPS_BRICK_AUDIT_V76.md
```

## 3. Vérifier le diff

```bash
git status
git diff -- Docs tests git
```

## 4. Ajouter au commit

```bash
git add Docs/POWERFLOW_BRICK_AUDIT_TERRAIN_V76_FINAL.md \
        Docs/POWERFLOW_BRICK_TO_PACKET_FIELD_MAPPING_V76.md \
        Docs/POWERFLOW_BRICK_FALSE_POSITIVES_V76.md \
        tests/POWERFLOW_BRICK_AUDIT_QA_CASES_V76.md \
        git/COMMIT_MESSAGE_BRICK_AUDIT_V76.txt \
        git/GIT_APPLY_STEPS_BRICK_AUDIT_V76.md
```

## 5. Commit

```bash
git commit -F git/COMMIT_MESSAGE_BRICK_AUDIT_V76.txt
```

## 6. Push branche feature

```bash
git push origin feature/v76-brick-audit
```

## 7. Contrôle attendu

```text
Aucun fichier dashboard_* modifié.
Aucun fichier telegram_* modifié.
Aucune spine nouvelle créée.
Aucun score global ajouté.
Seulement docs + QA + git instructions.
```
