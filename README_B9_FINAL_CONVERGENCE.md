# LIVRAISON FINALE — PowerFlow V7.6.7 B9 Convergence

## Objet

Ce pack rassemble la convergence opérationnelle B9 après les travaux :

- Engine + Telegram B9
- Packet Requalifier + B6 Field Memory
- Runtime Integration
- Flask Server B9/B8
- Dashboard Panels B9/B8
- Validation finale + checklist lundi

PowerFlow reste un moteur de perception : il perçoit, mesure, nomme et alerte. Le trader filtre et décide.

## Contenu du pack

```text
Core/RAPPORT_VALIDATION_B9_FINAL.md
Core/CHECKLIST_ACTIVATION_LUNDI_B9.md
Core/test_b9_final_end_to_end.py
Core/test_b9_runtime_10min_dryrun.py
Core/activate_telegram_b9_monday.py
tools/patch_dashboard_b9_b8_panels.py
tools/validate_b9_final_state.py
tests/test_b9_final_convergence_tools.py
Docs/RAPPORT_VALIDATION_B9_FINAL.md
Docs/CHECKLIST_ACTIVATION_LUNDI_B9.md
```

## Installation

Placer ces 3 fichiers dans `C:\Users\User\Downloads` :

```text
b9_final_convergence_v0.zip
install_b9_final_convergence.ps1
git_b9_final_convergence.ps1
```

Puis lancer :

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_b9_final_convergence.ps1"
```

## Validation après installation

Terminal serveur :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python cockpit_server_b9.py
```

Second terminal :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python test_b9_final_end_to_end.py
```

Dashboard :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
python -m http.server 8000
```

Puis ouvrir :

```text
http://localhost:8000/Core/dashboard_powerflow_v74.html
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_b9_final_convergence.ps1"
```

## Garde-fous respectés

- Pas de BUY/SELL.
- Pas de conseil décisionnel.
- Pas d'écriture DB ajoutée.
- Serveur cockpit read-only.
- Fail-soft si DB, nodes, dashboard ou table B8 manquent.
- Telegram reste progressif et désactivé tant que DRY-RUN non validé.

## Statut

Pack final de convergence prêt pour installation locale et validation lundi marché.
