# PATCH LEXIQUE M2 — COCKPIT ORCHESTRAL INTEGRATION

**Date** : 2026-05-07  
**Mission** : M2 Orchestral Cockpit  
**Statut** : À intégrer dans LEXIQUE_GRAMMAIRE PowerFlow V6

---

## Nouveaux termes Cockpit Orchestral

### ORCHESTRAL_GRAVITY (cockpit block)
Bloc JSON complet exposant orchestral gravity dans cockpit state.

```json
{
  "state": "ORCHESTRAL_ACTIVE",
  "timeframes": {...},
  "latest_tf": 30,
  "latest_state": {...},
  "compression_detected": bool,
  "leader_currency": str,
  "patterns": [str]
}
```

### ORCHESTRAL_ACTIVE
État orchestral opérationnel avec données valides pour au moins 1 TF.

### ORCHESTRAL_NO_TIMEFRAMES
État orchestral où aucun TF n'a été fourni pour analyse.

### ORCHESTRAL_BRIDGE_ERROR
Erreur globale du bridge orchestral (exception catch-all).

### ORCHESTRAL_TF_ERROR
Erreur compute orchestral pour un TF individuel (les autres TFs peuvent être OK).

### ORCHESTRAL_ALL_TF_FAILED
État où tous les TFs ont échoué à compute orchestral state.

### LATEST_TF (orchestral)
TF le plus élevé disponible dans l'analyse orchestrale (ex: si 1,5,15,60 → 60).

### LATEST_STATE (orchestral)
OrchestraState du TF le plus élevé disponible.

### COMPRESSION_DETECTED (orchestral)
Boolean auto-détecté : `true` si au moins 1 TF contient pattern `ORCHESTRAL_COMPRESSION`.

### LEADER_CURRENCY (orchestral)
Devise leader du latest_state (None si pas de leader).

### PATTERNS (orchestral)
Liste des patterns nommés détectés dans latest_state.

### ORCHESTRAL_AVG_BARS
Nombre de barres moyennées pour calcul angle orchestral (default: 3).

```
avg_bars=3  → moyenne angle sur 3 dernières barres
avg_bars=5  → moyenne angle sur 5 dernières barres
```

### ORCHESTRAL_TIMEFRAMES (config)
Liste TFs configurés pour analyse orchestrale.

```
Default : LTF + 30  (ex: [1, 5, 15, 30])
HTF     : [60, 240, 1440, 10080]  (H1, H4, D, W)
Mixte   : [1, 5, 15, 30, 60, 240]
```

---

## Nouveaux args CLI cockpit

### --orchestral-tfs
```bash
--orchestral-tfs "1,5,15,30"      # Default implicite si omis
--orchestral-tfs "60,240,1440"    # HTF stratégique
--orchestral-tfs "1,5,15,30,60"   # Mixte LTF + H1
```

### --orchestral-avg-bars
```bash
--orchestral-avg-bars 3   # Default
--orchestral-avg-bars 5   # Moyenne plus lissée
--orchestral-avg-bars 1   # Pas de moyenne (angle instant)
```

---

## Dashboard card orchestral

```python
{
    "title": "ORCHESTRAL GRAVITY",
    "status": "ORCHESTRAL_ACTIVE",
    "line": "Leader: USD | Compression: True | Patterns: 2"
}
```

---

## Structure JSON complète cockpit V0.1.4

```json
{
  "version": "0.1.4",
  "orchestral_gravity": {
    "state": "ORCHESTRAL_ACTIVE",
    "timeframes": {
      "1": OrchestraState,
      "5": OrchestraState,
      "15": OrchestraState,
      "30": OrchestraState
    },
    "latest_tf": 30,
    "latest_state": OrchestraState,
    "compression_detected": true,
    "leader_currency": "USD",
    "patterns": ["ORCHESTRAL_COMPRESSION"],
    "notes": []
  }
}
```

---

## Règles non-confusion

```
ORCHESTRAL_GRAVITY (cockpit block) ≠ ORCHESTRAL_GRAVITY (concept général)
LATEST_TF = TF numériquement le plus haut disponible, pas le plus récent temporellement
COMPRESSION_DETECTED = auto from patterns, pas décision trader
LEADER_CURRENCY = from latest_state only, pas synthèse cross-TF
```

---

## Chaîne d'intégration mise à jour

```
pf_orchestral_gravity_v02.py
    ↓
run_orchestral_analysis_once.py (runner)
    ↓
cockpit_agentic_state_v01.py V0.1.4
    ↓ _build_orchestral_gravity()
    ↓
cockpit_agentic_state_v01.json
    ↓
dashboard_live.html (futur)
```

---

**FIN PATCH LEXIQUE M2**
