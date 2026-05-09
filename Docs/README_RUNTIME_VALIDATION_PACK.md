# Pack Runtime Validation — PowerFlow V6

Ce pack sert à tester les séquences DB pour :

```text
Kinematics
Currency Energy
Relational Gravity standalone
Relational Gravity cockpit bridge
P1.2 Bridge Guard
```

## Lancement

Copier `RUN_POWERFLOW_RUNTIME_VALIDATION_KINEMATICS_GRAVITY.ps1` dans :

```text
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
```

Puis lancer :

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
powershell -ExecutionPolicy Bypass -File .\RUN_POWERFLOW_RUNTIME_VALIDATION_KINEMATICS_GRAVITY.ps1
```

Option avec fenêtre cockpit précise :

```powershell
powershell -ExecutionPolicy Bypass -File .\RUN_POWERFLOW_RUNTIME_VALIDATION_KINEMATICS_GRAVITY.ps1 -Start "2026-05-06T08:00:00" -End "2026-05-06T13:30:00"
```

## À me renvoyer

Après exécution, renvoyer le contenu de :

```powershell
Get-Content .\output\runtime_validation_kinematics_gravity_*\runtime_validation_summary.json -Raw
```

## Sécurité

Le script :

```text
ne touche pas capture_bridge.py
n’écrit pas powerflow.db
ne branche pas Telegram
ne patch pas dashboard
ne refactor rien
```
