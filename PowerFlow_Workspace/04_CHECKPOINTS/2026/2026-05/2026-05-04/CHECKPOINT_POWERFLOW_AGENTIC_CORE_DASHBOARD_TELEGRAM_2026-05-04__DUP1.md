# CHECKPOINT — PowerFlow V6 Agentic Core / Dashboard V06 / Telegram Nodes

**Date :** 2026-05-04  
**Statut :** VALIDÉ SESSION  
**Dernière étape validée :** Telegram Agentic Nodes V0.1 + Dashboard Agentic V06  
**Phrase de reprise :** PowerFlow a maintenant une chaîne vivante DB → Agents → Dashboard → Telegram.

---

## 1. État actuel

PowerFlow dispose maintenant d’un pipeline opérationnel :

```text
powerflow.db
→ DBVisionGuard
→ FlowEventExtractor
→ SceneNamer
→ FractalWindowEngine
→ FlowEventExtractor V0.2.1 Extended
→ cockpit_agentic_state_v01.json
→ dashboard_live_agentic_v06.html
→ Telegram Agentic Nodes V0.1
```

Statut :

```text
OK / fonctionnel / validé par tests locaux
```

---

## 2. Décisions actées

### 2.1 Le vrai 4e agent runtime est FractalWindowEngine

```text
WeeklyAgentScan = outil Lab / scanner historique
FractalWindowEngine = 4e agent runtime
```

Chaîne officielle :

```text
1. DBVisionGuard
2. FlowEventExtractor V0.1.3
3. SceneNamer V0.1.0
4. FractalWindowEngine V0.1.1
```

---

### 2.2 LAB_004 validé

Nom :

```text
LAB_004_TEMPORAL_WINDOW_FRACTAL_IMBRICATION
```

Statut :

```text
VALIDÉ TRADER
```

Concept central :

```text
Un node n’est pas seulement un croisement.
C’est un ancrage énergétique qui permet à plusieurs timeframes de s’imbriquer dans une histoire supérieure.
```

---

### 2.3 DB jeune mais exploitable

La DB V2 est jeune, donc :

```text
DB_HTF_SILENT_OR_FLAT
```

ne doit pas annuler :

```text
VISUAL_HIGHER_STORY_CONFIRMED
```

FractalWindowEngine V0.1.1 gère cette séparation via :

```text
--visual-htf-story confirmed
```

---

### 2.4 Extended V0.2.1 calibré

Flags ajoutés :

```text
MICRO_WINDOW_ACTIVE_WEAK
MICRO_WINDOW_ACTIVE_STRONG
```

Règle :

```text
WEAK  = M1/M5 node + price lag ou pression partielle
STRONG = M1/M5 node + price lag + volume/pip pressure
```

---

### 2.5 Dashboard V06 validé

Version actuelle :

```text
dashboard_live_agentic_v06.html
```

Fonctions :

```text
sticky scène vivante
auto-focus Agentic
NEXT WATCH renforcé
mode focus
cockpit field repliable
extended V0.2 visible
```

---

### 2.6 Telegram validé

Fichiers :

```text
telegram_agentic_nodes_v01.py
run_telegram_agentic_nodes_once.py
RUN_TELEGRAM_AGENTIC_NODES_LOOP.ps1
```

Dry-run :

```text
OK
```

Anti-doublon :

```text
OK
```

Message HOT :

```text
OK
```

---

## 3. Commandes de reprise

### 3.1 Générer le JSON cockpit

```powershell
python run_cockpit_agentic_state_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --visual-htf-story confirmed --out output/cockpit_agentic_state_v01.json --pretty
```

### 3.2 Tester Telegram sans envoyer

```powershell
python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json --dry-run
```

### 3.3 Envoyer Telegram

```powershell
$env:TELEGRAM_BOT_TOKEN="TON_TOKEN"
$env:TELEGRAM_CHAT_ID="TON_CHAT_ID"

python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json
```

### 3.4 Boucle Telegram

```powershell
.\RUN_TELEGRAM_AGENTIC_NODES_LOOP.ps1 -JsonPath output/cockpit_agentic_state_v01.json -SleepSeconds 15 -MinSeverity watch
```

### 3.5 Dashboard

```text
http://localhost:8080/dashboard_live.html?v=6
```

---

## 4. Derniers résultats validés

### FractalWindowEngine

```text
FRACTAL_STATE: LTF_BIRTH_INSIDE_VISUAL_HTF_STORY
TEMPORAL_STATE: TIME_COMPRESSED
HTF_RELATION: DB_HTF_SILENT_OR_FLAT
HIGHER_STORY: VISUAL_HIGHER_STORY_CONFIRMED
```

### Extended

```text
EXTENDED MICRO WINDOW ACTIVE WEAK
SPREAD_CLEAN_FIELD
NZD_AVAILABLE
M1_NODE_BIRTH
PRICE_LAG_AT_NODE
```

### Telegram

```text
SEVERITY: hot
SHOULD_SEND: True
DUPLICATE: False puis True
VERDICT: DRY_RUN_NOT_SENT puis NO_SEND_DUPLICATE
```

---

## 5. Questions ouvertes

```text
1. Automatiser la fenêtre --start / --end en recent-minutes.
2. Créer un RUN_AGENTIC_LIVE_STACK.ps1.
3. Décider si Telegram doit envoyer seulement HOT ou aussi WATCH.
4. Faire Dashboard V07 avec timeline visuelle.
5. Mettre à jour lexique officiel avec les nouveaux termes.
```

---

## 6. Prochaine action prioritaire

Priorité recommandée :

```text
P0 — créer RUN_AGENTIC_LIVE_STACK.ps1
```

Objectif :

```text
une seule commande lance :
- génération JSON agentic
- boucle Telegram
- dashboard server si besoin
```

Deuxième priorité :

```text
P1 — AutoWindow recent-minutes pour ne plus entrer start/end à la main
```

---

## 7. Statut final

```text
PowerFlow Agentic Core        VALIDÉ
Dashboard Agentic V06         VALIDÉ
Telegram Agentic Nodes V0.1   VALIDÉ
Anti-spam Telegram            VALIDÉ
Extended V0.2.1               VALIDÉ
DB V2                         ACTIVE MAIS JEUNE
```

Fin checkpoint.
