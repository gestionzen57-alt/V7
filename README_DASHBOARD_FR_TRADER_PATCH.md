# Patch Dashboard FR Trader — PowerFlow V7.6.7

## Objectif

Transformer l'affichage Dashboard V7.4 / Reality Board en français trader sans toucher au moteur `pf_*`, sans modifier `powerflow.db`, et sans casser le contrat Dashboard V7.4.

Le patch garde les enums techniques dans les données source, mais remplace les textes visibles dans le DOM.

## Fichiers

```text
dashboard_fr_trader_labels.js   # couche affichage FR trader
patch_dashboard_fr_trader.ps1   # injection automatique dans le HTML dashboard
```

## Installation

Copier les deux fichiers à la racine du repo PowerFlow :

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
Copy-Item C:\chemin\dashboard_fr_trader_labels.js .\ -Force
Copy-Item C:\chemin\patch_dashboard_fr_trader.ps1 .\ -Force
```

Puis lancer :

```powershell
.\patch_dashboard_fr_trader.ps1
```

Si le dashboard n'est pas nommé `dashboard_v74.html`, préciser le fichier :

```powershell
.\patch_dashboard_fr_trader.ps1 -DashboardFile .\dashboard_powerflow_v74.html
```

## Validation visuelle

Après Ctrl+F5 dans le navigateur :

```text
HIGH_ZONE_REJECTION -> Rejet de zone haute
HIGH_ZONE_EXHAUSTION_RISK -> Risque d'épuisement en zone haute
READING_PARTIAL -> Lecture partielle
POST_HIGH_UNWIND -> Déroulement après rejet haut
PAIR_UP -> Pression haussière brute de la paire
PAIR_DOWN -> Pression baissière brute de la paire
LTF_MTF_COUNTERFLOW_ACTIVE -> Contre-respiration LTF/MTF active
WAKE_TRADER -> Réveiller l'attention
DEGRADED -> Lecture dégradée
```

## Validation technique

```powershell
git diff -- dashboard_v74.html dashboard_powerflow_v74.html dashboard_live.html dashboard_fr_trader_labels.js
python dashboard_v74_contract_check.py
```

Si le check contract n'existe pas dans le repo actif, vérifier au minimum :

```powershell
python -m py_compile dashboard_data_normalizer.py
```

## Rollback

Le script crée un backup :

```text
*.bak_fr_trader_YYYYMMDD_HHMMSS
```

Pour revenir en arrière :

```powershell
Copy-Item .\dashboard_v74.html.bak_fr_trader_YYYYMMDD_HHMMSS .\dashboard_v74.html -Force
Remove-Item .\dashboard_fr_trader_labels.js -Force
```

## Risques techniques

```text
- risque de traduction incomplète si un enum n'est pas encore dans PF_FR_LABELS
- risque d'affichage double si le HTML contient déjà une autre couche de traduction
- risque faible sur textarea Telegram : le message visible devient français, ce qui est souhaité pour lecture trader
```

Le patch est volontairement une couche surface. Il ne modifie pas la logique moteur.
