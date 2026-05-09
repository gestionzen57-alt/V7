# CHECKPOINT — ORCHESTRAL GRAVITY V0.2

**Date :** 2026-05-07  
**Statut :** VALIDÉ SUR DB LIVE  
**Session :** Claude — nouveaux fichiers testés sur powerflow.db (06/05 + 07/05)

---

## 1. Ce qui a été construit

### 3 nouvelles briques pf_*

```
pf_force_inflection.py     V0.1   — détection pliure contresens par devise par TF
pf_force_extrema.py        V0.1   — détection valleys/peaks avec asymétrie entrée/sortie
pf_orchestral_gravity.py   V0.2   — leader/follower/croisements/coalitions + zone_dynamics
```

### 1 runner

```
run_orchestral_analysis_once.py   — combine les 3 briques, output .md ou .json
```

### Dépendances utilisées

```
pf_zone_dynamics.py        (existant dans core — utilisé pour tension_score par devise)
pf_force_kinematics.py     (existant dans core — angles/velocity reference)
```

---

## 2. Architecture des nouvelles briques

```
force_snapshots (DB)
    ↓
pf_force_inflection.py
├─ angle series par devise par TF
├─ détecte pliure contresens (sign flip + delta brutal)
└─ OUTPUT: List[InflectionEvent]

force_snapshots (DB)
    ↓
pf_force_extrema.py
├─ force series par devise par TF
├─ détecte local minima/maxima qualifiés
├─ calcule asymétrie entrée/sortie
└─ OUTPUT: List[ExtremaEvent]

force_snapshots (DB)  +  pf_zone_dynamics.py
    ↓
pf_orchestral_gravity.py
├─ angles moyens par devise (avg_bars derniers segments)
├─ z-scores comportementaux (rolling, lookback=20)
├─ pf_zone_dynamics → ZoneQuality par devise (state, tension_score, z_current)
├─ classification rôles: LEADER / FOLLOWER / ANTAGONIST / LAGGING / NEUTRAL
├─ coalitions UP/DOWN avec cohésion
├─ croisements CROSSING_IMMINENT / CROSSING_ZONE
├─ patterns nommés
└─ OUTPUT: OrchestraState
```

---

## 3. Validation sur DB 06/05 05:00-21:00

### Pliures M15 majeures détectées

```
07:30  CAD  CONTRESENS_PLIURE_DOWN  Δ-74.7°  EXTREME  — crash Acte 1
07:45  CAD  CONTRESENS_PLIURE_UP    Δ+56.6°  EXTREME  — absorption rapide
08:00  GBP  CONTRESENS_PLIURE_UP    Δ+44.1°  BRUTAL   — rebond birth GBP
11:00  GBP  CONTRESENS_PLIURE_DOWN  Δ-32.3°  MODERATE — pivot Acte 1→2
11:00  EUR  CONTRESENS_PLIURE_DOWN  Δ-22.0°  MODERATE — synchro GBP
11:00  JPY  CONTRESENS_PLIURE_UP    Δ+30.2°  MODERATE — JPY change de sens
```

### Valleys/Peaks M15 avec asymétrie

```
07:15  CAD  PEAK    amplitude=23.2  SLOW_ENTRY_FAST_EXIT  — chute explosive après
10:45  JPY  VALLEY  amplitude=10.5  FAST_ENTRY_SLOW_EXIT  — absorption JPY
14:45  EUR  PEAK    amplitude=12.8  SLOW_ENTRY_FAST_EXIT  — rotation après
11:00  EUR  VALLEY  H1  amplitude=10.5  BALANCED
```

### Orchestral Gravity H1 fin de journée

```
LEADER  : USD (+5.6° [EARLY_EXTREME z=+2.11 t=1.9])
NEUTRAL : GBP, EUR, JPY, CAD, CHF, AUD
CROSSING_IMMINENT : USD↔CHF, USD↔AUD, EUR↔JPY
PATTERN : ORCHESTRAL_COMPRESSION
```

---

## 4. Commandes validées

```powershell
# Rapport orchestral complet (Markdown)
python run_orchestral_analysis_once.py `
  --db powerflow.db `
  --start "2026-05-07T05:00:00+00:00" `
  --end "2026-05-07T21:00:00+00:00" `
  --tfs "15,60" --out output/orchestral_today.md

# Rapport JSON pour cockpit
python run_orchestral_analysis_once.py `
  --db powerflow.db `
  --start "2026-05-07T07:00:00+00:00" `
  --end "2026-05-07T12:00:00+00:00" `
  --tfs "5,15,60" --json --out output/orchestral_state.json
```

---

## 5. Ce qui n'est PAS encore fait

```
❌ run_orchestral_loop.py         — boucle live toutes N minutes
❌ intégration cockpit_agentic_state_v01.py — bloc orchestral dans le state
❌ lab.py queries orchestrales    — "gbp_h1_valley AND jpy_h1_leader"
❌ H4 support                     — manque de données pour avg_bars
❌ lag detection précis            — lag_bars actuellement estimé (0 ou 2)
❌ CHECKPOINT dans CLAUDE.md       — à mettre à jour lors de la prochaine session
```

---

## 6. Règles critiques à respecter

```
pf_force_inflection.py     — read-only, pas de DB write
pf_force_extrema.py        — read-only, pas de DB write
pf_orchestral_gravity.py   — read-only, pas de DB write
pf_zone_dynamics           — optionnel (fallback si absent)
capture_bridge.py          — NE PAS TOUCHER
powerflow.db               — lecture seule depuis ces briques
```

---

## 7. Phrase de reprise

```
Les briques orchestrales lisent le flux multi-devise multi-TF.
Elles ne décident pas. Elles nomment.
Pliure → Inflection → Valley/Peak → Leader/Follower → Pattern.
Le trader filtre. Le trader décide.
```
