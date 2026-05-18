# Commandes T0162 - B9 Market Compare Board V0

## Test cible

```powershell
python -m pytest tests\test_t0162_b9_market_compare_board.py
```

## CLI sample

```powershell
python tools\build_t0162_b9_market_compare_board.py --mode sample --sample-dir samples\b9_market_compare_board_v0 --output-dir outputs\b9_market_compare_board_v0_sample
```

## CLI runtime

```powershell
python tools\build_t0162_b9_market_compare_board.py --mode runtime --core-root . --output-dir outputs\b9_market_compare_board_v0 --top-k 8
```
