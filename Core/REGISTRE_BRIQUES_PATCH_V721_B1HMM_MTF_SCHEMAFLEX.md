# REGISTRE BRIQUES PATCH - PowerFlow V7.2.1

**Patch :** B1+ HMM MTF Schema-Flex + B4+ Wavelet Morlet Schema-Flex  
**Date :** 2026-05-11  
**Commit fonctionnel :** `71c2f91`  
**Commit documentation :** `50062c8`  
**Statut :** VALIDE / PUSHE / ACTIVE  
**Architecture :** Dual perception - jamais fusionnee  
**Doctrine :** Perception, mesure, qualification technique. Aucun BUY/SELL.

---

## 1. OBJECTIF DU PATCH

Ce patch officialise dans le registre PowerFlow V7.2.1 les deux briques livrees et corrigees :

1. **B1+ HMM MTF Schema-Flex**
   - Regime probabiliste multi-timeframe.
   - Activation sur stack tactique `H1 / M30 / M15`.
   - `TF1440` et `H4` deviennent enrichissants, jamais bloquants.
   - Compatible avec schemas DB flexibles.

2. **B4+ Wavelet Morlet Schema-Flex**
   - Densite temporelle non-stationnaire par CWT Morlet.
   - Detection multi-echelle sur `M1 / M5 / M15`.
   - Compatible avec schemas DB flexibles.

Les deux briques restent duales de leurs versions existantes :

```text
B1 Legacy  !=  B1+ HMM
B4 Rolling !=  B4+ Wavelet
```

Aucune fusion.
Aucune moyenne.
Aucune selection arbitraire par la machine.

---

## 2. B1+ HMM MTF SCHEMA-FLEX

```text
Fichier     : pf_hmm_regime_engine.py
Runner      : run_hmm_regime_once.py
Brique      : B1+
Statut      : ACTIVE - VALIDE - PUSHE
Commit      : 71c2f91
Methode     : HMM_GAUSSIAN_FALLBACK_NUMPY
Scope       : MULTI_TF_TACTICAL ou HTF_ENRICHED
```

### Role

Detecte le regime comportemental du flux via modele a etats caches sur observations multi-timeframe.

Etats produits :

```text
COMPRESSION
TENDANCE
RANGE
TRANSITION
```

### Lit

```text
DB : powerflow.db
Table principale : force_snapshots
Mode : READ ONLY uniquement
Connexion : sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

### Timeframes utilises

#### Stack actif par defaut

```text
60  -> H1
30  -> M30
15  -> M15
```

Ces timeframes suffisent a activer B1+ si le nombre d'observations agregees est suffisant.

#### Contextes enrichissants

```text
240  -> H4
1440 -> D
```

Ces timeframes enrichissent la lecture si disponibles, mais ne bloquent jamais le moteur.

### Produit

```text
output/dashboard_surface/regime_hmm.json
```

Structure de sortie principale :

```json
{
  "symbol": "GBPUSD",
  "regime_hmm": "TRANSITION",
  "regime_confidence_hmm": 0.460418,
  "state_probabilities": {
    "COMPRESSION": 0.147249,
    "TENDANCE": 0.209628,
    "RANGE": 0.182705,
    "TRANSITION": 0.460418
  },
  "method": "HMM_GAUSSIAN_FALLBACK_NUMPY",
  "status": "ACTIVE",
  "fallback": null,
  "rows_used": 973,
  "mtf_timeframes": [60, 30, 15],
  "context_timeframes": [240, 1440],
  "regime_scope": "HTF_ENRICHED",
  "schema_mode": "wide_currency",
  "observed_columns": [
    "force_gbp",
    "force_usd",
    "force_eur",
    "force_jpy",
    "force_cad",
    "force_chf",
    "force_aud"
  ],
  "time_column": "created_at",
  "timeframe_column": "timeframe",
  "symbol_column": "symbol",
  "technical_risks": [
    "HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED"
  ],
  "timestamp_utc": "2026-05-11T14:00:40.950041+00:00"
}
```

### Depend de

```text
numpy
sqlite3
datetime
statistics
```

`hmmlearn` est optionnel.

Si `hmmlearn` est indisponible :

```text
method = HMM_GAUSSIAN_FALLBACK_NUMPY
technical_risks += HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED
```

### Ne depend pas de

```text
pf_regime_engine.py
cockpit_*
dashboard_*
telegram_*
powerflow.db en ecriture
```

### Utilise par

```text
run_hmm_regime_once.py
dashboard_surface/regime_hmm.json
dashboard V7.2 section Regime HTF dual
cockpit synthese dual si lecture JSON
mapper comportemental si injection regime_context dual
```

### Limitations techniques

```text
HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED
-> Sur Python 3.14, hmmlearn peut necessiter Microsoft C++ Build Tools.
-> Le fallback NumPy maintient l'activation du moteur.

SCHEMA_FLEX_AUTO_DETECTION
-> Le moteur depend de l'introspection correcte des colonnes DB.
-> Si aucune colonne numerique exploitable n'existe, status = INSUFFICIENT_DATA.

LOW_OBSERVATION_COUNT
-> Si H1/M30/M15 agreges < seuil minimal, fallback = B1_LEGACY.
```

### Regles de non-regression

```text
NE PAS revenir a TF1440 >= 50 comme condition bloquante unique.
Le seuil doit rester multi-TF agrege.
H4/D sont enrichissants, pas bloquants.
Exposer les probabilites d'etat, ne pas fusionner avec B1 Legacy.
Conserver DB read-only.
```

---

## 3. B4+ WAVELET MORLET SCHEMA-FLEX

```text
Fichier     : pf_wavelet_density.py
Runner      : run_wavelet_density_once.py
Brique      : B4+
Statut      : ACTIVE - VALIDE - PUSHE
Commit      : 71c2f91
Methode     : CWT_MORLET
Scope       : LTF / MTF density
```

### Role

Detecte les cycles non-stationnaires et les structures multi-echelles via transformee ondelette continue Morlet.

Etats produits :

```text
WAVELET_COMPRESSING
WAVELET_EXPANDING
WAVELET_MULTI_SCALE
WAVELET_TRANSITIONING
WAVELET_SILENT
```

`WAVELET_SILENT` est un etat valide, pas une panne.

### Lit

```text
DB : powerflow.db
Table principale : force_snapshots
Mode : READ ONLY uniquement
Connexion : sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

### Timeframes utilises

```text
1  -> M1
5  -> M5
15 -> M15
```

### Produit

```text
output/dashboard_surface/wavelet.json
```

Structure de sortie principale :

```json
{
  "symbol": "GBPUSD",
  "status": "ACTIVE",
  "method": "CWT_MORLET",
  "currency": "GBP",
  "timeframes": [1, 5, 15],
  "schema_mode": "wide_currency",
  "source_column": "force_gbp",
  "technical_risks": [],
  "results": [
    {
      "currency": "GBP",
      "timeframe": 1,
      "wavelet_state": "WAVELET_MULTI_SCALE",
      "dominant_scale_bars": 21,
      "wavelet_energy_ratio": 0.112902,
      "scale_drift_direction": "COMPRESSING",
      "multi_scale_flag": true,
      "compression_onset": false,
      "method": "CWT_MORLET",
      "rows_used": 7261,
      "technical_risks": [],
      "schema_mode": "wide_currency",
      "source_column": "force_gbp"
    }
  ],
  "timestamp_utc": "2026-05-11T14:00:41.360403+00:00"
}
```

### Depend de

```text
numpy
pywt / PyWavelets
sqlite3
datetime
```

### Ne depend pas de

```text
pf_temporal_density.py
cockpit_*
dashboard_*
telegram_*
powerflow.db en ecriture
```

### Utilise par

```text
run_wavelet_density_once.py
dashboard_surface/wavelet.json
dashboard V7.2 section Densite Temporelle dual
cockpit synthese dual si lecture JSON
mapper comportemental si injection density_context dual
```

### Limitations techniques

```text
PYWAVELETS_REQUIRED
-> PyWavelets doit etre disponible pour CWT Morlet.

WAVELET_SENSITIVE_TO_NOISE
-> Risque technique de faux positif multi-scale sur microfilm tres agite.

SCHEMA_FLEX_AUTO_DETECTION
-> Le moteur utilise la premiere colonne de force compatible avec la devise cible.
-> Si aucune force specifique n'est trouvee, il peut basculer sur un flux numerique exploitable.

TF5_INSUFFICIENT_DATA
-> Si TF5 est trop mince, status = INSUFFICIENT_DATA.
```

### Regles de non-regression

```text
Ne jamais fusionner B4 Rolling et B4+ Wavelet.
Ne jamais traiter WAVELET_SILENT comme erreur.
Exposer wavelet_state par timeframe.
Exposer dominant_scale_bars, wavelet_energy_ratio, scale_drift_direction.
Conserver DB read-only.
```

---

## 4. SCHEMA-FLEX - REGLE TRANSVERSALE

Les deux briques supportent plusieurs formes de schema `force_snapshots`.

### Modes supportes

```text
wide_currency
-> Colonnes de type force_gbp, force_usd, force_eur, etc.

wide_plain_currency
-> Colonnes de type gbp, usd, eur, etc.

long_currency_value
-> Colonnes de type currency + value / force / score.

numeric_stream
-> Flux numerique generique si aucune colonne devise explicite n'est trouvee.
```

### Colonnes temporelles supportees

```text
created_at
timestamp
time
ts
datetime
date
rowid
```

### Colonnes timeframe supportees

```text
timeframe
tf
period
interval
```

### Colonnes symbol supportees

```text
symbol
pair
instrument
```

### Regle PowerFlow

```text
Le moteur doit s'adapter au schema reel de la DB.
Il ne doit pas crasher sur une difference de nommage.
Il doit exposer schema_mode, source_column, time_column, timeframe_column, symbol_column.
```

---

## 5. INTEGRATION DASHBOARD SURFACE

### Fichiers surface

```text
output/dashboard_surface/regime_hmm.json
output/dashboard_surface/wavelet.json
```

### Attributs dashboard recommandes

```html
data-brick="B1_HMM"
data-brick="B4_WAVELET"
data-method="HMM_GAUSSIAN_FALLBACK_NUMPY"
data-method="CWT_MORLET"
data-freshness="FRESH | AGING | STALE"
data-age-seconds="..."
```

### Regle dual display

```text
B1 Legacy + B1+ HMM affiches cote a cote.
B4 Rolling + B4+ Wavelet affiches cote a cote.
Aucune moyenne.
Aucune fusion.
Divergence exposee.
```

---

## 6. COMMANDES DE VALIDATION

```powershell
python -m py_compile pf_hmm_regime_engine.py pf_wavelet_density.py run_hmm_regime_once.py run_wavelet_density_once.py

python test_hmm_regime.py
python test_wavelet_density.py

python run_hmm_regime_once.py --db powerflow.db --symbol GBPUSD --tfs 60,30,15 --pretty

python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
```

Resultat valide observe :

```text
B1+ HMM : ACTIVE / rows_used=973 / schema_mode=wide_currency / regime_scope=HTF_ENRICHED
B4+ Wavelet : ACTIVE / schema_mode=wide_currency / source_column=force_gbp
```

---

## 7. IMPACT ARCHITECTURAL

```text
Couche 0 : capture_bridge.py inchange
Couche 1 : nouveaux moteurs pf_* read-only
Couche 2 : runners CLI
Couche 3 : dashboard lit JSON surface
Couche 4 : telegram non impacte
Couche 5 : trader arbitre
```

Aucune dependance circulaire introduite.
Aucune ecriture DB introduite.
Aucun BUY/SELL introduit.
Aucune fusion dual introduite.

---

## 8. STATUT FINAL

```text
B1+ HMM MTF Schema-Flex        : ACTIVE / VALIDE / PUSHE
B4+ Wavelet Morlet Schema-Flex : ACTIVE / VALIDE / PUSHE
Docs rapport complet           : PUSHE
Lexique patch                  : PUSHE
Registre patch                 : A COMMITER via ce patch
```

Apres commit de ce fichier :

```text
Continuite documentaire multi-IA : OK
Claude prochain fil : peut lire les briques et limites directement dans Git
```

---

*REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX - PowerFlow V7.2.1 - 2026-05-11*

