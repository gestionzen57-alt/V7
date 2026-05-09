# PATCH LEXIQUE M1 — ORCHESTRAL LOOP LIVE

**Date** : 2026-05-07  
**Mission** : M1 Orchestral Loop  
**Statut** : À intégrer dans LEXIQUE_GRAMMAIRE PowerFlow V6 + CLAUDE.md V3

---

## Nouveaux termes Loop

### ORCHESTRAL_LOOP
Boucle live qui compute et écrit l'état orchestral à intervalles réguliers.

```
run_orchestral_loop.py
Interval default : 60s
Output : output/orchestral_live.json
Mode : overwrite (dashboard) ou timestampé (historique)
```

### ORCHESTRAL_LOOP_ERROR
Exception globale capturée dans la boucle.

```
Cause : exception non catchée dans compute_orchestra_multi_tf()
Comportement : state=ORCHESTRAL_LOOP_ERROR exposé dans JSON
               Boucle continue après sleep
```

### ORCHESTRAL_TF_NO_DATA
TF individuel sans données suffisantes pour compute.

```
Cause : pas assez de barres dans la fenêtre lookback
Comportement : ce TF sort ORCHESTRAL_TF_NO_DATA
               Les autres TFs sont non affectés
```

### ORCHESTRAL_ALL_TF_FAILED
Tous les TFs ont échoué à produire un état valide.

```
Cause : lookback trop court, DB vide, ou mauvais symbol
Comportement : state=ORCHESTRAL_ALL_TF_FAILED
               valid_tfs = []
               latest_tf = null
```

### ORCHESTRAL_ACTIVE
État normal de la boucle — au moins 1 TF produit un état valide.

```
Condition : len(valid_tfs) >= 1
```

### OVERWRITE_MODE
Mode default de la loop : 1 fichier JSON réutilisé à chaque iteration.

```
Avantage : dashboard peut juste relire le même fichier
Usage : --output output/orchestral_live.json  (sans --no-overwrite)
```

### TIMESTAMPED_MODE
Mode trace : fichier JSON horodaté par iteration.

```
Format : orchestral_live_YYYYMMDD_HHMMSS.json
Usage : --no-overwrite
Avantage : historique complet des états
```

### LOOKBACK_WINDOW
Fenêtre glissante depuis NOW utilisée pour compute orchestral state.

```
Default : 180 minutes
Calcul  : start = now - timedelta(minutes=lookback)
          end   = now
Usage   : --lookback 180
```

### ONCE_MODE
Mode single run : compute 1 fois, print JSON stdout, exit.

```
Usage : --once --pretty
But   : test rapide, validation, debug
Sortie : stdout (pas de fichier)
```

### GRACEFUL_SHUTDOWN
Arrêt propre de la boucle sur SIGINT (Ctrl+C) ou SIGTERM.

```
Mécanisme : _RUNNING = False → exit après iteration courante
Réactivité : sleep interruptible en chunks 1s → réponse < 1s
```

### SLEEP_INTERRUPTIBLE
Technique de sleep fragmenté en chunks de 1s pour réponse rapide au shutdown.

```python
# Vs time.sleep(60) qui bloquerait 60s après Ctrl+C
for _ in range(interval):
    if not _RUNNING: break
    time.sleep(1.0)
```

---

## Champs JSON loop

### valid_tfs
Liste des TFs qui ont produit un OrchestraState valide dans cette iteration.

```json
"valid_tfs": [1, 5, 15, 30]
```

### latest_tf
TF numériquement le plus élevé dans valid_tfs.

```
Si valid_tfs = [1, 5, 15, 30] → latest_tf = 30
Si valid_tfs = [60, 240]      → latest_tf = 240
```

### latest_tf_label
Label human-readable du latest_tf.

```json
"latest_tf_label": "M30"
```

### window_start / window_end
Bornes ISO8601 de la fenêtre lookback utilisée pour cette iteration.

```json
"window_start": "2026-05-07T09:59:37+00:00",
"window_end":   "2026-05-07T12:59:37+00:00"
```

---

## Règles non-confusion

```
ORCHESTRAL_LOOP ≠ run_orchestral_analysis_once.py
  analysis_once = run ponctuel avec start/end manuels
  loop          = boucle live avec fenêtre glissante auto

OVERWRITE_MODE ≠ TIMESTAMPED_MODE
  overwrite     = dashboard-friendly (1 fichier)
  timestamped   = trace historique (N fichiers)

ONCE_MODE ≠ run_orchestral_analysis_once.py
  --once       = loop avec 1 iteration, stdout, test rapide
  analysis_once = runner complet inflection+extrema+orchestral
```

---

## Chaîne mise à jour

```
pf_orchestral_gravity_v02.py
    ↓
run_orchestral_loop.py (M1 ✅)     run_orchestral_analysis_once.py
    ↓ live loop 60s                      ↓ ponctuel start/end
    ↓ output/orchestral_live.json        ↓ output/orchestral_today.md
    ↓
cockpit_agentic_state_v01_orchestral.py V0.1.4 (M2 ✅)
    ↓
dashboard_live.html (futur M5)
```

---

**FIN PATCH LEXIQUE M1 — 2026-05-07**
