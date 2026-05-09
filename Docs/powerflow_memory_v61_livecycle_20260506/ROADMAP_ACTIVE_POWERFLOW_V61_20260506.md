# ROADMAP ACTIVE — POWERFLOW V6.1
## Mise à jour : 2026-05-06

---

## 1. Validé

```text
Live Cycle Orchestrator V0.3
Trader Alert State V0.1
Telegram Trader Alert V0.1.2
Relational Gravity Guard P1.2 / P1.2.2 / P2 / P2.1.1
Behavioral Flow Dashboard
```

---

## 2. Priorité P1 — Runtime Health Check renforcé

Créer ou renforcer :

```text
pf_runtime_health_check.py
```

Objectif :

```text
Savoir si PowerFlow est exploitable maintenant.
```

Checks :

```text
powerflow.db existe et n’est pas vide
DB freshness lisible
dashboard_data.json contient behavioral_flow
behavioral_count cohérent queue / cockpit / dashboard
trader_alert_state.json existe
runtime_status.json existe
pipeline_trace.json existe
Telegram config OK si mode Telegram actif
aucun double writer dashboard suspect
relational_gravity.topline_state présent si relational_gravity présent
```

Sortie :

```text
output/runtime_health.json
```

Niveaux :

```text
OK
WARN
FAIL
```

---

## 3. Priorité P2 — Dashboard Trader Panel

Objectif :

```text
Afficher la scène trader dans le dashboard.
```

Source :

```text
output/trader_alert_state.json
```

Ne pas afficher les labels moteur bruts.

Bloc dashboard souhaité :

```text
TRADER ALERT
niveau
titre
message court
âge
freshness
contradictions
action = WATCH / SILENCE
```

---

## 4. Priorité P3 — Core Audit / Registry

Créer :

```text
POWERFLOW_MODULE_REGISTRY.json
pf_core_audit.py
```

Objectif :

```text
Classer le Core.
Savoir qui est actif, legacy, backup, patch, runner, test, fixture, report.
```

À ne pas faire avant audit :

```text
suppression massive
fusion brutale
déplacement de modules actifs
```

---

## 5. Priorité P4 — Git cleanup

Après audit :

```powershell
git status
git checkout -b checkpoint/v61-livecycle
git add .
git commit -m "checkpoint: PowerFlow V6.1 live cycle trader alert telegram"
```

Puis branche nettoyage :

```powershell
git checkout -b chore/core-cleanup-v61
```

---

## 6. Priorité P5 — Boucle live contrôlée

Seulement après Health Check renforcé :

```text
run_powerflow_live_loop.ps1
```

Modes :

```text
OFF
HOT_ONLY
SCALPING
SYSTEM_ONLY
```

Avec :

```text
cooldown
logs JSONL
stop propre
health check
anti-double-writer
```

---

## 7. Priorité P6 — Dashboard State V2

Créer une spec :

```text
PF_COCKPIT_DASHBOARD_STATE_V2_SPEC.md
```

Puis module :

```text
pf_cockpit_dashboard_state.py
```

Objectif :

```text
Un JSON stable pour l’interface.
Moins de patchs directs dashboard_data.json.
```

---

## 8. À ne pas faire maintenant

```text
pas de nouvelle brique marché
pas de TemporalDensity production
pas de Telegram direct depuis pf_*
pas de refonte dashboard HTML lourde
pas de suppression Core sans audit
pas de boucle 30s sans Health Check
```

---

## 9. Phrase directionnelle

```text
PowerFlow a assez de perception pour l’instant.
La priorité V6.1 est l’exploitation live, la clarté, la santé runtime et la réduction de friction trader.
```
