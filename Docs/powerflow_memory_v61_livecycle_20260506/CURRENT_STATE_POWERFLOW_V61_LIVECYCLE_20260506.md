# CURRENT_STATE — POWERFLOW V6.1 LIVE CYCLE
## Mise à jour : 2026-05-06
**Statut : ACTIVE / VALIDÉ RUNTIME**

---

## 1. État officiel

PowerFlow V6.1 dispose maintenant d’une commande live unique :

```powershell
python .\run_powerflow_live_cycle.py `
  --live `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --pretty `
  --summary
```

Avec Telegram HOT_ONLY optionnel :

```powershell
python .\run_powerflow_live_cycle.py `
  --live `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --telegram-mode HOT_ONLY `
  --pretty `
  --summary
```

Commande validée runtime :

```text
[1/6] CHECK DB                         OK
[2/6] RUN REFRESH                      OK
[3/6] CHECK DASHBOARD                  OK
[4/6] RUN TRADER ALERT                 OK
[5/6] RUN TELEGRAM                     OK
[6/6] WRITE OUTPUTS                    OK
```

Dernier état validé :

```text
LIVE CYCLE OK
behavioral_count = 6
dashboard_ready = True
trader_alert_ready = False
telegram_mode = HOT_ONLY
telegram_verdict = NO_SEND_TRADER_ALERT_NOT_READY
telegram_sent = False
```

Lecture :

```text
La chaîne est saine.
Aucune scène trader fraîche n’est active.
Telegram reste silencieux.
```

---

## 2. Doctrine V6.1

PowerFlow V6.1 n’est pas une nouvelle couche de perception marché.
PowerFlow V6.1 est la couche d’exploitation live.

Objectif :

```text
PowerFlow doit servir le trader.
Le trader ne doit pas être esclave de PowerFlow.
```

Règles :

```text
La machine perçoit.
La machine mesure.
La machine nomme.
La machine alerte.
Le trader filtre.
Le trader décide.
```

Règles spécifiques :

```text
Telegram lit trader_alert_state.json.
Telegram ne lit pas behavioral_alert_queue.json.
Telegram ne lit pas powerflow.db.
Telegram ne lit pas les labels moteur directement.
```

---

## 3. Chaîne active V6.1

```text
powerflow.db
→ run_powerflow_dashboard_refresh_once.py
→ behavioral_alert_queue.json
→ cockpit_agentic_state_v01.json
→ dashboard_data.json
→ pf_trader_alert_state.py / run_trader_alert_state_once.py
→ trader_alert_state.json
→ telegram_trader_alert_v01.py
→ runtime_status.json + pipeline_trace.json
```

Orchestrateur :

```text
run_powerflow_live_cycle.py V0.3
```

---

## 4. Briques validées

### Live Cycle Orchestrator V0.3

Fichier :

```text
run_powerflow_live_cycle.py
```

Rôle :

```text
Commande unique de session.
Vérifie DB.
Rafraîchit dashboard.
Génère Trader Alert State.
Pilote Telegram optionnel.
Écrit runtime_status.json et pipeline_trace.json.
```

Modes Telegram intégrés :

```text
OFF
HOT_ONLY
SCALPING
SYSTEM_ONLY
```

Statut :

```text
VALIDÉ RUNTIME
```

---

### Trader Alert State V0.1

Fichier principal :

```text
pf_trader_alert_state.py
```

Runner :

```text
run_trader_alert_state_once.py
```

Sortie :

```text
output/trader_alert_state.json
```

Rôle :

```text
Transformer le film moteur en scène trader courte, datée, fraîche.
```

Principe :

```text
Moins de 3 lignes.
Français court.
Pas BUY/SELL.
Pas de jargon moteur brut.
HOT behavioral ≠ release confirmed.
Silence si alerte trop vieille.
```

Statut :

```text
PRODUCTION READY
```

---

### Telegram Trader Alert V0.1.2

Fichier :

```text
telegram_trader_alert_v01.py
```

Entrées :

```text
output/trader_alert_state.json
output/runtime_status.json
.env
```

Modes :

```text
OFF
HOT_ONLY
SCALPING
SYSTEM_ONLY
```

Statut :

```text
SCRIPT VALIDÉ + ENVOI RÉEL VALIDÉ
```

Règle :

```text
trader_alert_ready=false → silence Telegram.
runtime_status=OK en SYSTEM_ONLY → silence Telegram.
```

---

### Relational Gravity Guard

Briques déjà intégrées :

```text
P1.2   Relational Gravity Bridge Guard        VALIDÉ
P1.2.2 Topline State                          VALIDÉ
P2     Behavioral Mapper Guard-Aware          VALIDÉ
P2.1   Full Refresh Runner RG-aware           VALIDÉ
P2.1.1 Refresh Cockpit From Queue             VALIDÉ
```

Alerte actuelle :

```text
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

Règle :

```text
Direction relationnelle alignée ≠ leader fiable.
topline_reliable=false → pas de HOT leader.
```

---

## 5. Alertes moteur actuellement agrégées

```text
[HOT]   FIRST_DETACHMENT_WITH_CLEAN_RELAY
[WATCH] COUNTER_RELEASE_ATTEMPT_ALERT
[WATCH] NODE_HEAT_ENERGY_DIVERGENCE
[INFO]  TIGHT_GRAVITY_CLUSTER_ALERT
[INFO]  SAME_ANGLE_CLUSTER_ALERT
[WATCH] RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
```

Ces alertes ne doivent pas partir telles quelles sur Telegram.

Elles doivent être traduites via :

```text
trader_alert_state.json
```

---

## 6. Commandes live utiles

### Live sans Telegram

```powershell
python .\run_powerflow_live_cycle.py `
  --live `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --pretty `
  --summary
```

### Live Telegram HOT_ONLY

```powershell
python .\run_powerflow_live_cycle.py `
  --live `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --telegram-mode HOT_ONLY `
  --pretty `
  --summary
```

### Live Telegram SCALPING

```powershell
python .\run_powerflow_live_cycle.py `
  --live `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --telegram-mode SCALPING `
  --pretty `
  --summary
```

### Live Telegram SYSTEM_ONLY

```powershell
python .\run_powerflow_live_cycle.py `
  --live `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --telegram-mode SYSTEM_ONLY `
  --pretty `
  --summary
```

---

## 7. Point de vigilance

Le système est maintenant exploitable manuellement via commande unique.
Ne pas lancer encore une boucle automatique 30s sans couche anti-spam / health / logs renforcés.

Prochaine priorité :

```text
P1 — Runtime Health Check renforcé
P2 — Dashboard Trader Panel
P3 — Core Audit / Registry / Git cleanup
```

---

## 8. Phrase noyau

```text
PowerFlow V6.1 rafraîchit le cockpit, traduit la scène trader,
et pilote Telegram sans spammer si aucune scène fraîche n’est active.
```
