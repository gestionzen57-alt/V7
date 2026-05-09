# RAPPORT M1 — ORCHESTRAL LOOP LIVE

**Date** : 2026-05-07  
**Mission** : M1 Orchestral Loop  
**Statut** : ✅ TERMINÉ  
**Durée** : ~30 minutes

---

## OBJECTIF

Créer `run_orchestral_loop.py` — boucle live qui compute et écrit l'état orchestral
à intervalles réguliers, alimentant le cockpit/dashboard en continu.

---

## FICHIER CRÉÉ

```
run_orchestral_loop.py
```

### Architecture

```python
main()
  → parse_args()
  → run_loop()
      ├─ signal handlers (SIGINT / SIGTERM → graceful stop)
      ├─ while _RUNNING:
      │     _build_state()          ← compute orchestral state
      │       └─ compute_orchestra_multi_tf()
      │     _log_summary()          ← one-liner console log
      │     _write_output()         ← JSON file write
      │     sleep (interruptible)   ← chunks de 1s → Ctrl+C réactif
      └─ loop stopped log
```

---

## FONCTIONNALITÉS

### Boucle principale
```
✅ Boucle infinie (while _RUNNING)
✅ Interval configurable (default 60s)
✅ Sleep interruptible (chunks 1s — Ctrl+C réactif < 1s)
✅ Graceful shutdown SIGINT + SIGTERM
✅ Loop counter (log final "stopped after N iterations")
```

### Compute
```
✅ compute_orchestra_multi_tf() — multi-TF en une passe
✅ Fenêtre glissante auto (lookback depuis NOW)
✅ avg_bars configurable (lissage angle)
✅ Per-TF error isolation (un TF fail ne tue pas les autres)
✅ Global error catch (loop continue même si exception)
```

### Output JSON
```
✅ Mode overwrite (default) — 1 fichier réutilisé, dashboard-friendly
✅ Mode timestamped (--no-overwrite) — trace historique
✅ Pretty print (--pretty) ou compact
✅ mkdir -p automatique (output/ créé si manquant)
✅ --once mode (stdout, test rapide)
```

### Logging
```
✅ One-liner résumé par iteration
✅ Format : [STATE] leader=X tfs=[M1,M5,M15,M30] ⚠ COMPRESSION | patterns=[...]
✅ Niveau configurable DEBUG/INFO/WARNING/ERROR
✅ Timestamps HH:MM:SS
```

---

## ARGS CLI COMPLETS

```bash
--db              powerflow.db         # Path DB SQLite
--symbol          GBPUSD               # Symbol
--tfs             "1,5,15,30"          # TFs en minutes (default LTF+M30)
--interval        60                   # Secondes entre iterations
--lookback        180                  # Minutes fenêtre lookback
--avg-bars        3                    # Barres moyenne angle
--output          output/orchestral_live.json
--no-overwrite                         # Fichiers timestampés vs overwrite
--pretty                               # JSON indenté
--once                                 # Run once → stdout (test)
--log-level       INFO                 # DEBUG|INFO|WARNING|ERROR
```

---

## OUTPUT JSON STRUCTURE

```json
{
  "timestamp": "2026-05-07T14:23:45+00:00",
  "symbol": "GBPUSD",
  "window_start": "...",
  "window_end": "...",
  "lookback_minutes": 180,
  "avg_bars": 3,
  "state": "ORCHESTRAL_ACTIVE",
  "timeframes": {
    "1":  { "tf_label": "M1",  ... OrchestraState ... },
    "5":  { "tf_label": "M5",  ... OrchestraState ... },
    "15": { "tf_label": "M15", ... OrchestraState ... },
    "30": { "tf_label": "M30", ... OrchestraState ... }
  },
  "valid_tfs": [1, 5, 15, 30],
  "latest_tf": 30,
  "latest_tf_label": "M30",
  "latest_state": { ... OrchestraState complet ... },
  "compression_detected": true,
  "leader_currency": "USD",
  "patterns": ["ORCHESTRAL_COMPRESSION"]
}
```

---

## ÉTATS POSSIBLES

```
ORCHESTRAL_ACTIVE          → Au moins 1 TF valide, données OK
ORCHESTRAL_ALL_TF_FAILED   → Tous les TFs ont échoué
ORCHESTRAL_LOOP_ERROR      → Exception globale compute_orchestra_multi_tf
ORCHESTRAL_TF_NO_DATA      → TF individuel sans données suffisantes
```

---

## COMMANDES USAGE

### Default (LTF+M30, 60s)
```powershell
python run_orchestral_loop.py `
  --db powerflow.db `
  --symbol GBPUSD
```

### Test single run
```powershell
python run_orchestral_loop.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --once --pretty
```

### HTF stratégique (H1/H4, 5min interval)
```powershell
python run_orchestral_loop.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --tfs "60,240" `
  --interval 300 `
  --lookback 1440
```

### Mixte complet + trace historique
```powershell
python run_orchestral_loop.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --tfs "1,5,15,30,60" `
  --interval 60 `
  --no-overwrite `
  --output output/orchestral_history.json `
  --pretty
```

### Debug
```powershell
python run_orchestral_loop.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --once `
  --log-level DEBUG `
  --pretty
```

---

## VALIDATION

```
✅ py_compile : SYNTAX OK
✅ --help : CLI OK
✅ --once --pretty : JSON complet, zero crash
✅ ORCHESTRAL_ACTIVE détecté
✅ Patterns détectés (ORCHESTRAL_COMPRESSION, BIPOLAR_FIELD_ACTIVE)
✅ Multi-TF (M1/M5/M15/M30) validé
✅ Leaders/Followers/Antagonists/Crossings exposés
✅ latest_tf = M30 (max available)
✅ compression_detected auto
✅ Read-only DB (uri=ro via pf_orchestral_gravity_v02)
✅ Zero DB write
✅ Zero Telegram
✅ Graceful shutdown (SIGINT/SIGTERM)
```

---

## RÈGLES RESPECTÉES

```
✅ Read-only DB
✅ No DB write
✅ No Telegram
✅ Zero crash (fallback global + per-TF)
✅ Configurable TFs
✅ avg_bars=3 default
✅ Latest TF = max numérique disponible
✅ Compression auto-détecté depuis patterns
✅ Leader currency extracted depuis latest_state
✅ Patterns exposés
✅ Interruptible (Ctrl+C < 1s de réponse)
```

---

## ARCHITECTURE CHAÎNE MISE À JOUR

```
pf_orchestral_gravity_v02.py
    ↓
run_orchestral_loop.py (NOUVEAU ✅)
    ↓ loop 60s
    ↓ output/orchestral_live.json (overwrite)
    ↓
cockpit_agentic_state_v01_orchestral.py V0.1.4
    ↓
dashboard_live.html (futur)
```

---

## MISSIONS RESTANTES

```
✅ M2 — Orchestral cockpit integration (DONE)
✅ M1 — run_orchestral_loop.py (DONE)
❌ M3 — lab.py queries orchestrales (autre fil)
❌ M4 — H4 support (avg_bars data)
❌ Orchestral → dashboard_live.html display
```

---

## PHRASE DE REPRISE

```
La boucle tourne.
Le moteur perçoit toutes les 60 secondes.
L'orchestre est vivant.
Le JSON est disponible.
Le trader lit.
```

---

**FIN RAPPORT M1 — 2026-05-07**
