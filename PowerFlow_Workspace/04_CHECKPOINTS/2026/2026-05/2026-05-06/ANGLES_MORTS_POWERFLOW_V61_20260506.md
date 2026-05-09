# ANGLES MORTS POSSIBLES — POWERFLOW V6.1

---

## 1. Freshness réelle vs freshness affichée

Risque :

```text
Une alerte peut être techniquement présente mais trop vieille pour être utile.
```

Mitigation :

```text
Trader Alert State doit toujours afficher age_seconds / freshness.
Telegram doit rester silencieux si trader_alert_ready=false.
```

---

## 2. Queue fraîche / cockpit vieux

Risque :

```text
behavioral_alert_queue.json est régénéré mais cockpit_agentic_state_v01.json ne l’absorbe pas.
```

Mitigation actuelle :

```text
--refresh-cockpit-from-queue
```

À vérifier dans Health Check.

---

## 3. Dashboard double writer

Risque :

```text
Deux serveurs ou scripts écrivent dashboard_data.json.
```

Symptôme :

```text
Behavioral Flow alterne visible / absent.
```

Mitigation :

```text
Health Check + netstat + un seul dashboard_server.
```

---

## 4. Telegram spam / duplicate

Risque :

```text
Même scène renvoyée trop souvent.
```

Mitigation actuelle :

```text
telegram_trader_alert_last.json
cooldown anti-spam
trader_alert_ready=false → silence
```

À renforcer avant boucle.

---

## 5. Jargon moteur dans Telegram

Risque :

```text
Telegram envoie FIRST_DETACHMENT_WITH_CLEAN_RELAY au lieu d’une phrase trader.
```

Mitigation :

```text
Telegram lit trader_alert_state.json uniquement.
```

---

## 6. Core trop rempli

Risque :

```text
Les fichiers actifs se mélangent aux backups et patchs.
```

Mitigation :

```text
POWERFLOW_MODULE_REGISTRY.json
pf_core_audit.py
```

---

## 7. Recent-minutes non propagé réellement

Risque :

```text
--recent-minutes est tracé mais ne contrôle pas encore toute la fenêtre upstream.
```

Mitigation :

```text
P2.3 futur : propagation fenêtre temporelle propre.
```

Non bloquant pour V6.1 actuel.

---

## 8. Trader Alert trop strict

Risque :

```text
trader_alert_ready=false trop souvent, Telegram silencieux alors que le dashboard contient une scène moteur HOT.
```

Lecture :

```text
Ce n’est pas forcément un bug.
Cela peut vouloir dire que la scène est trop vieille ou non traduite en scène trader fraîche.
```

À affiner :

```text
tests live pendant marché actif
seuil freshness
règles de groupement
```

---

## 9. Confondre HOT moteur et HOT trader

Risque :

```text
top_alert HOT dans Behavioral Flow mais trader_alert_ready=false.
```

Interprétation correcte :

```text
HOT moteur peut exister.
HOT trader exige fraîcheur + traduction + filtre.
```

---

## 10. Automatiser trop vite la boucle

Risque :

```text
Une boucle 30s sans contrôle de santé peut créer bruit / confusion.
```

Mitigation :

```text
Boucle seulement après Runtime Health Check renforcé.
```

---

## Phrase noyau

```text
Un système live utile doit savoir se taire, signaler ses failles,
et ne pas confondre événement moteur avec alerte trader.
```
