# B6 Memory Candidate Board V0 — Livraison one-shot Windows

## Résumé mission

Livraison adaptée à l'environnement local Windows :

```text
Repo core    : C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
Downloads   : C:\Users\User\Downloads
Branche     : feat/b6-memory-candidate-board-v0
Commit msg  : feat(b6): add memory candidate board v0 deliverable
```

Cette livraison installe le générateur B6, le rapport Markdown, les CSV analytiques, un test de contrat, un runner PowerShell, un patch Git et un script Git commit + push.

## Doctrine verrouillée

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
B6 ne prédit pas.
B6 compare des films.
```

Aucun BUY/SELL. Aucune probabilité de succès. Aucun dashboard. Aucun Telegram. Aucune écriture `powerflow.db`. Aucune écriture `tick_archive.db`.

## Résultat analytique livré

```text
Total scenes: 174
FORCE_SNAPSHOT_DERIVED: 122
RECOVERED_EXISTING_B9_SUMMARY: 52
CONFIRMED_BY_RAW: 40
NUANCED_BY_RAW: 113
RAW_UNAVAILABLE: 21
B6_KEEP_CANDIDATE: 138
B6_REVIEW_CANDIDATE: 13
B6_LOW_TRUST_CANDIDATE: 2
B6_REJECT_RAW_UNAVAILABLE: 21
```

## Fichiers installés dans Core

```text
tools/build_b6_memory_candidate_board_v0_from_uploads.py
scripts/RUN_B6_MEMORY_CANDIDATE_BOARD_V0_FROM_DOWNLOADS.ps1
tests/test_b6_memory_candidate_board_v0_contract.py
docs/Reports/B6_MEMORY_CANDIDATE_BOARD_V0_INSTALLATION_REPORT.md
docs/Reports/B6_MEMORY_CANDIDATE_BOARD_V0.md
docs/Reports/B6_MEMORY_CANDIDATE_BOARD_V0_MANIFEST.json
docs/Reports/MESSAGE_CLAUDE_B6_MEMORY_CANDIDATE_BOARD_V0_FINAL.md
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_BOARD_V0.md
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_BOARD_V0.csv
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_KEEP.csv
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_REVIEW.csv
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_LOW_TRUST.csv
outputs/b6_memory_candidate_board_v0/B6_MEMORY_REJECTED_RAW_UNAVAILABLE.csv
outputs/b6_memory_candidate_board_v0/B6_MEMORY_CANDIDATE_BOARD_V0_MANIFEST.json
```

Le ZIP analytique `B6_MEMORY_CANDIDATE_BOARD_V0_OUTPUTS_ONLY.zip` reste dans le pack et n'est pas ajouté au commit par défaut.

## Commande installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_b6_memory_candidate_board_v0.ps1"
```

## Commande Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_b6_memory_candidate_board_v0.ps1"
```

## Tests lancés par install et Git

```powershell
python -m py_compile tools\build_b6_memory_candidate_board_v0_from_uploads.py
python -m pytest tests\test_b6_memory_candidate_board_v0_contract.py
```

## CLI de validation / régénération

Si les ZIPs source sont présents dans Downloads :

```powershell
python tools\build_b6_memory_candidate_board_v0_from_uploads.py `
  --force-zip "C:\Users\User\Downloads\B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.zip" `
  --recovered-zip "C:\Users\User\Downloads\B9_RAW_CALIBRATION_OUTPUTS_20260506_0001_0055_SHIFT0_RAW.zip" `
  --output-dir "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\outputs\b6_memory_candidate_board_v0_regenerated"
```

## Limites / blockers

- Les scènes `RAW_UNAVAILABLE` restent exclues de la mémoire active.
- Les scènes `B6_LOW_TRUST_CANDIDATE` sont conservées pour audit, pas pour mémoire active.
- `FORCE_SNAPSHOT_DERIVED` reste une famille reconstruite, jamais présentée comme recovered summary existant.
- `NUANCED_BY_RAW` n'est jamais durci en `CONFIRMED_BY_RAW`.
- Les outputs CSV sont des livrables analytiques ; le script Git les ajoute explicitement car cette mission les demande.

## Prochain geste architecte

Relire la branche `feat/b6-memory-candidate-board-v0`, vérifier que le board nourrit bien la prochaine brique B6 film comparison, puis décider si les CSV doivent rester versionnés ou être déplacés vers une archive d'outputs.
