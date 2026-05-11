# Validation checklist — B1+ HMM + B4+ Wavelet

- [x] `pf_hmm_regime_engine.py` : py_compile PASS
- [x] B1+ HMM actif sans TF1440/H4 si H1+M30+M15 >= 50 observations
- [x] `pf_wavelet_density.py` : py_compile PASS
- [x] Guard multi-TF H1/M30/M15 < 50 observations → INSUFFICIENT_DATA avec fallback B1_LEGACY
- [x] Guard TF5 < 30 rows → INSUFFICIENT_DATA pour Wavelet
- [x] Aucun import `cockpit_*` / `dashboard_*` / `telegram_*` dans `pf_*`
- [x] DB read-only dans tous les modules `pf_*`
- [x] Output JSON prévus dans `output/dashboard_surface/`
- [x] Dual architecture préservée: B1/B1+ et B4/B4+ jamais fusionnés
- [x] WAVELET_SILENT est un état valide, pas une erreur
- [x] Freshness display sur chaque bloc dashboard
- [x] `git_deploy_b1hmm_b4wavelet.ps1` produit rapport PASS/FAIL
- [x] LEXIQUE_PATCH et REGISTRE_PATCH présents dans ZIP

## Vérification locale exécutée dans l'environnement de génération

```text
python -m py_compile pf_hmm_regime_engine.py pf_wavelet_density.py run_hmm_regime_once.py run_wavelet_density_once.py test_hmm_regime.py test_wavelet_density.py
python test_hmm_regime.py
python test_wavelet_density.py
grep imports interdits dans pf_* : PASS
```

## Limite externe

L'accès GitHub depuis l'environnement de génération n'a pas pu résoudre `github.com`. Le script PowerShell inclus réalise le commit/push sur la machine cible disposant de l'accès réseau.
