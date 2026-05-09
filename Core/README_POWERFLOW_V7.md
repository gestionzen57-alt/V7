# README — PowerFlow V7 — Nouvelles Briques

**Date : 2026-05-09 | Git : c579afa**

---

## Qu'est-ce qui a changé entre V6 et V7 ?

V6 percevait les événements.
V7 perçoit **dans quel contexte** ces événements se produisent.

---

## B1 — Regime Engine (`pf_regime_engine.py`)

### Quoi
Détecte le régime HTF actuel : COMPRESSION / TENDANCE / RANGE.

### Pourquoi c'était l'angle mort critique
En V6, un FIRST_DETACHMENT en régime COMPRESSION et un FIRST_DETACHMENT en régime TENDANCE déclenchaient **la même alerte**. Ce sont deux réalités opposées.

### Comment lire la sortie
```json
{
  "regime": "COMPRESSION",
  "confidence": 0.82,
  "htf_context_stack": {
    "W": "RANGE",
    "D": "COMPRESSION",
    "H4": "COMPRESSION",
    "H1": "TRANSITION"
  }
}
```
- `COMPRESSION` : marché serré, explosion imminente possible
- `TENDANCE` : flux directionnel établi, continuer dans le sens
- `RANGE` : pas de flux, éviter ou scalper court

### Commande
```powershell
python run_regime_engine_once.py --db powerflow.db --pretty
```

### Règle
Le regime_context enrichit chaque alerte behavioral :
- FIRST_DETACHMENT + COMPRESSION → HOT
- FIRST_DETACHMENT + RANGE → WATCH
- FIRST_DETACHMENT + TENDANCE → INFO (déjà en cours)

---

## B2 — Cascade Engine (`pf_cascade_engine.py`)

### Quoi
Compte les événements HOT dans une fenêtre glissante de 5 min.

### Pourquoi
V6 alertait sur chaque événement isolément. Il ne détectait pas si une séquence s'amplifiait : FIRST_DETACHMENT → M5_RELAY → RELEASE_ATTEMPT en 5 min est bien plus significatif qu'un détachement isolé.

### Comment lire
```json
{
  "cascade_state": "SEQUENCE_VELOCITY_HIGH",
  "events_count": 4,
  "cascade_building": true
}
```
- `SEQUENCE_VELOCITY_HIGH` : 3+ HOT en 5 min → cascade en formation
- `SEQUENCE_VELOCITY_MEDIUM` : 2 HOT → attention
- `SEQUENCE_VELOCITY_LOW` : 0-1 HOT → normal

### Commande
```powershell
python run_cascade_engine_once.py
```

### Note
Le résultat sera `LOW` quand le marché est fermé (weekend). Normal.

---

## B3 — Kalman Kinematics (`pf_force_kinematics.py`)

### Quoi
Remplace les fenêtres fixes (N barres hardcodées) par un filtre de Kalman adaptatif.

### Pourquoi
Avant : en marché calme → le bruit était perçu comme signal. En marché fort → le filtre réagissait trop lentement.

Après : Kalman adapte automatiquement. Moins de faux positifs sur les PLIURES. Speed_state plus réactif.

### Nouveaux champs
```json
{
  "angle_kalman": 0.43,
  "speed_kalman": 0.021,
  "noise_ratio": 0.12
}
```
- `noise_ratio` proche de 0 = signal propre
- `noise_ratio` > 0.3 = beaucoup de bruit → alerte à qualifier

### Paramètres
- Q=0.01 (bruit processus) — adapte vite aux changements réels
- R=0.10 (bruit mesure) — filtre le bruit des snapshots bruts

---

## B4 — Temporal Density (`pf_temporal_density.py`)

### Quoi
Détecte si les oscillations de force d'une devise se **compriment dans le temps**.

### Pourquoi c'est le pré-signal du pré-signal
V6 mesurait la FORCE et la CINÉMATIQUE. Il ne mesurait pas les CYCLES.
Un marché peut avoir une force stable mais des oscillations qui se compriment rapidement = signal de rupture imminente avant que M1 le montre.

### Comment lire
```json
{
  "currency": "GBP",
  "timeframe": 5,
  "compression_ratio": 0.93,
  "cycle_state": "CYCLE_COMPRESSING",
  "dominant_period_bars": 1
}
```
- `CYCLE_COMPRESSING` + ratio > 0.65 → rupture possible imminente
- `CYCLE_EXPANDING` → respiration / pullback en cours
- `CYCLE_STABLE` → range / consolidation
- `CYCLE_NOISY` → pas de cycle dominant

### Alerte système
Si 3+ devises simultanément en CYCLE_COMPRESSING → `compression_alert: true`

### Commande
```powershell
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
```

### Note importante
Résultat weekend : dominant_period=1 partout = marché fermé, séries statiques. **Normal.** Tester lundi Asian open.

---

## B5 — Spearman Gravity (`pf_spearman_gravity.py`)

### Quoi
Corrélation de rang Spearman rolling pour toutes les paires de devises.

### Pourquoi
Relational Gravity V6 utilisait des heuristiques (distances, scores, seuils fixes). Le problème P1.2 (USD leader ET antagoniste) venait directement de ça.

B5 remplace ça par une mesure statistique réelle : **est-ce que GBP et USD co-bougent vraiment ?**

### Comment lire
```json
{
  "pair": "GBP_CAD",
  "spearman_rho": -0.88,
  "direction": "DIVERGENT",
  "tail_signal": "DIVERGENT_EXTREME"
}
```
- `rho > 0.70` → SYNCHRO (bougent ensemble)
- `rho < -0.50` → DIVERGENT (bougent en sens opposé)
- `CODEPENDANT_EXTREME` → co-dépendance extrême aux extrema
- `DIVERGENT_EXTREME` → opposition structurelle forte

### Résolution MIXED probabiliste
Au lieu de l'étiquette vague MIXED, B5 donne un `avg_rho` mesurable :
```json
{"pair": "GBP_USD", "avg_rho": 0.343, "note": "MIXED_PROBABILISTE"}
```
→ rho=0.34 = relation faible mais légèrement positive. Pas aléatoire.

### Commande
```powershell
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
```

---

## Chaîne complète V7

```
force_snapshots (DB)
    ↓
B1  pf_regime_engine.py         → HTF_CONTEXT_STACK
    ↓
B3  pf_force_kinematics.py      → Kalman angle/speed
    ↓
    pf_tension_signature.py
    ↓
P1  pf_currency_energy_probe.py → elastic_tension_score
    ↓
    pf_temporal_node_state.py
    ↓
B4  pf_temporal_density.py      → CYCLE_COMPRESSING
    ↓
B5  pf_spearman_gravity.py      → Spearman pairs
    ↓
P4  run_confluence_alert.py     → EIE → queue
    ↓
B2  pf_cascade_engine.py        → SEQUENCE_VELOCITY
    ↓
    pf_behavioral_alert_mapper.py (V7 regime_context enrichi)
    ↓
    cockpit_agentic_state_v01.py
    ↓
    dashboard_live.html
```

---

## Nouvelles alertes V7

| Alerte | Source | Niveau | Signification |
|--------|--------|--------|---------------|
| REGIME_COMPRESSION_ACTIVE | B1 | HOT | HTF en compression |
| REGIME_TENDANCE_CONFIRMED | B1 | INFO | Flux directionnel établi |
| CASCADE_BUILDING_ALERT | B2 | HOT | 3+ HOT en 5 min |
| CYCLE_COMPRESSING_ALERT | B4 | WATCH | Oscillations se compriment |
| CODEPENDANT_EXTREME | B5 | WATCH | Co-dépendance paire extrême |
| ELASTIC_COMPONENT_ACTIVE | P1 | WATCH | Tension élastique dans energy |
| EIE_LEADER_CONFIRMED | P4 | HOT | EIE + leader RG confirmé |

---

## Règles mémoire

- **CLAUDE.md** = mis à jour manuellement en fin de session (pas auto)
- **Lexique** = intégré dans CLAUDE.md à chaque nouveau terme validé
- **Checkpoint** = généré en fin de mission, à coller dans Git
- **git_sync.ps1** = `.\git_sync.ps1 "Message"` → commit + push auto

---

## Limitations connues

- B4 weekend : dominant_period=1 = séries statiques. Normal.
- B2 weekend : events_count=0 = queue vide. Normal.
- B1 TF240/1440 : peu de données (39/11 rows). Heuristique moins fiable.
- CLAUDE.md V7 : pas auto-alimenté. Mise à jour manuelle après chaque mission.

---

## Prochaines missions (queue)

```
Lab Engine V2    : 6 queries trading orientées (B4+B5 nourriront)
Task Scheduler   : automatiser cycle complet toutes les 5 min
Dashboard V7     : cartes B1 regime + B4 compression + B5 pairs
B1 HMM upgrade  : quand TF1440 > 50 rows (dans ~3 semaines)
```
