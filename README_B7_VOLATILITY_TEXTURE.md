# B7+ Volatility Texture Engine — VolatilityTextureV0.1Standalone

## Fichiers

```text
Core/pf_volatility_texture.py
Core/run_volatility_texture_once.py
tests/test_volatility_texture.py
docs/PATCH_INTEGRATION_VOLATILITY_TEXTURE.md
```

## Installation

Dépendance unique :

```powershell
python -m pip install numpy
```

## Validation

Depuis la racine du repo :

```powershell
python -m py_compile Core\pf_volatility_texture.py Core\run_volatility_texture_once.py
python -m pytest tests\test_volatility_texture.py -v
```

Depuis `Core` :

```powershell
python -m py_compile pf_volatility_texture.py run_volatility_texture_once.py
python run_volatility_texture_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --recent-bars 100 --pretty
python -m json.tool ..\output\volatility_texture.json | Out-Null
```

## Sortie

```json
{
  "volatility_texture": {
    "type": "STRUCTURAL",
    "confidence": 0.84,
    "micro_macro_ratio": 1.23,
    "spread_behavior": "STABLE",
    "pattern_consistency": 0.81
  }
}
```

## Doctrine

Texture qualifie la nature du mouvement. Elle ne filtre pas l'alerte, ne prédit pas, ne décide pas.
