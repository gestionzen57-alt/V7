# P0 AUTOMATION — RAPPORT D'INTÉGRATION
**Date : 2026-05-11 | PowerFlow V7.2 | Statut : LIVRÉ — À valider dans Core**

---

## 1. ARCHITECTURE WORKFLOW

Fichiers livrés :

```text
run_p0_full_workflow.ps1
p0_scheduler_config.json
taskscheduler_setup.ps1
```

Objectif : enrichir `run_p0_final_auto.ps1` sans le remplacer.

```text
run_p0_full_workflow.ps1
  → Health Check
  → Run P0 Complete
  → Tracking état précédent / actuel
  → Logs journaliers
  → Dashboard refresh léger
```

---

## 2. HEALTH CHECK

Contrôles :

```text
DB respire : TF1 >= 5 rows depuis -5 minutes
capture_bridge visible : process python contenant capture_bridge.py
output/ existe : création si absent
```

Verdicts :

```text
GREEN  = DB respire + infra lisible
YELLOW = état dégradé mais runnable
RED    = DB non respirante, P0 run skip pour éviter faux verdict
```

---

## 3. COMMANDES DISPONIBLES

### Cycle unique

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
.\run_p0_full_workflow.ps1 -Symbol GBPUSD -Once
```

### Cycle unique + Git si demandé

```powershell
.\run_p0_full_workflow.ps1 -Symbol GBPUSD -Once -Git
```

### Installation Task Scheduler

```powershell
.\taskscheduler_setup.ps1 `
  -TaskName "PowerFlow_P0_Full_Workflow" `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbol GBPUSD
```

---

## 4. LOGS GÉNÉRÉS

```text
logs/p0_run_YYYY-MM-DD.log
logs/p0_last_status.json
```

Format :

```text
[HH:MM:SS UTC] HEALTH: GREEN | DB=GREEN rows=7 | Bridge=GREEN
[HH:MM:SS UTC] STATUS: PASS_CORE_PARTIAL_STRICT at 88%
[HH:MM:SS UTC] STATE_CHANGE: PENDING_DATA_WINDOW -> PASS_STRICT
```

---

## 5. CONFIGURATION SCHEDULER

```json
{
  "enabled": true,
  "interval_minutes": 60,
  "auto_push_git": false,
  "alert_on_status_change": true,
  "log_directory": "logs/",
  "symbol": "GBPUSD"
}
```

---

## 6. ESCALADE SI FAIL MOTEUR DÉTECTÉ

Escalade technique uniquement :

```text
RED DB health
  → Vérifier capture_bridge.py / EA / connexion MT4.

P0_FINAL_DECISION absent
  → Vérifier run_p0_final_auto.ps1 et p0_final_validator.py.

STATUS devient FAIL_STATIC_SIGNATURE
  → Vérifier B4/B5 variance, stale data, output JSON.

STATUS reste PENDING_DATA_WINDOW
  → Continuer accumulation, relancer hourly.
```

---

## 7. MONITORING DASHBOARD SUGGÉRÉ

```text
Ouvrir dashboard_live_v7.2_final.html.
Surveiller :
  P0_FINAL_DECISION.json
  cycle_report.json
  data_quality_guard_ltf.json
  temporal_density_state.json
  spearman_gravity_state.json
```

---

## 8. LIMITATION TRANSPARENTE

Les scripts sont livrés prêts à copier dans `Core/`. Ils doivent être validés localement avec le vrai `powerflow.db`, le vrai `run_p0_final_auto.ps1` et les vrais outputs. Aucun accès runtime local n'était disponible dans cet espace de génération.

---

*P0_AUTOMATION_INTEGRATION_REPORT.md — 2026-05-11*
