# PowerFlow V7.6.7 - Telegram Reality Board prioritaire

## Objectif

Faire de Telegram une lecture terrain exploitable, alignée avec le Reality Board.

Avant ce patch, le cycle affichait surtout l’alerte qualifiée V7.6 longue, utile en calibration mais trop technique côté trader.

Après ce patch :

- le cycle historique `run_powerflow_v76_telegram_cycle.ps1` reste disponible ;
- le nouveau wrapper `run_powerflow_v767_reality_telegram_cycle.ps1` lance le cycle V7.6 en `dry-run/debug` ;
- puis il envoie ou affiche le message `Réalité marché` court issu du Reality Board.

## Commandes

Dry-run :

```powershell
.\run_powerflow_v767_reality_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode dry-run
```

Live :

```powershell
.\run_powerflow_v767_reality_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode live
```

Live forcé malgré déduplication :

```powershell
.\run_powerflow_v767_reality_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode live -Force
```

## Variables Telegram live

Le script lit au choix :

- `POWERFLOW_TELEGRAM_BOT_TOKEN`
- `POWERFLOW_TELEGRAM_CHAT_ID`

ou :

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Il peut aussi lire `.env`, `telegram.env`, `config/telegram.env`, `telegram_config.json`, `config/telegram.json`.

## Doctrine

Telegram ne doit pas noyer le trader dans les enums.

Message cible :

```text
GBPUSD - Réalité marché

Lecture : ...
HTF - Analyse : ...
MTF - Plan : ...
LTF - Action : ...
B6 : ...
Session : ...
Alternative : ...
Piège : ...
Data : ...
Rappel : lecture terrain, décision trader.
```

Les enums restent disponibles dans les JSON pour debug, mais Telegram parle trader.

## Correctifs V2

- Sortie console Python forcée en UTF-8 pour éviter les erreurs `UnicodeEncodeError` Windows cp1252 sur les accents et flèches.
- Wrapper PowerShell corrigé : appel du cycle legacy via hashtable splatting, afin que `-RunCoreScheduler` reste un switch et ne soit jamais interprété comme `RepoPath`.
