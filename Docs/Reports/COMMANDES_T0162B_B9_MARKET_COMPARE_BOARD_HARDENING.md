# Commandes T0162B — B9 Market Compare Board Hardening

## Installation depuis Downloads

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0162b_b9_market_compare_board_hardening.ps1"
```

## Git commit + push

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0162b_b9_market_compare_board_hardening.ps1"
```

## CLI sample

```powershell
python tools\build_t0162_b9_market_compare_board.py --mode sample --core-root . --sample-dir samples\b9_market_compare_board_v0 --output-dir outputs\b9_market_compare_board_v0_sample --top-k 8
```

## CLI runtime

```powershell
python tools\build_t0162_b9_market_compare_board.py --mode runtime --core-root . --output-dir outputs\b9_market_compare_board_v0 --top-k 8
```

## CLI runtime strict

```powershell
python tools\build_t0162_b9_market_compare_board.py --mode runtime --core-root . --output-dir outputs\b9_market_compare_board_v0 --top-k 8 --strict-exit
```
