#!/usr/bin/env python3
"""
Telegram V6 - Alertes avec Timing Précis

Système d'alertes Telegram qui affiche clairement :
- QUAND le signal est né
- SI le trader peut encore agir (FRAIS / MOYEN / VIEUX)
- Mise à jour automatique du statut

Modes :
- SIGNAL_BIRTH : alerte immédiate dès détection
- SIGNAL_UPDATE : mise à jour 2min après si toujours actif
- SIGNAL_EXPIRED : notification si signal périmé (5min+)
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests


@dataclass
class SignalAlert:
    """Représentation d'une alerte signal"""
    signal_id: str
    symbol: str
    timeframe: str
    signal_type: str
    dev_strong: str
    dev_weak: str
    timestamp: str
    freshness: str  # FRAIS / MOYEN / VIEUX
    sent_at: Optional[str] = None
    last_update_at: Optional[str] = None


class TelegramTimingBot:
    """Bot Telegram avec gestion précise du timing"""
    
    # Seuils de fraîcheur (en minutes)
    FRESH_THRESHOLD = 2
    MEDIUM_THRESHOLD = 5
    EXPIRED_THRESHOLD = 10
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID requis")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        # Fichier de mémoire des alertes envoyées
        self.memory_file = Path("telegram_alerts_memory.json")
        self.sent_alerts: Dict[str, SignalAlert] = self._load_memory()
    
    def _load_memory(self) -> Dict[str, SignalAlert]:
        """Charge la mémoire des alertes envoyées"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    return {
                        k: SignalAlert(**v) for k, v in data.items()
                    }
            except:
                return {}
        return {}
    
    def _save_memory(self):
        """Sauvegarde la mémoire"""
        data = {k: asdict(v) for k, v in self.sent_alerts.items()}
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_time_ago(self, timestamp_str: str) -> tuple[int, str]:
        """
        Calcule le temps écoulé depuis un timestamp
        Returns: (minutes_écoulées, texte_formaté)
        """
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - timestamp
        
        total_seconds = int(delta.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes == 0:
            text = f"{seconds}s"
        elif minutes < 60:
            text = f"{minutes}min"
            if seconds > 0:
                text += f" {seconds}s"
        else:
            hours = minutes // 60
            mins = minutes % 60
            text = f"{hours}h{mins}min"
        
        return minutes, text
    
    def _get_freshness(self, minutes_ago: int) -> str:
        """Détermine la fraîcheur du signal"""
        if minutes_ago < self.FRESH_THRESHOLD:
            return "FRAIS"
        elif minutes_ago < self.MEDIUM_THRESHOLD:
            return "MOYEN"
        else:
            return "VIEUX"
    
    def _format_birth_message(self, alert: SignalAlert, time_ago_text: str) -> str:
        """Formate le message de naissance du signal"""
        
        emoji = "🔔"
        if alert.signal_type == "CROSS":
            emoji = "⚡"
        elif alert.signal_type == "KISS_REJECT":
            emoji = "💋"
        elif alert.signal_type == "COMPRESSION_BREAK":
            emoji = "💥"
        
        msg = f"{emoji} <b>{alert.symbol} {alert.timeframe}</b>\n\n"
        
        # Détail du mouvement
        msg += f"<b>{alert.dev_strong}</b> pousse\n"
        msg += f"<b>{alert.dev_weak}</b> plie\n\n"
        
        # Type de signal
        msg += f"⚡ <b>{alert.signal_type}</b> détecté\n"
        
        # Timing
        msg += f"⏱️ Il y a <b>{time_ago_text}</b>\n\n"
        
        # Statut
        msg += f"✅ <b>SIGNAL FRAIS - Agir maintenant</b>"
        
        return msg
    
    def _format_update_message(self, alert: SignalAlert, 
                               minutes_ago: int, time_ago_text: str) -> str:
        """Formate le message de mise à jour"""
        
        freshness = self._get_freshness(minutes_ago)
        
        if freshness == "MOYEN":
            emoji = "⚠️"
            status = "⚠️ <b>TIMING MOYEN - Prudence</b>"
        else:
            emoji = "❌"
            status = "❌ <b>SIGNAL PÉRIMÉ - Ne plus agir</b>"
        
        msg = f"{emoji} <b>{alert.symbol} {alert.timeframe}</b>\n\n"
        msg += f"Signal toujours actif\n"
        msg += f"⏱️ Il y a <b>{time_ago_text}</b>\n\n"
        msg += status
        
        return msg
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Envoie un message Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Message Telegram envoyé")
                return True
            else:
                print(f"❌ Erreur Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception Telegram: {e}")
            return False
    
    def send_signal_birth(self, signal: Dict) -> bool:
        """
        Envoie l'alerte de naissance d'un signal
        
        Args:
            signal: Dict contenant symbol, timeframe, signal_type, dev_strong, dev_weak, created_at
        """
        
        # Créer l'objet SignalAlert
        alert = SignalAlert(
            signal_id=f"{signal['symbol']}_{signal['timeframe']}_{signal['created_at']}",
            symbol=signal['symbol'],
            timeframe=f"M{signal['timeframe']}",
            signal_type=signal['signal_type'],
            dev_strong=signal.get('dev_strong', '?'),
            dev_weak=signal.get('dev_weak', '?'),
            timestamp=signal['created_at'],
            freshness="FRAIS",
            sent_at=datetime.now().isoformat()
        )
        
        # Calculer le temps écoulé
        minutes_ago, time_ago_text = self._get_time_ago(alert.timestamp)
        
        # Formater le message
        message = self._format_birth_message(alert, time_ago_text)
        
        # Envoyer
        success = self.send_message(message)
        
        if success:
            # Mémoriser l'alerte
            self.sent_alerts[alert.signal_id] = alert
            self._save_memory()
        
        return success
    
    def send_signal_update(self, signal_id: str) -> bool:
        """Envoie une mise à jour pour un signal déjà envoyé"""
        
        if signal_id not in self.sent_alerts:
            print(f"⚠️  Signal {signal_id} non trouvé dans la mémoire")
            return False
        
        alert = self.sent_alerts[signal_id]
        
        # Calculer le temps écoulé
        minutes_ago, time_ago_text = self._get_time_ago(alert.timestamp)
        
        # Vérifier si mise à jour nécessaire
        if minutes_ago < self.FRESH_THRESHOLD:
            print(f"ℹ️  Signal encore FRAIS, pas de mise à jour")
            return False
        
        # Formater le message
        message = self._format_update_message(alert, minutes_ago, time_ago_text)
        
        # Envoyer
        success = self.send_message(message)
        
        if success:
            alert.last_update_at = datetime.now().isoformat()
            alert.freshness = self._get_freshness(minutes_ago)
            self._save_memory()
        
        return success
    
    def check_and_update_all(self):
        """
        Vérifie tous les signaux en mémoire et envoie des mises à jour si nécessaire
        
        Règles :
        - 2 min après envoi → alerte MOYEN si pas déjà fait
        - 5 min après envoi → alerte VIEUX si pas déjà fait
        """
        
        now = datetime.now()
        
        for signal_id, alert in list(self.sent_alerts.items()):
            
            # Temps depuis l'envoi initial
            sent_at = datetime.fromisoformat(alert.sent_at)
            minutes_since_sent = (now - sent_at).total_seconds() / 60
            
            # Temps depuis le signal
            minutes_ago, _ = self._get_time_ago(alert.timestamp)
            new_freshness = self._get_freshness(minutes_ago)
            
            # Si la fraîcheur a changé et qu'on n'a pas encore mis à jour
            if new_freshness != alert.freshness:
                
                # Envoyer mise à jour seulement pour MOYEN ou VIEUX
                if new_freshness in ["MOYEN", "VIEUX"]:
                    print(f"📢 Mise à jour {signal_id}: {alert.freshness} → {new_freshness}")
                    self.send_signal_update(signal_id)
            
            # Nettoyer les vieux signaux (> 15 min)
            if minutes_ago > 15:
                print(f"🗑️  Suppression {signal_id} (trop vieux)")
                del self.sent_alerts[signal_id]
                self._save_memory()
    
    def clean_old_alerts(self, max_age_minutes: int = 30):
        """Nettoie les alertes trop vieilles de la mémoire"""
        now = datetime.now()
        to_delete = []
        
        for signal_id, alert in self.sent_alerts.items():
            minutes_ago, _ = self._get_time_ago(alert.timestamp)
            if minutes_ago > max_age_minutes:
                to_delete.append(signal_id)
        
        for signal_id in to_delete:
            del self.sent_alerts[signal_id]
        
        if to_delete:
            self._save_memory()
            print(f"🗑️  {len(to_delete)} alertes nettoyées")


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def send_quick_alert(symbol: str, timeframe: int, signal_type: str,
                     dev_strong: str, dev_weak: str):
    """
    Fonction rapide pour envoyer une alerte
    
    Usage:
        send_quick_alert("GBPUSD", 5, "CROSS", "GBP", "USD")
    """
    bot = TelegramTimingBot()
    
    signal = {
        'symbol': symbol,
        'timeframe': timeframe,
        'signal_type': signal_type,
        'dev_strong': dev_strong,
        'dev_weak': dev_weak,
        'created_at': datetime.now().isoformat()
    }
    
    return bot.send_signal_birth(signal)


def run_update_loop(interval_seconds: int = 60):
    """
    Boucle de mise à jour automatique
    
    Usage:
        run_update_loop(60)  # Check toutes les minutes
    """
    bot = TelegramTimingBot()
    
    print(f"🔄 Boucle de mise à jour démarrée (interval: {interval_seconds}s)")
    print("Ctrl+C pour arrêter")
    
    try:
        while True:
            bot.check_and_update_all()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt de la boucle")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram V6 - Timing Bot")
    parser.add_argument('--test', action='store_true',
                       help='Envoyer un message de test')
    parser.add_argument('--loop', action='store_true',
                       help='Boucle de mise à jour auto')
    parser.add_argument('--interval', type=int, default=60,
                       help='Interval de check (secondes)')
    
    args = parser.parse_args()
    
    if args.test:
        print("📤 Envoi d'un signal de test...")
        send_quick_alert("GBPUSD", 5, "CROSS", "GBP", "USD")
    
    elif args.loop:
        run_update_loop(args.interval)
    
    else:
        parser.print_help()
