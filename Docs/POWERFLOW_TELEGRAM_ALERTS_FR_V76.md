# POWERFLOW TELEGRAM ALERTS FR V7.6.4

## Objectif

Telegram sert à réveiller le trader avec un contexte qualifié en français.

Il ne doit pas envoyer :
- un `PAIR_UP` ou `PAIR_DOWN` brut ;
- un `HONEST_UNKNOWN` sans événement utile ;
- du spam à chaque cycle ;
- un ordre automatique.

Il doit envoyer :
- le film du marché ;
- le dernier événement structurel ;
- la lecture qualifiée ;
- la confirmation prix ;
- la propagation ;
- la texture ;
- la visibilité data ;
- les risques techniques ;
- la condition à surveiller ;
- la condition d’invalidation.

## Fichiers

- `patch/pf_telegram_qualified_alert_once.py`
- `patch/pf_trader_labels_fr_once.py`
- `schema/terrain_packet_labels_fr_v76.json`
- `output/dashboard_surface/GBPUSD/terrain_packet.json`
- `output/dashboard_surface/GBPUSD/terrain_packet_fr.txt`

## Configuration locale

Ne jamais committer le token Telegram.

Créer localement :

```json
{
  "bot_token": "TON_BOT_TOKEN",
  "chat_id": "TON_CHAT_ID"
}
```

dans :

```text
config/telegram_alerts.local.json
```

ou définir les variables d’environnement :

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_CHAT_ID="..."
```

## Dry run

```powershell
python patch\pf_telegram_qualified_alert_once.py --dry-run
```

## Envoi réel

```powershell
python patch\pf_telegram_qualified_alert_once.py --send
```

## Forcer un test

```powershell
python patch\pf_telegram_qualified_alert_once.py --send --force
```

## Doctrine corrigée

PowerFlow peut réveiller le trader et proposer un scénario qualifié.

PowerFlow ne doit pas imposer une décision ni exécuter automatiquement.

Le trader reste souverain.

