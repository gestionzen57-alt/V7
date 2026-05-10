# B1 HMM V1.1 Standalone — Reissue

Ce pack remplace la version `hmmlearn` par une version autonome `numpy`.

Marqueurs de vérification :

```powershell
Select-String -Path .\pf_hmm_regime.py -Pattern "hmmlearn"
Select-String -Path .\run_hmm_regime_once.py -Pattern "hmmlearn"
Select-String -Path .\pf_hmm_regime.py -Pattern "V1.1Standalone"
Select-String -Path .\run_hmm_regime_once.py -Pattern "V1.1Standalone"
```

Attendu :
- aucune ligne pour `hmmlearn`
- plusieurs lignes pour `V1.1Standalone`

Validation :

```powershell
python -m py_compile pf_hmm_regime.py run_hmm_regime_once.py
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
Test-Path ..\output\hmm_regime_model.pkl
```
