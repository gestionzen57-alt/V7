# CHECKPOINT — PowerFlow Zone / Battlefield / Cockpit

Date : 2026-05-02  
Checkpoint : après validation de `run_cockpit_field.py`

---

## 1. État global

Statut : **VALIDÉ**

La chaîne suivante fonctionne :

```text
zone dynamique
→ mémoire historique
→ film de zone
→ stack fractal
→ session story
→ brief Cockpit
→ battlefield map
→ cockpit field court
```

Dernière sortie validée :

```text
COCKPIT FIELD
FIELD: TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US | score=257.063
DOMINANT: release=CAD HIGH/GBP HIGH | prep=EUR HIGH/CHF HIGH/AUD HIGH/JPY HIGH
OPPOSITE/CONTEXT: prep=EUR LOW/GBP LOW/CHF LOW/CAD LOW/JPY LOW
CONTESTED_WINDOW: HIGH=CAD/GBP/EUR/CHF/AUD/JPY vs LOW=EUR/GBP/CHF/CAD/JPY
BIPOLAR_FOCUS: EUR | MICRO_VS_HTF_ROTATION_CONTEST | HIGH_TF=M1,M5 vs LOW_TF=M15,M30
BIPOLAR_LIST: EUR:PREPH/PREPL | GBP:RELH/PREPL | CAD:RELH/PREPL | CHF:PREPH/PREPL
```

---

## 2. Fichiers validés

### Zone dynamics

```text
pf_zone_dynamics.py
```

Validé avec :

```text
EARLY_EXTREME
PRE_EXTREME
ACCUMULATING
LEAKING
RUPTURE
```

---

### Logger zone

```text
pf_zone_context_logger.py
run_zone_context_logger_once.py
run_zone_context_logger_history.py
```

Validé avec :

```text
zone_diagnostics
1368 lignes historiques
156 timestamps
5 timeframes
6 devises
```

---

### Film de zone

```text
pf_zone_evolution_reader.py
run_zone_evolution_report.py
```

Validé :

```text
Events: 1368
Sequences: 70
```

---

### Fractal stack

```text
pf_fractal_zone_stack.py
run_fractal_zone_stack_report.py
```

Validé :

```text
Fractal stacks: 16
```

---

### Session story

```text
pf_session_zone_reader.py
run_session_zone_report.py
```

Validé :

```text
Session stories: 16
```

---

### Zone brief

```text
pf_powerflow_zone_brief.py
run_powerflow_zone_brief.py
```

Version validée :

```text
V0.1.2 Temporal Split
```

Paramètres recommandés :

```text
recent-minutes = 180
max-gap-minutes = 90
```

---

### Battlefield map

```text
pf_battlefield_map.py
run_battlefield_map.py
```

Version validée :

```text
V0.1.2 Bipolar Currency Fields
```

Paramètres recommandés :

```text
cluster-gap-minutes = 60
cluster-mode = side
```

---

### Cockpit field

```text
pf_cockpit_field.py
run_cockpit_field.py
```

Validé.

---

## 3. Commande Cockpit principale

Commande de référence :

```powershell
python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt
```

Utilité :

```text
sortie finale courte pour Cockpit /  console
```

---

## 4. Commandes secondaires utiles

### Rebuild historique zone diagnostics

```powershell
python run_zone_context_logger_history.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --limit 50 --replace --summary
```

---

### Rapport film de zone

```powershell
python run_zone_evolution_report.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --top 30 --out zone_evolution_report.txt
```

---

### Rapport fractal

```powershell
python run_fractal_zone_stack_report.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --top 30 --out fractal_zone_stack_report.txt
```

---

### Rapport session

```powershell
python run_session_zone_report.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --top 30 --out session_zone_report.txt
```

---

### Brief zones récent

```powershell
python run_powerflow_zone_brief.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --top 12 --out powerflow_zone_brief_recent.txt
```

---

### Battlefield map récent

```powershell
python run_battlefield_map.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --top 10 --out battlefield_map_recent.txt
```

---

## 5. Dernière lecture validée

Champ :

```text
LATE_US
TACTICAL_RELEASE_BATTLEFIELD
```

Dominant :

```text
CAD HIGH release M1/M5
GBP HIGH release M1/M5
```

Préparation haute :

```text
EUR HIGH M1/M5
CHF HIGH M1/M5
AUD HIGH M1/M5
JPY HIGH M1/M5
```

Opposition / contexte :

```text
EUR LOW M15/M30
GBP LOW M15/M30/H1
CHF LOW M15
CAD LOW M30/H1
JPY LOW M1
```

Bipolaire principal :

```text
EUR : MICRO_VS_HTF_ROTATION_CONTEST
HIGH M1/M5 vs LOW M15/M30
```

Bipolaires secondaires :

```text
GBP : HIGH_RELEASE_VS_LOW_HTF_PREP
CAD : HIGH_RELEASE_VS_LOW_HTF_PREP
CHF : BIPOLAR_CURRENCY_FIELD
JPY : BIPOLAR_CURRENCY_FIELD
```

Phrase :

```text
Late US : champ tactique haut actif.
CAD/GBP libèrent haut en M1/M5.
EUR est bipolaire : micro haut contre scénario bas M15/M30.
GBP/CAD sont aussi en release haute contre préparation basse.
Fenêtre contestée ouverte.
```

---

## 6. Réglages retenus

### Pour Cockpit live

```text
recent-minutes = 180
max-gap-minutes = 90
cluster-gap-minutes = 60
cluster-mode = side
max-lines = 6
```

### Pour analyse historique

```text
recent-minutes = 0
max-gap-minutes = 90
cluster-gap-minutes = 60
cluster-mode = side
```

### Pour analyse plus nerveuse

```text
max-gap-minutes = 45
```

Mais pas recommandé pour le Cockpit principal car cela fragmente davantage.

---

## 7. Points à ne pas oublier

### M1 est spécial

M1 = microfilm projeté, pas simple timeframe classique.

```text
refresh DB ≈ 6–10 secondes
M1 = naissance / microstructure
```

---

### H4/D1 pas mûrs

État actuel :

```text
H4 = 8 lignes
D1 = 1 ligne
```

Ne pas encore construire la gravité LONG sérieusement.

---

### La chaîne ne donne pas des ordres

Elle nomme :

```text
préparation
release
champ contesté
bipolaire
rotation interne
fenêtre temporelle
```

---

## 8. Prochaine suite logique

### Priorité 1 — ajouter `--watch`

Sur :

```text
run_cockpit_field.py
```

But :

```text
rafraîchir automatiquement cockpit_field.txt
```

Proposition :

```powershell
python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt --watch --interval-seconds 30
```

---

### Priorité 2 — `LOCAL_RELEASE_FIELD`

Patch mineur à prévoir :

```text
si une seule TF contient LEAKING ou RUPTURE
→ LOCAL_RELEASE_FIELD
```

---

### Priorité 3 — intégration affichage 

Lire :

```text
cockpit_field.txt
```

dans une console simple ou interface Cockpit.

---

### Priorité 4 — labellisation plus organique

Possibles noms futurs :

```text
ROTATION_GATE
BATTLEFIELD_OPEN_WINDOW
MICRO_RELEASE_OVER_HTF_PREP
HTF_MEMORY_UNDER_MICRO_RELEASE
```

---

### Priorité 5 — multi-symbol plus tard

Ne pas précipiter.

D’abord stabiliser :

```text
GBPUSD
M1/M5/M15/M30/H1
Cockpit field
watch mode
```

Puis seulement :

```text
multi-symbol
```

---

## 9. État émotionnel/projet

Cette session a consolidé une brique vitale.

Avant :

```text
pf_zone_dynamics = module de zone
```

Maintenant :

```text
pf_zone_dynamics = racine d’une chaîne Cockpit complète
```

Le projet dispose maintenant d’une colonne vertébrale claire :

```text
Zone → Film → Fractal → Session → Battlefield → Cockpit Field
```

---

## 10. Reprise conseillée

Quand on reprend, commencer par :

```powershell
python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt
```

Puis demander :

```text
On ajoute --watch ?
```

Suite directe recommandée :

```text
patch run_cockpit_field.py avec --watch
```
