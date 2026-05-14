# POWERFLOW V7.6.5 — GBPUSD ONLY CYCLE RUNNER REPORT

## 0. Mission

Forcer le cycle operationnel PowerFlow V7.6.5 a travailler uniquement sur `GBPUSD`, sans casser :

- `run_powerflow_v76_telegram_cycle.ps1`
- `Core/scheduler_powerflow_turbo_wrapper.py`
- le terrain packet
- Telegram FR
- le legacy adapter
- le mode `-TelegramMode send`

Scope actif :

```text
GBPUSD ONLY
```

Hors scope volontaire :

```text
EURUSD
USDJPY
XAUUSD
```

---

## 1. Diagnostic attendu

Le scheduler lance encore un panier multi-symbol historique :

```text
GBPUSD,EURUSD,USDJPY
```

Ce comportement est coherent avec l'ancienne infrastructure multi-symbol, mais il n'est plus conforme au scope operationnel V7.6.5.

Le patch doit donc agir au niveau orchestration / scheduler, pas au niveau logique terrain.

---

## 2. Principe du patch minimal

Le patch applique une regle simple :

```text
Tout cycle operationnel V7.6.5 normalise les symboles vers GBPUSD uniquement.
```

Implication :

- si aucun symbole n'est fourni : `GBPUSD`
- si `GBPUSD,EURUSD,USDJPY` est fourni par legacy/scheduler : `GBPUSD`
- si un symbole autre que `GBPUSD` est fourni : warning technique + fallback `GBPUSD`
- aucune modification de terrain packet
- aucune modification Telegram token
- aucune modification du mode send

---

## 3. Fichiers cibles

```text
run_powerflow_v76_telegram_cycle.ps1
Core/scheduler_powerflow_turbo_wrapper.py
```

---

## 4. Changement PowerShell

### Objectif

Ajouter un parametre operationnel explicite :

```powershell
[string]$Symbol = "GBPUSD"
```

Puis normaliser :

```powershell
$ActiveSymbol = "GBPUSD"
$env:POWERFLOW_SYMBOL = "GBPUSD"
$env:POWERFLOW_SYMBOLS = "GBPUSD"
```

Et transmettre au scheduler core :

```powershell
python .\Core\scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD
```

### Pourquoi env + CLI ?

Double compatibilite :

- CLI explicite pour le wrapper moderne
- env fallback pour tout code legacy qui lit encore `POWERFLOW_SYMBOL` ou `POWERFLOW_SYMBOLS`

---

## 5. Changement Python wrapper

### Objectif

Ajouter une fonction centrale :

```python
def normalize_symbols_for_v765(symbols: str | list[str] | None) -> list[str]:
    return ["GBPUSD"]
```

Cette fonction doit etre appliquee juste apres parsing CLI / env et avant toute boucle scheduler.

### Regle

Le wrapper peut encore accepter `--symbols`, mais V7.6.5 force l'univers operationnel a `GBPUSD`.

Cela evite :

- lancement EURUSD parasite
- lancement USDJPY parasite
- modifications terrain inutiles
- divergence Telegram entre dry-run et send

---

## 6. Verification demandee

Commande cible :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode dry-run
```

Attendu :

```text
GBPUSD present
EURUSD absent
USDJPY absent
```

Commande send a conserver :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send
```

Attendu :

```text
Mode send operationnel
Aucun token Telegram touche
Aucun changement terrain packet
```

---

## 7. Test PowerShell copier-coller

```powershell
Set-Location "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"

$log = Join-Path $PWD "output\test_gbpusd_only_cycle.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

.\run_powerflow_v76_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode dry-run *> $log

Write-Host "--- GBPUSD ONLY CYCLE TEST ---"
Write-Host "Log: $log"

$txt = Get-Content $log -Raw

if ($txt -notmatch "GBPUSD") {
    throw "FAIL: GBPUSD non detecte dans le cycle."
}

if ($txt -match "EURUSD|USDJPY") {
    throw "FAIL: symbole hors scope detecte: EURUSD ou USDJPY."
}

Write-Host "PASS: cycle dry-run limite a GBPUSD uniquement."
```

---

## 8. Risques techniques

| Risque | Cause | Mitigation |
|---|---|---|
| Patch diff ne s'applique pas | fichier local different | utiliser `tools/apply_gbpusd_only_cycle_patch.ps1` ou appliquer manuellement les blocs |
| Symboles encore visibles dans anciens logs | logs historiques non nettoyes | tester uniquement logs du run courant |
| Wrapper ignore `--symbols` | parser absent | ajouter argparse minimal ou utiliser env fallback |
| Scheduler interne hardcode une liste | list literal dans wrapper | remplacer par `normalize_symbols_for_v765(...)` avant boucle |

---

## 9. Acceptance criteria

```text
[ ] run_powerflow_v76_telegram_cycle.ps1 accepte ou force GBPUSD
[ ] Core/scheduler_powerflow_turbo_wrapper.py normalise vers GBPUSD
[ ] dry-run scheduler ne lance que GBPUSD
[ ] send reste operationnel
[ ] aucun token Telegram modifie
[ ] aucun changement terrain packet
[ ] aucun ajout EURUSD / USDJPY
```

---

## 10. Verdict

Patch minimal recommande :

```text
PowerShell = scope explicite + env fallback
Python wrapper = normalisation defensive avant boucle
```

Ce patch ne change pas la perception terrain. Il limite seulement le champ operationnel du cycle courant.

