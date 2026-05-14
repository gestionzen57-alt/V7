# CHECKPOINT — POWERFLOW V7.6.7 FINAL

Date : 2026-05-15  
Statut : **clôture propre**  
HEAD final : `ef632ff`  
Branche : `main`

---

## État final

```text
Reality Board intégré
FR final nettoyé
Telegram Reality Board primary ajouté
Test Telegram réparé
Git distant à jour
Runtime dashboard_data restauré hors Git
```

---

## Derniers commits

```text
ef632ff fix(v767): repair reality telegram primary test
6512018 feat(v767): add reality board primary telegram
ea30df5 fix(v767): polish final French reality board labels
4657f12 merge(v767): reality board minimal live integration
```

---

## Surfaces actives

```text
Dashboard : Reality Board
Telegram : Reality Board primary
Mémoire : B6 film memory
Profils : HTF Analyse / MTF Plan / LTF Action
Langue : français trader-facing
```

---

## Commandes de reprise

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"

git status --short
git log --oneline -5
```

Reality Board seul :

```powershell
python patch\pf_reality_board_state_once.py --symbol GBPUSD
```

Telegram Reality seul :

```powershell
python patch\pf_telegram_reality_board_v767.py --symbol GBPUSD --mode dry-run
```

Cycle complet dry-run :

```powershell
.\run_powerflow_v767_reality_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode dry-run
```

---

## Tests rapides

```powershell
python tests\test_v767_reality_board_telegram_primary.py
python tests\test_v767_final_fr_labels.py
python tests\test_v767_reality_board_cycle_binding.py
```

---

## Point de vigilance

`Core/dashboard_data.json` est runtime.  
Ne pas committer.

Procédure :

```powershell
$backupRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT_LOCAL_BACKUPS"
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item "Core\dashboard_data.json" "$backupRoot\dashboard_data_runtime_$ts.json" -Force
git restore "Core/dashboard_data.json"
```

---

## Prochain chantier conseillé

```text
V7.6.8 : réduire le bruit du Telegram legacy.
```

Objectif :

- legacy V7.6 conservé en debug ;
- Reality Telegram primary = canal principal ;
- moins de bruit console ;
- lecture trader plus nette.
