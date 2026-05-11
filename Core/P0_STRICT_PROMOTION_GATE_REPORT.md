# P0 STRICT PROMOTION GATE V1 — PowerFlow V7.2

## Objet

Débloquer P0 strict sans mentir au moteur.

Le dernier `P0_FINAL_DECISION` montre :

```text
core_steps          : PASS
data_quality_ltf    : PASS
b4                  : PASS_ALIVE
b5                  : PASS_ALIVE
dashboard           : PASS
market_validator    : FAIL_STATIC_SIGNATURE
```

Mais les preuves B4 disent aussi :

```text
static_tfs = []
alive_tfs = GBP_TF1, GBP_TF5, GBP_TF15
series unique/std vivants
dominant_period_bars=1 = LAG1_COMPRESSION
```

Donc `market_open_validator` applique encore l'ancienne règle :

```text
dominant_period_bars=1 => STATIC_SIGNATURE
```

alors que la doctrine post-P0 est :

```text
dominant_period_bars=1 + variance vivante + DQ PASS => LAG1_COMPRESSION
dominant_period_bars=1 + variance nulle => STATIC_SIGNATURE
```

## Fichiers

```text
p0_strict_promotion_gate.py
run_p0_strict_promotion_gate.ps1
P0_STRICT_PROMOTION_GATE_REPORT.md
```

## Installation

Depuis Core :

```powershell
Expand-Archive `
  -Path "$env:USERPROFILE\Downloads\POWERFLOW_P0_STRICT_PROMOTION_GATE_V1.zip" `
  -DestinationPath ".\_p0_strict_gate_v1" `
  -Force

copy .\_p0_strict_gate_v1\runtime\p0_strict_promotion_gate.py .\ -Force
copy .\_p0_strict_gate_v1\runtime\run_p0_strict_promotion_gate.ps1 .\ -Force
copy .\_p0_strict_gate_v1\docs\P0_STRICT_PROMOTION_GATE_REPORT.md .\ -Force
```

## Test sans overwrite

```powershell
python .\p0_strict_promotion_gate.py --root .
Get-Content .\output\P0_STRICT_PROMOTION_DECISION.md
```

## Promotion finale

```powershell
.\run_p0_strict_promotion_gate.ps1 -Root . -PromoteFinal
```

Cela backup puis remplace :

```text
output/P0_FINAL_DECISION.json
output/P0_FINAL_DECISION.md
```

## Commit recommandé

```powershell
git add p0_strict_promotion_gate.py
git add run_p0_strict_promotion_gate.ps1
git add P0_STRICT_PROMOTION_GATE_REPORT.md

git commit -m "P0: add strict promotion gate for stale market validator semantics"
git push
```

Ne pas committer `output/`.
