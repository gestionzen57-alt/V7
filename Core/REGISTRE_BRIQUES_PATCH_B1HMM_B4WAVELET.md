# Registre briques patch — B1+ HMM MTF + B4+ Wavelet

## B1+ HMM MTF — Regime Engine

```text
Fichier      : pf_hmm_regime_engine.py
Runner       : run_hmm_regime_once.py
Statut       : READY / DUAL / STANDALONE / MULTI_TIMEFRAME
Rôle         : Détecte le régime via Gaussian HMM à 4 états cachés sur stack H1/M30/M15.
Lit          : powerflow.db / force_snapshots / TF60, TF30, TF15 par défaut / H4-D bonus / symbol paramétrique / read-only
Produit      : output/dashboard_surface/regime_hmm.json
Dépend de    : numpy, hmmlearn ; fallback local si hmmlearn indisponible
Utilisé par  : dashboard_surface dual, cockpit lecture, orchestrator step regime si intégré
Limitations  : 50 observations multi-TF agrégées requises ; TF1440/H4 ne bloquent jamais l'activation tactique
```

### Contrat de sortie B1+ HMM

```text
regime_hmm               : COMPRESSION | TENDANCE | RANGE | TRANSITION | null
regime_confidence_hmm    : 0.0-1.0
state_probabilities      : dict des 4 états
method                   : HMM_GAUSSIAN
status                   : ACTIVE | INSUFFICIENT_DATA
fallback                 : null | B1_LEGACY
rows_used                : rows tactiques agrégées
observations_used        : observations réellement utilisées
rows_used_by_tf          : dict par TF
regime_scope             : MULTI_TF_TACTICAL | HTF_ENRICHED
timeframes_requested     : [60,30,15] par défaut
timeframes_used          : TF réellement exploités
activation_guard         : MIN_MTF_OBSERVATIONS>=50
technical_risks          : risques techniques uniquement
```

## B4+ Wavelet — Morlet Density Engine

```text
Fichier      : pf_wavelet_density.py
Runner       : run_wavelet_density_once.py
Statut       : READY / DUAL / STANDALONE
Rôle         : Détecte densité temporelle non stationnaire via CWT Morlet.
Lit          : powerflow.db / force_snapshots / TF1, TF5, TF15 / symbol paramétrique / read-only
Produit      : output/dashboard_surface/wavelet.json
Dépend de    : numpy, PyWavelets (import pywt) ; fallback convolution Morlet local si pywt indisponible
Utilisé par  : dashboard_surface dual, cockpit lecture, orchestrator step temporal density si intégré
Limitations  : TF5 >= 30 rows propres requis ; WAVELET_SILENT est un état valide, pas une erreur
```
