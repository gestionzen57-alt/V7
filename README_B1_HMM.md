# PowerFlow B1 HMM Regime Upgrade

Livrables :

- `Core/pf_hmm_regime.py`
- `Core/run_hmm_regime_once.py`
- `requirements_hmm.txt`

## Installation dépendances

```powershell
python -m pip install -r requirements_hmm.txt
```

ou :

```powershell
python -m pip install hmmlearn scikit-learn numpy scipy
```

## Validation

Depuis la racine du repo :

```powershell
python -m py_compile Core\pf_hmm_regime.py Core\run_hmm_regime_once.py
python Core\run_hmm_regime_once.py --db Core\powerflow.db --train --predict --pretty
python -m json.tool output\hmm_regime_result.json | Out-Null
```

Depuis `Core` :

```powershell
python -m py_compile pf_hmm_regime.py run_hmm_regime_once.py
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
```

## Stabilité

```powershell
python Core\run_hmm_regime_once.py --db Core\powerflow.db --predict --pretty > hmm1.json
python Core\run_hmm_regime_once.py --db Core\powerflow.db --predict --pretty > hmm2.json
python Core\run_hmm_regime_once.py --db Core\powerflow.db --predict --pretty > hmm3.json
```

Les trois runs doivent garder le même `regime`, `raw_state`, et des probabilités identiques à données constantes.

## Commit

```powershell
git add Core\pf_hmm_regime.py Core\run_hmm_regime_once.py requirements_hmm.txt
git commit -m "B1: HMM Gaussian regime upgrade"
git push
```
