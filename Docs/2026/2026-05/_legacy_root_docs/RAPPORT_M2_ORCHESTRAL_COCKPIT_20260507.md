# RAPPORT M2 — INTÉGRATION ORCHESTRAL → COCKPIT

**Date** : 2026-05-07  
**Mission** : M2 Orchestral Integration Cockpit  
**Statut** : ✅ TERMINÉ  
**Durée** : ~20 minutes

---

## OBJECTIF

Intégrer bloc `orchestral_gravity` dans `cockpit_agentic_state_v01.py` pour exposition dashboard.

---

## FICHIER CRÉÉ

```
cockpit_agentic_state_v01_orchestral.py  (V0.1.4)
```

### Changements vs V0.1.3

**Import ajouté** :
```python
from pf_orchestral_gravity_v02 import compute_orchestra_state
```

**Fonction helper créée** :
```python
def _build_orchestral_gravity(
    db_path, symbol, start, end, timeframes, avg_bars=3
) -> Dict[str, Any]
```

**Bloc injecté dans state** :
```python
"orchestral_gravity": {
    "state": "ORCHESTRAL_ACTIVE",
    "timeframes": {...},
    "latest_tf": 15,
    "latest_state": {...},
    "compression_detected": bool,
    "leader_currency": str,
    "patterns": [str]
}
```

**Dashboard card ajoutée** :
```python
{
    "title": "ORCHESTRAL GRAVITY",
    "status": orchestral_gravity.get("state"),
    "line": "Leader: USD | Compression: True | Patterns: 2"
}
```

**Arg CLI ajouté** :
```
--orchestral-tfs "1,5,15,30"     # Default LTF + 30
--orchestral-avg-bars 3          # Moyenne angle sur N barres
```

---

## CONFIGURATION RETENUE

### Default (LTF tactique + 30min)
```bash
--orchestral-tfs "1,5,15,30"
```

### Option HTF stratégique
```bash
--orchestral-tfs "60,240,1440,10080"  # H1, H4, D, W
```

### Option mixte complète
```bash
--orchestral-tfs "1,5,15,30,60,240"  # LTF + HTF intraday
```

---

## STRUCTURE OUTPUT JSON

```json
{
  "version": "0.1.4",
  "orchestral_gravity": {
    "state": "ORCHESTRAL_ACTIVE",
    "timeframes": {
      "1": {
        "leader": {"currency": "USD", "angle": 5.6, ...},
        "followers": [...],
        "antagonists": [...],
        "coalitions": {...},
        "crossings": [...],
        "patterns": ["ORCHESTRAL_COMPRESSION"]
      },
      "5": {...},
      "15": {...},
      "30": {...}
    },
    "latest_tf": 30,
    "latest_state": {...},
    "compression_detected": true,
    "leader_currency": "USD",
    "patterns": ["ORCHESTRAL_COMPRESSION", "JPY_GRAVITY_PULLING_GBP_EUR"],
    "notes": []
  }
}
```

---

## FALLBACK ERRORS

### Si aucun TF fourni
```json
{
  "state": "ORCHESTRAL_NO_TIMEFRAMES",
  "timeframes": {},
  "latest_state": null,
  "compression_detected": false,
  "notes": ["No timeframes provided"]
}
```

### Si erreur compute
```json
{
  "state": "ORCHESTRAL_BRIDGE_ERROR",
  "timeframes": {},
  "latest_state": null,
  "compression_detected": false,
  "notes": ["orchestral_bridge_error: Exception..."]
}
```

### Si TF individuel fail
```json
{
  "timeframes": {
    "1": {...},
    "5": {
      "state": "ORCHESTRAL_TF_ERROR",
      "error": "DB read timeout"
    },
    "15": {...}
  }
}
```

---

## COMMANDES TEST

### Test LTF tactique (default)
```powershell
python cockpit_agentic_state_v01_orchestral.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --start "2026-05-07T07:00:00+00:00" `
  --end "2026-05-07T12:00:00+00:00" `
  --out output/cockpit_orchestral_ltf.json `
  --pretty
```

### Test HTF stratégique
```powershell
python cockpit_agentic_state_v01_orchestral.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --start "2026-05-06T00:00:00+00:00" `
  --end "2026-05-07T23:59:59+00:00" `
  --orchestral-tfs "60,240,1440" `
  --out output/cockpit_orchestral_htf.json `
  --pretty
```

### Test mixte complet
```powershell
python cockpit_agentic_state_v01_orchestral.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --start "2026-05-07T05:00:00+00:00" `
  --end "2026-05-07T21:00:00+00:00" `
  --orchestral-tfs "1,5,15,30,60" `
  --orchestral-avg-bars 5 `
  --out output/cockpit_orchestral_full.json `
  --pretty
```

---

## VALIDATION CHECKLIST

- [x] Import `pf_orchestral_gravity_v02`
- [x] Fonction `_build_orchestral_gravity()` créée
- [x] Bloc `orchestral_gravity` injecté dans state
- [x] Dashboard card `ORCHESTRAL GRAVITY` ajoutée
- [x] Arg `--orchestral-tfs` configurable
- [x] Arg `--orchestral-avg-bars` configurable
- [x] Fallback errors OK
- [x] Default LTF + 30
- [x] Option HTF stratégique documentée
- [x] Version bumped 0.1.3 → 0.1.4
- [x] Read-only (no DB write)
- [x] No Telegram
- [x] Zero crash

---

## RÈGLES RESPECTÉES

```
✅ Read-only DB
✅ No DB write
✅ No Telegram
✅ Zero crash (fallback partout)
✅ Configurable TFs
✅ avg_bars=3 default
✅ Latest TF = highest available
✅ Compression detected auto
✅ Leader currency extracted
✅ Patterns exposed
```

---

## ARCHITECTURE FINALE COCKPIT

```
cockpit_agentic_state_v01.py V0.1.4
├─ db_vision
├─ flow_events
├─ scene
├─ fractal
├─ extended
├─ behavioral_alerts (bridge)
├─ relational_gravity (bridge)
├─ orchestral_gravity (bridge) ← NOUVEAU ✅
└─ dashboard_cards (6 cards)
```

---

## INTÉGRATION DASHBOARD

Le bloc `orchestral_gravity` est maintenant disponible dans `cockpit_agentic_state_v01.json`.

Dashboard peut afficher :
- Leader actuel
- Followers/Antagonists
- Coalitions UP/DOWN
- Croisements imminents
- Patterns détectés (ORCHESTRAL_COMPRESSION, JPY_GRAVITY_PULLING, etc.)
- Compression warning

---

## PROCHAINES ÉTAPES

### Immédiat (P0)
```
✅ M2 Orchestral Cockpit terminé
```

### Next missions
```
🔵 M1 — run_orchestral_loop.py (boucle live)
🔵 M3 — lab.py queries orchestrales
🔵 M4 — H4 support (avg_bars data)
```

---

## PHRASE DE REPRISE

```
Orchestral Gravity est maintenant visible dans le cockpit.
Le trader voit qui mène, qui suit, qui résiste.
Les compressions pré-mouvement sont détectées.
Les patterns nommés apparaissent.

La machine perçoit l'orchestre.
Le trader décide.
```

---

**FIN RAPPORT M2**
