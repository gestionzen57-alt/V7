# B4 Wavelet Density - Validation locale

## Fichiers livrés

- `Core/pf_wavelet_density.py`
- `Core/run_wavelet_density_once.py`
- `output/wavelet_density.json`

## Checks exécutés ici

```powershell
python -m py_compile Core\pf_wavelet_density.py Core\run_wavelet_density_once.py
python Core\run_wavelet_density_once.py --db <sample_db> --tfs 1,5,15 --pretty --output output\wavelet_density.json
python -m json.tool output\wavelet_density.json
```

Statut : OK sur base SQLite synthétique.

## Checks à lancer dans le dépôt réel

```powershell
cd Core
pip install PyWavelets numpy scipy
python -m py_compile pf_wavelet_density.py run_wavelet_density_once.py
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty --output output/wavelet_density.json
python -m json.tool output/wavelet_density.json > $null
```

## Commit

```powershell
git status
git add Core/pf_wavelet_density.py Core/run_wavelet_density_once.py Core/output/wavelet_density.json
git commit -m "B4: Morlet Wavelet CWT upgrade"
git push
```

Si `output/` est ignoré par Git, c'est normal dans PowerFlow V7 : committer seulement les deux fichiers Python.
