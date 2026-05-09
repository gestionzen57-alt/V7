# Telegram Trader Alert V0.1.2 - 4 Modes

Copier ces fichiers `.bat` dans le dossier core PowerFlow :

`C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\`

## Modes

### OFF
Aucun message Telegram.

```powershell
python telegram_trader_alert_v01.py --mode OFF --summary
```

### HOT_ONLY
Envoie uniquement si :

```text
trader_alert_ready = true
level = HOT
freshness in FRESH / RECENT
```

```powershell
python telegram_trader_alert_v01.py --mode HOT_ONLY --summary
```

### SCALPING
Envoie si :

```text
trader_alert_ready = true
level in HOT / WATCH
freshness in FRESH / RECENT
```

```powershell
python telegram_trader_alert_v01.py --mode SCALPING --summary
```

### SYSTEM_ONLY
Envoie uniquement si :

```text
runtime_status.status = WARN ou FAIL
```

```powershell
python telegram_trader_alert_v01.py --mode SYSTEM_ONLY --summary
```

## Test dry-run complet

```powershell
.\TEST_TELEGRAM_TRADER_ALERT_4_MODES_DRY_RUN.bat
```

## Note

Pour tester sans envoyer, ajouter `--dry-run`.
