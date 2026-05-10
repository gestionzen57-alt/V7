# RAPPORT TECHNIQUE — B7 Fractal Resonance Detection

**Projet :** PowerFlow V7.1  
**Brique :** B7 — Fractal Resonance Detection  
**Mission :** détecter si plusieurs timeframes vibrent ensemble ou si un étage est en retard  
**Statut :** livrable prêt à intégrer  
**Commit cible :** `B7: Fractal Resonance Detection`

---

## 1. Résumé opérationnel

B7 ajoute une lecture de synchronisation fractale entre timeframes adjacents.

La brique répond à une question simple :

```text
M1, M5, M15, M30, H1 vibrent-ils sur le même événement,
ou est-ce que certains timeframes sont en retard ?
```

Ce n'est pas une brique de prédiction. C'est une brique de perception temporelle.

États produits :

```text
RESONANT  -> plusieurs TF vibrent ensemble, même direction, faible lag
LAGGED    -> corrélation présente mais délai visible entre TF
DISSONANT -> corrélation faible, TF partiellement indépendants
SILENT    -> aucune synchronisation exploitable ou données insuffisantes
```

---

## 2. Fichiers livrés

```text
Core/pf_fractal_resonance.py
Core/run_fractal_resonance_once.py
output/fractal_resonance.json
commit_b7_fractal_resonance.ps1
```

---

## 3. Architecture respectée

```text
pf_fractal_resonance.py
  Couche 1 moteur pf_*
  Aucun import cockpit/dashboard/telegram
  Aucun accès DB direct
  Aucun BUY/SELL
  Aucune décision de trade

run_fractal_resonance_once.py
  Couche 2 runner run_*
  Lecture DB read-only : sqlite3.connect(file:...?mode=ro, uri=True)
  Écrit uniquement output/fractal_resonance.json
```

---

## 4. Algorithme

### 4.1 Chargement

Le runner charge les N dernières valeurs par timeframe depuis :

```text
Table : force_snapshots
Colonnes attendues : timeframe, timestamp, force_gbp / force_usd / force
```

Par défaut pour `GBPUSD`, la colonne prioritaire est :

```text
force_gbp
```

Fallbacks intégrés :

```text
force_<base>
force_<quote>
force
angle_kalman
angle
force_gbp
force_usd
```

### 4.2 Corrélation

Pour chaque paire adjacente disponible :

```text
(1, 5)
(5, 15)
(15, 30)
(30, 60)
(60, 240)
```

B7 prend une fenêtre rolling de 50 barres, aligne les deux séries par la queue, normalise en z-score, puis calcule :

```text
correlation = np.corrcoef(s1_norm, s2_norm)[0, 1]
```

### 4.3 Lag detection

B7 scanne les décalages de `-max_lag` à `+max_lag` et mesure la meilleure corrélation croisée.

```text
lag > 0 : le second TF traîne le premier
lag < 0 : le second TF semble en avance
lag = 0 : synchronisation directe
```

### 4.4 Classification

Classification signée positive. Une corrélation inverse forte n'est pas classée RESONANT, car B7 cherche une vibration directionnelle similaire entre TF adjacents.

```text
corr >= 0.80 et lag faible  -> RESONANT
corr >= 0.60               -> LAGGED
corr >= 0.30               -> DISSONANT
sinon                      -> SILENT
```

Globalement :

```text
resonance_score = moyenne des corrélations positives valides
avg_signed_correlation = moyenne signée brute
```

---

## 5. Format JSON produit

```json
{
  "timestamp": "2026-05-10T00:39:19Z",
  "symbol": "GBPUSD",
  "resonance_state": "RESONANT",
  "resonance_score": 0.988912,
  "avg_signed_correlation": 0.988912,
  "resonant_tfs": [1, 5, 15, 30, 60],
  "lagged_tfs": [],
  "dissonant_tfs": [],
  "pair_correlations": {
    "(1, 5)": 0.993122,
    "(5, 15)": 0.993502,
    "(15, 30)": 0.976461,
    "(30, 60)": 0.992562
  },
  "pair_states": {
    "(1, 5)": "RESONANT",
    "(5, 15)": "RESONANT",
    "(15, 30)": "RESONANT",
    "(30, 60)": "RESONANT"
  },
  "lag_detection": {
    "(1, 5)": 0,
    "(5, 15)": 0,
    "(15, 30)": 2,
    "(30, 60)": 0
  },
  "expected_amplification": true,
  "technical_risks": [],
  "method": "cross_correlation_multi_tf",
  "valid": true
}
```

---

## 6. Validation locale effectuée

Validation faite sur SQLite synthétique compatible schema PowerFlow :

```text
symbol text
timeframe integer
timestamp text
force_gbp real
force_usd real
```

Checks :

```text
OK  python -m py_compile Core/pf_fractal_resonance.py
OK  python -m py_compile Core/run_fractal_resonance_once.py
OK  runner --db Core/powerflow.db --tfs 1,5,15,30,60 --pretty
OK  output/fractal_resonance.json valide via python -m json.tool
OK  stabilité 3 runs : même resonance_state, même score
```

Exemple stabilité :

```text
Run 1: RESONANT 0.993312
Run 2: RESONANT 0.993312
Run 3: RESONANT 0.993312
```

---

## 7. Commandes d'intégration dans ton repo

Depuis la racine du repo V7 :

```powershell
python -m py_compile Core\pf_fractal_resonance.py Core\run_fractal_resonance_once.py
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --pretty
python -m json.tool .\output\fractal_resonance.json | Out-Null
```

Commit :

```powershell
git add Core\pf_fractal_resonance.py Core\run_fractal_resonance_once.py
git commit -m "B7: Fractal Resonance Detection"
```

Ou utiliser :

```powershell
.\commit_b7_fractal_resonance.ps1
```

---

## 8. Risques techniques résiduels

```text
INSUFFICIENT_DATA
  Moins de 50 barres disponibles sur une paire TF.

FLAT_SERIES
  Série figée ou weekend, std proche de zéro.

CORRELATION_UNSTABLE
  Corrélation non finie ou dispersion excessive.

LAGGED_MULTIPLE_TF
  Plusieurs paires montrent un lag supérieur au seuil.

SILENT_HTF
  H1/H4 présents mais synchronisation trop faible.
```

Ces risques qualifient la perception. Ils ne censurent pas l'information.

---

## 9. Intégration future

### Mapper

Injection possible dans `pf_behavioral_alert_mapper.py` :

```python
fractal_context = FractalResonanceAnalyzer().analyze_multi_tf(series_by_tf, symbol=symbol)
alert["fractal_resonance"] = fractal_context
```

### Orchestrateur

Step à ajouter dans `run_powerflow_cycle_once.py` après B3/B4 ou avant dashboard refresh :

```powershell
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60
```

### Dashboard

Card future :

```text
State: RESONANT / LAGGED / DISSONANT / SILENT
Score: resonance_score
Resonant TFs
Lagged TFs
Expected amplification
```

---

## 10. Checkpoint final

```text
B7 Fractal Resonance Detection est prête.
La machine mesure la synchronisation fractale.
Elle distingue vibration commune, retard, dissonance et silence.
Le trader lit la synchronisation.
Le trader décide.
```
