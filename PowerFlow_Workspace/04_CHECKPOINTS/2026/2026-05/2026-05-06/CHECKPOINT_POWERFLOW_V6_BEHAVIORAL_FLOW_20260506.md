# CHECKPOINT POWERFLOW V6 — 2026-05-06
## Node V0.8.2 / Behavioral Flow / Dashboard Live

**Statut : VALIDÉ RUNTIME + AFFICHAGE LIVE**

---

## 1. État actuel

PowerFlow affiche maintenant en live :

```text
BEHAVIORAL FLOW
HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
FIRST_DETACHMENT_WITH_CLEAN_RELAY
```

Chaîne active :

```text
temporal_node_state.json
→ behavioral_alert_queue.json
→ cockpit_agentic_state_v01.json
→ dashboard_data.json
→ dashboard_live.html
```

---

## 2. Décisions actées

```text
Energy ≠ direction
Energy ≠ signal
Node Heat ≠ Currency Energy
Energy qualifie release_state mais ne crée pas release_state
HOT behavioral ≠ release confirmée
dashboard_sync_agent doit être la dernière étape avant dashboard_data.json final
```

---

## 3. Fichiers validés / créés

```text
pf_temporal_node_state.py
→ Node V0.8.2 avec energy_release_alignment / energy_context

pf_behavioral_alert_mapper.py
→ Mapper V0.8.2.1 avec EnergyView

run_behavioral_alert_mapper_once.py
→ produit behavioral_alert_queue.json

cockpit_agentic_state_v01.py
→ lit behavioral_alert_queue.json

dashboard_sync_agent_v01.py
→ produit dashboard_data.json enrichi

dashboard_live.html
→ affiche Behavioral Flow en grille et focus agentic

dashboard_server.py
→ applique behavioral sync avant save_json

run_powerflow_dashboard_refresh_once.py
→ runner full refresh en ordre forcé
```

---

## 4. Tests validés

```text
pf_behavioral_alert_mapper.py : py_compile OK
test_behavioral_alert_mapper.py : 50/50 tests passés

behavioral_queue :
behavioral_count = 5
degraded_count = 0

cockpit :
top_alert = FIRST_DETACHMENT_WITH_CLEAN_RELAY
top_level = HOT

dashboard_sync :
behavioral_flow_status = HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT

dashboard_server :
dashboard_data.json contient behavioral_flow = True

dashboard_live :
Behavioral Flow visible sur http://localhost:8081/dashboard_live.html
```

---

## 5. Lecture runtime validée

```text
RAW_NODE_BIRTH
LTF_BIRTH_INSIDE_VISUAL_HTF_STORY
HOT_NODE
```

Behavioral Flow :

```text
M1_FIRST_DETACHMENT_USD_DOWN
M5 relay clean
COUNTER_RELEASE_ATTEMPT
GBP=ENERGY_WEAK
USD=ENERGY_WEAK
relation=DIVERGENT
field=ENERGY_THIN_OR_MIXED
```

Alertes :

```text
[HOT]   FIRST_DETACHMENT_WITH_CLEAN_RELAY
[WATCH] COUNTER_RELEASE_ATTEMPT_ALERT
[WATCH] NODE_HEAT_ENERGY_DIVERGENCE
[INFO]  TIGHT_GRAVITY_CLUSTER_ALERT
[INFO]  SAME_ANGLE_CLUSTER_ALERT
```

Interprétation :

```text
Détachement fort.
Relais M5 propre.
Mais release non confirmée.
Energy GBP/USD faible / divergente.
Le cockpit alerte fort, mais qualifie proprement.
```

---

## 6. Incident résolu

Problème :

```text
Behavioral Flow alternait avec "en attente de dashboard_sync_agent".
```

Cause :

```text
Deux process écrivaient dashboard_data.json.
Un écrivait la version enrichie.
Un écrivait la version brute.
```

Correction :

```text
Ancien process sur port 8080 identifié.
Serveur propre utilisé sur port 8081.
```

Commande utile :

```powershell
netstat -ano | findstr :8080
taskkill /PID 16900 /F
```

---

## 7. Commandes utiles

Serveur stable :

```powershell
python .\dashboard_server.py --serve --port 8081
```

Full refresh complet :

```powershell
python .\run_powerflow_dashboard_refresh_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --start 2026-05-06T09:00:00 `
  --end 2026-05-06T10:30:00 `
  --visual-htf-story confirmed `
  --pretty `
  --summary
```

Refresh rapide :

```powershell
python .\run_powerflow_dashboard_refresh_once.py `
  --skip-cockpit `
  --pretty `
  --summary
```

Vérifier behavioral_flow :

```powershell
python -c "import json; d=json.load(open('dashboard_data.json', encoding='utf-8')); print('behavioral_flow' in d); print(d.get('behavioral_flow', {}).get('status'))"
```

---

## 8. Lexique à intégrer

```text
ENERGY_RELEASE_ALIGNMENT
ENERGY_CONTEXT
ENERGY_VIEW
BEHAVIORAL_FLOW
HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
PAIR_ENERGY_NOT_CONFIRMED
ENERGY_THIN_OR_MIXED
NODE_HEAT_ENERGY_DIVERGENCE
FIRST_DETACHMENT_WITH_CLEAN_RELAY
```

---

## 9. Prochaines actions

```text
P1 — Garder un seul dashboard_server actif.
P2 — Sauvegarder ce checkpoint dans Drive.
P3 — Créer PATCH_LEXIQUE_BEHAVIORAL_FLOW_V082_20260506.md.
P4 — Ajouter plus tard --recent-minutes auto au full refresh runner.
P5 — Auditer plus tard run_battlefield_map.py sur fenêtres anciennes.
```

---

## 10. Questions ouvertes

```text
Faut-il créer un badge plus court que HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT ?

Faut-il afficher "release confirmed / not confirmed" comme sous-bloc visuel séparé ?

Faut-il brancher plus tard Behavioral Flow vers Telegram ?

Faut-il auditer run_battlefield_map.py sur fenêtres anciennes ?
```

---

## 11. Verdict

```text
VALIDÉ.
PowerFlow dispose maintenant d’une lecture live comportementale :
Node / Relay / Release / Energy / Clusters.
```

Phrase checkpoint :

```text
Le dashboard ne montre plus seulement qu’un node est né.
Il montre pourquoi la scène mérite attention,
ce qui la soutient,
ce qui la contredit,
et pourquoi la release n’est pas encore confirmée.
```
