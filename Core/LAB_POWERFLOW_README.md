# LAB POWERFLOW V6 — README

**Version** : V3 (11 couches)  
**Date** : 2026-05-08  
**Fichiers** : `lab_powerflow.py` + `pf_lab_engine.py`  
**Doctrine** : Read-only. No Telegram. No BUY/SELL. Trader décide.

---

## ARCHITECTURE — 11 COUCHES

```
Couche  1  kinematics       angle / speed / accel / first_detachment / clusters
Couche  2  zones            NEUTRAL → PRE_EXTREME → EARLY_EXTREME → ACCUMULATING → LEAKING → RUPTURE
Couche  3  nodes            fractal nodes (pf_flow_nodes) — TRIPLE_CROSS_CLUSTER, PRE_CROSS_COMPRESSION_NODE...
Couche  4  turning_points   naissances de mouvement (BIRTH / CONFIRMED / WATCH)
Couche  5  orchestra        leader / follower / antagonist / ORCHESTRAL_COMPRESSION
Couche  6  relational        gravity brut SANS filtre P1.2 (legacy)
Couche  7  fractal          cohérence LTF/MTF/HTF (PHASE_SYNC / PHASE_OPPOSITION / FRACTAL_PARTIAL)
Couche  8  relational_gravity  gravity direct multi-TF + cross-tf summary
Couche  9  temporal_density   COMPRESSED / ACTIVE / HOLLOW / DEAD per devise per TF
Couche 10  coalition        blocs devises + battlefield windows (ELASTIC_RESPRING vs HIGH_FOLDING)
Couche 11  tension_signature  ELASTIC_LOADED / DIRECTIONAL_MOVE / DEAD_CURRENCY per devise
```

---

## QUERIES DISPONIBLES

| Query | Couches | Usage |
|-------|---------|-------|
| `kinematics` | 1 | Angles bruts, detachments, clusters |
| `zones` | 2 | États zone + cascade LTF→HTF |
| `nodes` | 3 | Fractal nodes sur 3 horizons |
| `turning_points` | 4 | Naissances de mouvement |
| `orchestra` | 5 | Leader/follower/compression orchestrale |
| `relational` | 6 | Relational gravity legacy |
| `fractal` | 7 | Cohérence fractale HTF vs sub-TFs |
| `relational_gravity` | 8 | Relational gravity direct (bypass P1.2) |
| `temporal_density` | 9 | Densité temporelle per devise |
| `coalition` | 10 | Blocs coalitions + battlefield windows |
| `tension` | 11 | Micro/macro variance par devise |
| `full_v2` | 1-9 | Session complète sans coalitions |
| `full_v3` | 1-11 | Session complète toutes couches ← DÉFAUT |

---

## COMMANDES RAPIDES

### Setup initial — vérifier la DB
```powershell
python lab_powerflow.py --list-tfs --symbol GBPUSD --db powerflow.db
python lab_powerflow.py --probe-db --symbol GBPUSD --db powerflow.db
```

### Fenêtre glissante (NOW - N minutes)
```powershell
python lab_powerflow.py --query full_v3 `
  --db powerflow.db --symbol GBPUSD `
  --horizons "MTF" --once --lookback 300 --pretty
```

### Fenêtre fixe (start/end)
```powershell
python lab_powerflow.py --query full_v3 `
  --db powerflow.db --symbol GBPUSD `
  --tfs "15,30,60" `
  --start "2026-05-07T07:00:00" --end "2026-05-07T20:00:00" `
  --out output/lab_session.json --pretty
```

---

## COUCHE PAR COUCHE — USAGE

### Couche 1 — Kinematics
```powershell
python lab_powerflow.py --query kinematics `
  --db powerflow.db --symbol GBPUSD `
  --tfs "1,5,15,30,60" --once --lookback 180 --pretty
```
**Lit** : angle, speed, accel, first_detachment, same_angle_cluster, tight_gravity_cluster  
**Seuils first_detachment** : M1=55° M5=45° M15=35° M30=28° H1=22°  
**Usage** : détecter qui décroche, vitesse mouvement, clusters devises

---

### Couche 2 — Zones
```powershell
python lab_powerflow.py --query zones `
  --db powerflow.db --symbol GBPUSD `
  --tfs "15,30,60,240" --once --lookback 480 --pretty
```
**Lit** : zone_state per devise per TF + cascade divergence entre TF pairs  
**États** : `NEUTRAL` → `PRE_EXTREME` → `EARLY_EXTREME` → `ACCUMULATING` → `LEAKING` → `RUPTURE`  
**Cascade** : détecte combien de devises divergent entre TF adjacents (ex: M30→H1)  
**Usage** : voir où sont les tensions accumulées, repérer transitions régime

---

### Couche 3 — Nodes
```powershell
python lab_powerflow.py --query nodes `
  --db powerflow.db --symbol GBPUSD `
  --horizons "LTF,MTF,HTF" --once --lookback 480 --pretty

# Fenêtre large pour historique
python lab_powerflow.py --query nodes `
  --db powerflow.db --symbol GBPUSD `
  --horizons "MTF,HTF" `
  --start "2026-05-06T00:00:00" --end "2026-05-07T23:59:59" --pretty
```
**Horizons** : `LTF`=[1,5,15] `MTF`=[15,30,60] `HTF`=[60,240,1440]  
**Patterns** : `TRIPLE_CROSS_CLUSTER`, `PRE_CROSS_COMPRESSION_NODE`, `TRIPLE_NODE_PREPARATION`, `EXTREME_BOUND_NODE`  
**Note** : M15 intentionnellement dans LTF+MTF (pont cohérence fractale)

---

### Couche 4 — Turning Points
```powershell
python lab_powerflow.py --query turning_points `
  --db powerflow.db --symbol GBPUSD `
  --tfs "5,15,30,60" --once --lookback 300 --pretty
```
**Lit** : BIRTH / CONFIRMED / WATCH — croise first_detachment + zone + fractal  
**Usage** : repérer naissances de mouvement qualifiées

---

### Couche 5 — Orchestra
```powershell
python lab_powerflow.py --query orchestra `
  --db powerflow.db --symbol GBPUSD `
  --tfs "5,15,30,60" --avg-bars 3 --once --lookback 180 --pretty
```
**Lit** : leader, followers, antagonists, coalitions, ORCHESTRAL_COMPRESSION  
**`--avg-bars`** : lissage angle sur N barres (défaut 3, augmenter pour HTF)

---

### Couche 7 — Fractal Coherence
```powershell
# H1 comme référence, comparer avec LTF
python lab_powerflow.py --query fractal `
  --db powerflow.db --symbol GBPUSD `
  --main-tf 60 --sub-tfs "1,5,15,30" `
  --start "2026-05-06T00:00:00" --end "2026-05-07T20:00:00" --pretty
```
**Labels** : `PHASE_SYNC`, `PARTIAL_SYNC`, `PHASE_OPPOSITION`, `FRACTAL_LAG`  
**Global** : `FRACTAL_FULL_SYNC` / `FRACTAL_PARTIAL` / `FRACTAL_DIVERGENT`  
**Usage** : voir si LTF confirme ou contredit HTF

---

### Couche 8 — Relational Gravity (direct, bypass P1.2)
```powershell
python lab_powerflow.py --query relational_gravity `
  --db powerflow.db --symbol GBPUSD `
  --tfs "1,5,15,30,60" --relational-bars 30 --once --pretty
```
**États** : `GRAVITY_COMPRESSION_CLUSTER`, `LEADER_PULLING_AWAY`, `POSITIVE_DISTANCE_SYNC`, `DESYNC_TRIGGER`  
**Note** : bypass P1.2 Bridge Guard — expose MIXED sans filtre

---

### Couche 9 — Temporal Density
```powershell
python lab_powerflow.py --query temporal_density `
  --db powerflow.db --symbol GBPUSD `
  --tfs "5,15,30,60" --density-window 20 --once --pretty
```
**États** : `COMPRESSED` / `ACTIVE` / `NEUTRAL` / `HOLLOW` / `DEAD`  
**Usage** : identifier quelle devise est active vs endormie

---

### Couche 10 — Coalition
```powershell
python lab_powerflow.py --query coalition `
  --db powerflow.db --symbol GBPUSD `
  --tfs "5,15,30,60" `
  --coalition-bars 50 `
  --coalition-cohesion 0.62 `
  --coalition-field-score 0.45 `
  --once --pretty
```
**Lit** : blocs coalitions (z_basket + slope + curvature alignés), battlefield relations  
**`coalition-cohesion`** : seuil cohésion minimum [0..1] (défaut 0.62)  
**`coalition-field-score`** : seuil field_score active relation (défaut 0.45)  
**États coalition** : `LOW_ELASTIC_COALITION_RESPRING`, `HIGH_PRESSURE_COALITION_EXPANDING`, `HIGH_PRESSURE_COALITION_FOLDING`  
**Battlefield** : `BATTLEFIELD_WINDOW_OPENING` (score≥0.58), `FIELD_SIDE_SHIFT_ACTIVE` (score≥0.72)  
**Note** : coalition détectée seulement si `abs(z_basket) >= 1.20` ET écarts z/slope/curvature serrés

**Lecture résultat** :
```json
"cross_tf_summary": {
  "battlefield_windows": [15, 30],  // TFs avec fenêtre ouverte
  "dominant_coalition": "USD",      // devise la plus souvent en coalition
  "dominant_antagonist": "JPY",     // antagoniste le plus fréquent
  "compression_detected": true      // 5+ devises neutres, z_spread < 1.5
}
```

---

### Couche 11 — Tension Signature
```powershell
python lab_powerflow.py --query tension `
  --db powerflow.db --symbol GBPUSD `
  --tfs "1,5,15,30,60" `
  --tension-bars 30 `
  --tension-window 5 `
  --once --pretty
```
**Lit** : micro_variance (bar-to-bar) vs macro_variance (tendance)  
**Labels** :
- `ELASTIC_LOADED` (score > 2.5) — micro agitation haute, macro plat → compression avant release
- `DIRECTIONAL_MOVE` (score < 0.35) — macro dominante → mouvement trend lent
- `DEAD_CURRENCY` — équilibré ou amplitude négligeable

**`--tension-window`** : taille fenêtre macro (défaut 5, augmenter pour H4/D1)  
**`--tension-bars`** : barres chargées (défaut 30, augmenter pour H1+)

**Lecture résultat** :
```json
"cross_tf_summary": {
  "elastic_currencies": {"CHF": 2, "USD": 1},  // nbre TFs où ELASTIC_LOADED
  "directional_currencies": {"GBP": 3},
  "top_elastic_global": "CHF"  // devise la plus comprimée globalement
}
```

**Croisements utiles** :
- `ELASTIC_LOADED` + kinematics `speed=SLOW` → compression sans mouvement, attendre release
- `ELASTIC_LOADED` + zone `PRE_EXTREME` → compression extrême imminente
- `DIRECTIONAL_MOVE` + zone `ACCUMULATING` → trend lent en accumulation

---

## SESSION COMPLÈTE — FULL V3

```powershell
# Session MTF tactique — toutes couches
python lab_powerflow.py --query full_v3 `
  --db powerflow.db --symbol GBPUSD `
  --horizons "MTF" `
  --once --lookback 300 `
  --out output/lab_full_v3.json --pretty

# Session HTF stratégique
python lab_powerflow.py --query full_v3 `
  --db powerflow.db --symbol GBPUSD `
  --tfs "60,240,1440" `
  --start "2026-05-06T00:00:00" --end "2026-05-07T23:59:59" `
  --main-tf 1440 `
  --coalition-bars 80 --tension-bars 50 --tension-window 10 `
  --out output/lab_htf.json --pretty

# Session LTF scalping
python lab_powerflow.py --query full_v3 `
  --db powerflow.db --symbol GBPUSD `
  --tfs "1,5,15" `
  --once --lookback 120 `
  --coalition-cohesion 0.55 `
  --out output/lab_ltf.json --pretty
```

**Structure output full_v3** :
```
lab_full_v3.json
├── query, symbol, tfs, horizons, start, end, computed_at
├── kinematics          → couche 1
├── zones               → couche 2
├── nodes               → couche 3
├── turning_points      → couche 4
├── orchestra           → couche 5
├── relational_gravity  → couche 8
├── temporal_density    → couche 9
├── fractal             → couche 7
├── coalitions          → couche 10
└── tension_signature   → couche 11
```

---

## TUNING — QUAND AJUSTER LES SEUILS

### Coalitions — zéro détectée
Si aucune coalition n'apparaît :
```
Option 1 : réduire --coalition-cohesion 0.55  (moins strict)
Option 2 : augmenter --coalition-bars 80       (plus de contexte)
Option 3 : normal si marché en pause (z_basket tous < 1.20)
```

### Tension — tout DEAD_CURRENCY
Si tout est DEAD :
```
Option 1 : réduire --tension-bars 15           (fenêtre plus courte)
Option 2 : réduire --tension-window 3           (macro window plus petite)
Option 3 : normal en overnight ou session morte
```

### H1/H4 — INSUFFICIENT_DATA
Si H1 retourne < 6 barres :
```
Cause : fenêtre --once trop courte (3h = 3 barres H1)
Fix   : --lookback 480 pour H1, --lookback 2880 pour H4
Ou    : utiliser --start / --end avec plage suffisante
```

---

## DÉPENDANCES REQUISES EN CORE

```
pf_lab_engine.py            ← moteur principal
pf_lab_coalitions.py        ← layer 10 (NOUVEAU)
pf_lab_tension.py           ← layer 11 (NOUVEAU)
pf_coalitions.py            ← détection coalitions
pf_coalition_relations.py   ← battlefield relations
pf_tension_signature.py     ← micro/macro variance
pf_personalities.py         ← profils devises
pf_orchestral_gravity_v02.py  ← orchestra
pf_relational_gravity_probe.py  ← relational gravity
pf_temporal_density.py      ← density
pf_flow_nodes.py            ← fractal nodes
db.py                       ← connexion DB
powerflow.db                ← données
```

---

## LECTURE RAPIDE OUTPUT — TOPLINE

```powershell
# Résumé stderr uniquement (pas de JSON)
python lab_powerflow.py --query full_v3 `
  --db powerflow.db --symbol GBPUSD `
  --horizons "MTF" --once --summary-only
```

Output stderr :
```
[LAB] GBPUSD FULL_V3 | 18:16→23:16 | tp_priority=BIRTH | leader=USD | battlefield_tfs=[] | top_elastic=CHF
```

Lecture :
- `tp_priority=BIRTH` — turning point naissant détecté
- `leader=USD` — USD mène l'orchestre
- `battlefield_tfs=[]` — pas de fenêtre de bataille ouverte
- `top_elastic=CHF` — CHF comprimé, élastique en charge

---

## ANTI-BIAIS DOCTRINE

```
Ce lab ne produit pas de signaux.
Ce lab ne produit pas de BUY/SELL.
Ce lab ne retient pas d'informations "par prudence".

Il expose :
  ✅ Tensions accumulées
  ✅ Compressions (ELASTIC_LOADED)
  ✅ Mouvements directionnels (DIRECTIONAL_MOVE)
  ✅ Coalitions (blocs devises qui respirent ensemble)
  ✅ Fenêtres battlefield (rotation opposition)
  ✅ Naissances de mouvement (BIRTH)
  ✅ Contradictions LTF vs HTF (PHASE_OPPOSITION)

Trader filtre.
Trader décide.
```

---

**FIN README**  
Lab PowerFlow V6 — 11 couches — V3 — 2026-05-08
