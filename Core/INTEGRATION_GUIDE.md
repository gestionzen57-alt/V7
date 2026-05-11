# PowerFlow V7.2.1 — Integration Guide B1+ HMM MTF + B4+ Wavelet

## Position architecture

- `pf_hmm_regime_engine.py` appartient à la couche 1 `pf_*`.
- `pf_wavelet_density.py` appartient à la couche 1 `pf_*`.
- Les deux modules lisent `powerflow.db` en read-only via `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)`.
- Aucun module `pf_*` n'importe `cockpit_*`, `dashboard_*` ou `telegram_*`.
- B1+ HMM ne remplace pas B1 Legacy.
- B4+ Wavelet ne remplace pas B4 Rolling.

## Correction V7.2.1 — HMM multi-timeframe

Le guard B1+ HMM n'attend plus `TF1440 >= 50 rows`.

Doctrine corrigée :

```text
B1+ HMM = régime probabiliste multi-TF.
Default stack : H1 / M30 / M15 = 60,30,15.
H4 / D = contexte bonus si disponible.
H4 / D / TF1440 ne bloquent jamais l'activation tactique.
```

Activation :

```text
ACTIVE si observations agrégées multi-TF >= 50
INSUFFICIENT_DATA seulement si H1+M30+M15 n'apportent pas assez d'observations
fallback=B1_LEGACY seulement dans ce cas
```

Nouveaux champs `regime_hmm.json` :

```json
{
  "timeframes_requested": [60, 30, 15],
  "timeframes_used": [15, 30, 60],
  "rows_used_by_tf": {"15": 20, "30": 20, "60": 20},
  "observations_used": 60,
  "regime_scope": "MULTI_TF_TACTICAL | HTF_ENRICHED",
  "activation_guard": "MIN_MTF_OBSERVATIONS>=50"
}
```

## Fichiers à copier dans `Core/`

```text
pf_hmm_regime_engine.py
pf_wavelet_density.py
run_hmm_regime_once.py
run_wavelet_density_once.py
test_hmm_regime.py
test_wavelet_density.py
dashboard_surface_dual_patch.html
INSTALL_REQUIREMENTS.txt
LEXIQUE_PATCH_B1HMM_B4WAVELET.md
REGISTRE_BRIQUES_PATCH_B1HMM_B4WAVELET.md
validation_checklist.md
```

## Commandes manuelles

```powershell
python -m py_compile pf_hmm_regime_engine.py pf_wavelet_density.py run_hmm_regime_once.py run_wavelet_density_once.py
python test_hmm_regime.py
python test_wavelet_density.py
python run_hmm_regime_once.py --db powerflow.db --symbol GBPUSD --tfs 60,30,15 --pretty
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
```

## Outputs dashboard surface

```text
output/dashboard_surface/regime_hmm.json
output/dashboard_surface/wavelet.json
```

## Affichage dual

Insérer `dashboard_surface_dual_patch.html` dans le dashboard existant en gardant les blocs côte à côte:

```text
B1 Legacy   : regime_legacy.json
B1+ HMM MTF : regime_hmm.json
B4 Rolling  : temporal_density_state.json
B4+ Wavelet : wavelet.json
```

Freshness standard:

```text
FRESH si age_seconds < 300
AGING si 300 <= age_seconds < 600
STALE si age_seconds >= 600
```

## Risques techniques

- `MULTI_TF_INSUFFICIENT_OBSERVATIONS`: HMM retourne fallback B1_LEGACY seulement si H1/M30/M15 agrégés restent sous le seuil.
- `HTF_CONTEXT_THIN_BUT_NOT_BLOCKING`: H4/D absents ou trop fins ; le régime reste tactique multi-TF, non bloqué.
- `TF5_INSUFFICIENT_ROWS`: Wavelet retourne INSUFFICIENT_DATA tant que TF5 < 30 rows.
- `HMMLEARN_FALLBACK_HEURISTIC_USED`: hmmlearn indisponible ou fit instable ; le module produit une perception softmax de secours mais l'installation de hmmlearn doit être corrigée.
- `PYWT_FALLBACK_USED`: PyWavelets indisponible ; le module utilise une approximation convolution Morlet locale.
