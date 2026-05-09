# LEXIQUE_UPDATE_QUEUE — POWERFLOW V6.1 LIVE CYCLE

À intégrer dans le lexique complet.

---

## Termes à ajouter

```text
LIVE_CYCLE_ORCHESTRATOR
TRADER_ALERT_STATE
TRADER_ALERT_READY
TRADER_ALERT_FRESHNESS
TELEGRAM_TRADER_ALERT
TELEGRAM_MODE_OFF
TELEGRAM_MODE_HOT_ONLY
TELEGRAM_MODE_SCALPING
TELEGRAM_MODE_SYSTEM_ONLY
NO_SEND_TRADER_ALERT_NOT_READY
NO_SEND_RUNTIME_OK
RUNTIME_STATUS
PIPELINE_TRACE
TRADER_SCENE_TRANSLATION
SILENCE_IS_VALID
```

---

## Définitions courtes

### LIVE_CYCLE_ORCHESTRATOR

```text
Commande unique qui rafraîchit la chaîne live PowerFlow :
DB check, dashboard refresh, trader alert, Telegram optionnel, runtime outputs.
```

### TRADER_ALERT_STATE

```text
Traduction trader du film moteur.
Doit être courte, datée, fraîche et exploitable.
```

### TRADER_ALERT_READY

```text
Booléen indiquant qu’une scène trader fraîche mérite transmission.
Si false : Telegram reste silencieux.
```

### TELEGRAM_TRADER_ALERT

```text
Transmission mobile lisant uniquement trader_alert_state.json.
Ne lit pas les labels moteur.
```

### NO_SEND_TRADER_ALERT_NOT_READY

```text
Verdict Telegram indiquant que le script fonctionne mais qu’aucune scène trader fraîche n’est active.
```

### SILENCE_IS_VALID

```text
État normal où PowerFlow choisit de ne pas alerter car rien de frais n’est exploitable.
```

---

## Règles de non-confusion

```text
Behavioral HOT ≠ Trader Alert Ready
Trader Alert Ready false ≠ bug
Telegram silence ≠ panne
Dashboard event ≠ Telegram alert
```

---

## Phrase noyau

```text
PowerFlow V6.1 traduit le moteur en scène trader et se tait quand rien n’est frais.
```
