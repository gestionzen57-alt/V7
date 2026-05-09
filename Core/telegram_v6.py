"""
PowerFlow V6 — telegram_v6.py
Module d'alertes Telegram simple et robuste
"""

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

TELEGRAM_TOKEN = os.getenv("8656365767:AAHRsPA4DgFvsIUFqB9M7Df9rJmKelWpwNk", "")
TELEGRAM_CHAT_ID = os.getenv("1401055223", "")

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def send_temporal_node_alert(message: str, token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """
    Envoyer alerte Telegram pour un Temporal Node.
    
    Args:
        message: Message texte (HTML allowed)
        token: Token Telegram (default: env TELEGRAM_TOKEN)
        chat_id: Chat ID Telegram (default: env TELEGRAM_CHAT_ID)
    
    Returns:
        True si succès, False si erreur
    
    Usage:
        from telegram_v6 import send_temporal_node_alert
        
        msg = "🚨 NODE_COMPLET_FULL détecté!\n..."
        send_temporal_node_alert(msg)
    """
    
    if not token:
        token = TELEGRAM_TOKEN
    if not chat_id:
        chat_id = TELEGRAM_CHAT_ID
    
    if not token or not chat_id:
        logger.warning("Telegram not configured (TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing)")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info("Telegram alert sent successfully")
        return True
    
    except requests.RequestException as e:
        logger.error(f"Telegram send error: {e}")
        return False


def send_telegram_safe(message: str, max_retries: int = 3) -> bool:
    """
    Envoyer avec retry logic.
    
    Args:
        message: Message à envoyer
        max_retries: Nombre de tentatives
    
    Returns:
        True si succès
    """
    
    for attempt in range(max_retries):
        try:
            if send_temporal_node_alert(message):
                return True
        except Exception as e:
            logger.warning(f"Retry {attempt+1}/{max_retries}: {e}")
    
    logger.error(f"Failed to send Telegram after {max_retries} retries")
    return False


def format_critical_alert(symbol: str, node_type: str, score: int, window: str) -> str:
    """
    Formater alerte CRITICAL.
    
    Returns:
        Message formaté HTML
    """
    
    emoji_map = {
        "NODE_COMPLET_FULL": "⚡⚡",
        "NODE_COMPLET": "⚡",
        "NODE_REPULSION": "↔",
        "NODE_CROSS": "✕",
        "NODE_SIMPLE": "·"
    }
    
    emoji = emoji_map.get(node_type, "!")
    
    msg = f"""🚨 <b>CRITICAL ALERT</b> — {symbol}

{emoji} <b>{node_type}</b>
Score: <i>{score}/10</i>
Window: <i>{window}</i>

<b>ACTION REQUIRED:</b>
Check direction of break
Monitor entry points
"""
    
    return msg


def test_telegram_connection() -> bool:
    """
    Tester la connexion Telegram.
    
    Returns:
        True si connecté, False sinon
    """
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured")
        return False
    
    msg = "🔧 <b>PowerFlow V6</b> — Test message"
    return send_temporal_node_alert(msg)


# ============================================================================
# BATCH SENDING
# ============================================================================

class TelegramBatch:
    """Envoyer plusieurs alertes en batch (utile pour traiter 10+ nodes)."""
    
    def __init__(self, batch_size: int = 5):
        self.messages = []
        self.batch_size = batch_size
    
    def add(self, message: str):
        """Ajouter message au batch."""
        self.messages.append(message)
        
        if len(self.messages) >= self.batch_size:
            self.flush()
    
    def flush(self):
        """Envoyer tous les messages en attente."""
        for msg in self.messages:
            send_temporal_node_alert(msg)
        
        self.messages.clear()


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    # Test simple
    print("Testing Telegram connection...")
    
    if test_telegram_connection():
        print("✅ Telegram connected!")
    else:
        print("❌ Telegram not configured")
        print("   Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID env vars")
    
    # Exemple d'alerte
    example_msg = format_critical_alert(
        symbol="GBPUSD",
        node_type="NODE_COMPLET_FULL",
        score=10,
        window="13:36->13:56"
    )
    
    print("\nExample alert:")
    print(example_msg)
