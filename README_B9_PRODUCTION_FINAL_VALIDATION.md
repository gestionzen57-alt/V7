# B9 Production Final Validation Pack

## Objectif

Automatiser la validation E2E finale B9 et préparer le push Git final.

## Fichiers livrés

- `Core/validate_b9_production_final.py`
- `Core/run_b9_production_e2e.ps1`
- `Core/docs/Reports/RAPPORT_VALIDATION_B9_PRODUCTION_FINAL_TEMPLATE.md`
- `Core/docs/Checklists/CHECKLIST_ACTIVATION_TELEGRAM_B9_FINAL.md`
- `tests/test_b9_production_final_validation_tools.py`

## Validation rapide avec Flask déjà lancé

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python validate_b9_production_final.py
```

## Validation complète avec scheduler 5 min

Terminal 1 :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python cockpit_server_b9.py
```

Terminal 2 :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python validate_b9_production_final.py --run-scheduler
```

Ou :

```powershell
powershell -ExecutionPolicy Bypass -File ".\run_b9_production_e2e.ps1" -RunScheduler5Min
```

## Sorties

- `Core/docs/Reports/B9_PRODUCTION_FINAL_VALIDATION_RESULT.json`
- `Core/docs/Reports/RAPPORT_VALIDATION_B9_PRODUCTION_FINAL.md`
