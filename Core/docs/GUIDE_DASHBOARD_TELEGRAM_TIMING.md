# 🚀 GUIDE RAPIDE — Dashboard Live + Telegram Timing

## ✅ CE QUI A ÉTÉ CRÉÉ

### 1. **Dashboard Live** (`dashboard_live.html`)
Interface web ultra-simple qui affiche :
- État en temps réel de chaque paire (GBPUSD, EURUSD, etc.)
- Timing précis de chaque signal (il y a combien de temps)
- Statut de fraîcheur : ✅ FRAIS / ⚠️ MOYEN / ❌ VIEUX
- Liste des alertes des 15 dernières minutes

### 2. **Serveur Dashboard** (`dashboard_server.py`)
Script Python qui :
- Lit `powerflow.db` toutes les 10 secondes
- Génère le JSON consommé par le dashboard
- Peut tourner en boucle ou servir via HTTP

### 3. **Telegram avec Timing** (`telegram_timing_v6.py`)
Bot Telegram nouvelle génération qui :
- Envoie l'alerte dès qu'un signal naît
- Indique précisément "il y a X secondes/minutes"
- Met à jour automatiquement après 2 min si signal toujours actif
- Notifie quand le signal devient périmé (5 min+)

---

## 🎯 UTILISATION — DASHBOARD

### Option A : Mode Simple (génération JSON uniquement)

```bash
# Générer le JSON une fois
python dashboard_server.py --once

# Puis ouvrir dashboard_live.html dans le navigateur
# (il lira dashboard_data.json)
```

### Option B : Mode Boucle (mise à jour continue)

```bash
# Terminal 1 : Générer le JSON en boucle
python dashboard_server.py --loop

# Terminal 2 : Ouvrir dashboard_live.html
# Il se rafraîchira automatiquement toutes les 10s
```

### Option C : Mode Serveur HTTP (tout-en-un)

```bash
# Lance le serveur + génération automatique
python dashboard_server.py --serve

# Puis ouvrir dans le navigateur :
# http://localhost:8080/dashboard_live.html
```

**💡 ASTUCE** : Laisser le dashboard ouvert sur un 2ème écran pendant que tu trades

---

## 📱 UTILISATION — TELEGRAM

### Configuration initiale

Créer un fichier `.env` avec :

```
TELEGRAM_BOT_TOKEN=ton_token_ici
TELEGRAM_CHAT_ID=ton_chat_id_ici
```

### Test d'envoi

```bash
# Envoyer un signal de test
python telegram_timing_v6.py --test
```

Tu recevras :

```
🔔 GBPUSD M5

GBP pousse
USD plie

⚡ CROSS détecté
⏱️ Il y a 12s

✅ SIGNAL FRAIS - Agir maintenant
```

### Mode automatique (mise à jour continue)

```bash
# Boucle qui check toutes les 60s
python telegram_timing_v6.py --loop
```

Ce mode va :
- Surveiller tous les signaux envoyés
- Envoyer une mise à jour à 2 min si toujours actif
- Notifier à 5 min si périmé

**Exemple de mise à jour automatique :**

```
⚠️ GBPUSD M5

Signal toujours actif
⏱️ Il y a 2min30

⚠️ TIMING MOYEN - Prudence
```

Puis si le signal vieillit encore :

```
❌ GBPUSD M5

⏱️ Il y a 5min15

❌ SIGNAL PÉRIMÉ - Ne plus agir
```

---

## 🔗 INTÉGRATION AVEC LE MOTEUR POWERFLOW

### Dans ton engine.py (ou équivalent)

```python
from telegram_timing_v6 import TelegramTimingBot

# Initialiser le bot
telegram = TelegramTimingBot()

# Quand un signal est détecté
def on_signal_detected(signal_data):
    """
    signal_data doit contenir :
    - symbol : "GBPUSD"
    - timeframe : 5
    - signal_type : "CROSS"
    - dev_strong : "GBP"
    - dev_weak : "USD"
    - created_at : timestamp ISO
    """
    
    # Envoyer immédiatement
    telegram.send_signal_birth(signal_data)
```

### Lancer la boucle de mise à jour en parallèle

```bash
# Terminal 1 : Ton moteur PowerFlow
python engine.py

# Terminal 2 : Mises à jour Telegram
python telegram_timing_v6.py --loop
```

---

## 📊 TIMELINE D'UN SIGNAL

```
T+0s     : Signal détecté → 🔔 FRAIS (envoi immédiat)
T+2min   : ⚠️ MOYEN (mise à jour auto)
T+5min   : ❌ VIEUX (notification expiration)
T+15min  : Suppression de la mémoire
```

---

## 🎨 PERSONNALISATION

### Changer les seuils de fraîcheur

Dans `telegram_timing_v6.py` :

```python
class TelegramTimingBot:
    # Seuils actuels (en minutes)
    FRESH_THRESHOLD = 2      # ← Change ici
    MEDIUM_THRESHOLD = 5     # ← Change ici
    EXPIRED_THRESHOLD = 10   # ← Change ici
```

### Ajouter des paires au dashboard

Dans `dashboard_server.py` :

```python
# Ligne 133
pairs_to_watch = ["GBPUSD", "EURUSD", "USDJPY", "GBPJPY", "EURJPY"]
#                                                          ^^^^^^^^ Ajoute ici
```

---

## ⚡ DÉMARRAGE RAPIDE EN 3 COMMANDES

```bash
# 1. Dashboard en mode serveur
python dashboard_server.py --serve &

# 2. Telegram en mode boucle
python telegram_timing_v6.py --loop &

# 3. Ouvrir le navigateur
open http://localhost:8080/dashboard_live.html
```

**Et voilà — tu as CLARTÉ + TIMING en temps réel !**

---

## 🐛 TROUBLESHOOTING

### Le dashboard affiche "MODE DÉMO"
➜ La DB `powerflow.db` n'est pas trouvée ou vide  
➜ Vérifie le chemin avec `--db /chemin/vers/powerflow.db`

### Telegram ne part pas
➜ Vérifie `.env` avec le bon token et chat_id  
➜ Test avec `python telegram_timing_v6.py --test`

### Les mises à jour ne partent pas
➜ La boucle `--loop` doit tourner en parallèle  
➜ Vérifie que `telegram_alerts_memory.json` existe

---

## 📝 FICHIERS CRÉÉS

```
dashboard_live.html          → Interface web
dashboard_server.py          → Générateur de données
telegram_timing_v6.py        → Bot Telegram avec timing
dashboard_data.json          → Données live (auto-généré)
telegram_alerts_memory.json  → Mémoire des alertes (auto-généré)
```

---

**🎯 OBJECTIF ATTEINT**

✅ **CLARTÉ** : Dashboard qui montre l'essentiel en 1 coup d'œil  
✅ **TIMING** : Tu sais QUAND le signal est né et si tu peux encore agir  

**Plus d'hésitation. Plus de doute. AGIR au bon moment.**
