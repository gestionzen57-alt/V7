# PowerFlow — Alertes Telegram FR

Ce README explique comment lancer les alertes Telegram PowerFlow en français trader.

## Objectif

PowerFlow ne doit pas rendre le trader esclave du dashboard.
Le cycle Telegram sert à transmettre une lecture qualifiée et lisible :

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

Les enums internes restent en anglais dans `terrain_packet.json`.
La traduction FR se fait uniquement à l’affichage via :

```text
schema/terrain_packet_labels_fr_v76.json
patch/pf_trader_labels_fr_once.py
```

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

## Alerte Telegram sans relancer le scheduler

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send
```

## Test sans envoyer Telegram

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode dry-run
```

Résultat attendu :

```text
telegram_mode=dry-run
telegram_returncode=0
```

## Forcer un test réel Telegram

```powershell
.\run_powerflow_v76_telegram_cycle.ps1 -TelegramMode send -ForceAlert
```

À utiliser seulement pour vérifier la transmission Telegram.

## Anti-spam / cooldown

PowerFlow calcule un fingerprint du `terrain_packet`.
Si le même packet a déjà été envoyé récemment, Telegram répond :

```text
cooldown active for fingerprint ...
```

Cela signifie que le packet est qualifié, mais que PowerFlow ne répète pas la même alerte.

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

## Nettoyage FR des conditions

Depuis ce patch, `watch_condition` et `invalidation_condition` sont traduits avant affichage Telegram.

Exemples :

```text
vraie acceptation prix, pas extension tardive
→ À surveiller : vraie acceptation prix, pas extension tardive.

rejet haut confirmé ou déroulement inverse
→ Invalidation : rejet haut confirmé ou déroulement inverse.
```

Si une valeur inconnue apparaît, le formatter n’affiche pas l’enum brute.
Il produit une phrase propre :

```text
WATCH_FOR_PULLBACK_CONFIRMATION
→ À surveiller : condition à surveiller non traduite : pullback confirmation.

INVALIDATION_PRICE_REENTERS_OLD_ZONE
→ Invalidation : condition d'invalidation non traduite : price reenters old zone.
```

## Message Telegram exemple

```text
PowerFlow — alerte qualifiée

GBPUSD — Rejet de zone haute

Film : Rejet de zone haute
Dernier événement : Rejet de zone haute
Zone : 1.34840-1.34977 / Rejet de zone haute
Rôle du mouvement : Déroulement baissier après rejet haut
Lecture : Signal brut baissier → Déroulement baissier après rejet haut
Qualité : Réaction structurelle
Prix : Prix rejeté en haut
Propagation : Relais petit timeframe vers moyen timeframe
Texture : Détachement de rejet
Data : Lecture partielle
Risques : Décalage temporel événement
À surveiller : vraie acceptation prix, pas extension tardive.
Invalidation : rejet haut confirmé ou déroulement inverse.

Résumé technique : GBPUSD | POST_HIGH_UNWIND | PRICE_REJECTED_HIGH | DATA=READING_PARTIAL
Nature : alerte de contexte PowerFlow.
```

## Tests

```powershell
python -m unittest tests/test_trader_labels_fr_v76.py
```

Ou :

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

