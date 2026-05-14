# POWERFLOW V7.6.5 — CYCLE TELEGRAM FR

## Objectif

Ce module ajoute une fin de cycle opérationnelle :

```text
legacy_behavioral_state.json
→ terrain_context.json
→ terrain_packet.json
→ terrain_packet_fr.txt
→ Telegram FR qualifié
```

Il ne remplace pas la spine et ne transforme pas PowerFlow en bot d’exécution.

## Fichiers

- `patch/pf_v76_telegram_cycle_once.py`
- `run_powerflow_v76_telegram_cycle.ps1`
- `tests/test_v76_telegram_cycle_once.py`

## Utilisation simple

Dry-run, sans envoyer :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode dry-run
```

Envoi réel normal avec anti-spam :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send
```

Forcer un test :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send -ForceAlert
```

## Avec le scheduler existant

Pour lancer le scheduler puis la couche Telegram :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode send
```

## Règle d’alerte

Telegram n’envoie pas les `HONEST_UNKNOWN` ou les signaux bruts seuls.

Il envoie uniquement les packets qualifiés :
- événement structurel ;
- prix confirmé / rejeté ;
- qualité utile ;
- data visibility visible ;
- anti-spam par fingerprint et cooldown.

