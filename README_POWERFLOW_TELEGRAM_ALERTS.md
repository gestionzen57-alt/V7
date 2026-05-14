# PowerFlow — Alertes Telegram

Ce README explique comment lancer les alertes Telegram PowerFlow en français.

## Objectif

PowerFlow ne doit pas te rendre esclave du dashboard.

Le cycle Telegram sert à :

```text
legacy_behavioral_state.json
→ terrain_context.json
→ terrain_packet.json
→ terrain_packet_fr.txt
→ alerte Telegram qualifiée
```

Telegram envoie uniquement une lecture utile :

```text
film du marché
dernier événement structurel
lecture qualifiée
qualité du packet
confirmation prix
propagation
texture
visibilité data
risques techniques
condition à surveiller
condition d’invalidation
```

Telegram ne doit pas envoyer :

```text
PAIR_UP / PAIR_DOWN brut
HONEST_UNKNOWN seul
du spam à chaque cycle
un ordre automatique
```

Le trader reste souverain.

---

## Commande quotidienne

Depuis PowerShell :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
.\run_powerflow_v76_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode send
```

Cette commande :

```text
1. lance le scheduler PowerFlow ;
2. lit les sorties legacy ;
3. génère le terrain_packet ;
4. génère le message français ;
5. envoie Telegram si le packet est qualifié.
```

---

## Alerte Telegram sans relancer le scheduler

Si les sorties PowerFlow existent déjà et que tu veux seulement envoyer l’alerte sur le dernier packet :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send
```

---

## Test sans envoyer Telegram

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode dry-run
```

Résultat attendu :

```text
telegram_mode=dry-run
telegram_returncode=0
```

---

## Forcer un test réel Telegram

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send -ForceAlert
```

À utiliser seulement pour vérifier que Telegram fonctionne.

---

## Anti-spam / cooldown

PowerFlow calcule un fingerprint du terrain_packet.

Si le même packet a déjà été envoyé récemment, Telegram répond :

```text
cooldown active for fingerprint ...
```

C’est normal.

Cela veut dire :

```text
le packet est qualifié,
mais PowerFlow ne répète pas la même alerte.
```

Pour forcer un test malgré le cooldown :

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send -ForceAlert
```

---

## Configuration Telegram

PowerFlow lit les identifiants Telegram dans :

```text
config\telegram_alerts.local.json
```

Format :

```json
{
  "bot_token": "TON_BOT_TOKEN",
  "chat_id": "TON_CHAT_ID"
}
```

Ce fichier est ignoré par Git. Ne jamais committer un token.

Si tu as déjà un `.env`, le fichier local peut être généré avec :

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\AutoPilot-V76-TelegramFromEnv.ps1"
```

---

## Vérifier que les secrets ne sont pas trackés

```powershell
git check-ignore -v "config\telegram_alerts.local.json"
git ls-files "Core\.env"
git ls-files "config\telegram_alerts.local.json"
```

Résultat souhaité :

```text
config\telegram_alerts.local.json est ignoré
git ls-files Core\.env ne retourne rien
git ls-files config\telegram_alerts.local.json ne retourne rien
```

---

## Lock scheduler

Si la commande avec `-RunCoreScheduler` affiche :

```text
OVERLAP_SKIP previous lock active
```

cela signifie qu’un lock scheduler existe encore.

Vérifier les processus actifs :

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match "scheduler_powerflow|powerflow_turbo|scheduler_powerflow_turbo_wrapper" } |
  Select-Object ProcessId, CommandLine
```

S’il n’y a aucun processus actif, le lock est stale.

Dans notre cas, le fichier trouvé était :

```text
Core\logs\scheduler_powerflow (1).lock
```

Il peut être déplacé hors du repo pour débloquer le scheduler.

---

## Message Telegram exemple

```text
🔔 PowerFlow — alerte qualifiée

GBPUSD — Rejet de zone haute

Film : Rejet de zone haute
Dernier événement : Rejet de zone haute
Lecture : Signal brut baissier → Déroulement baissier après rejet haut
Qualité : Réaction structurelle
Prix : Prix rejeté en haut
Propagation : Relais petit timeframe vers moyen timeframe
Texture : Détachement de rejet
Data : Lecture partielle
Risques : Décalage temporel événement

Résumé technique : GBPUSD | POST_HIGH_UNWIND | PRICE_REJECTED_HIGH | DATA=READING_PARTIAL
Rappel : alerte de contexte, pas ordre automatique.
```

---

## Commandes utiles

### Usage quotidien

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode send
```

### Alerte seule

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send
```

### Dry-run

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode dry-run
```

### Test forcé

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send -ForceAlert
```
