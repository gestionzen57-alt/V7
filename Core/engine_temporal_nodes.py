"""
PowerFlow V6 — engine_temporal_nodes.py
Module C: Intégration moteur temporal nodes + alertes Telegram
"""

import sqlite3
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Configuration logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ============================================================================
# CONFIGURATION
# ============================================================================

ALERT_THRESHOLDS = {
    "NODE_COMPLET_FULL": {"level": "CRITICAL", "delay_sec": 0},
    "NODE_COMPLET": {"level": "HIGH", "delay_sec": 30},
    "NODE_REPULSION": {"level": "HIGH", "delay_sec": 0},
    "NODE_CROSS": {"level": "MEDIUM", "delay_sec": None},
    "NODE_SIMPLE": {"level": "LOW", "delay_sec": None},
}

# ============================================================================
# DEDUPLICATOR — Éviter spam Telegram
# ============================================================================

class AlertDeduplicator:
    """Tracker des alertes envoyées pour éviter spam."""
    
    def __init__(self, cache_duration_sec: int = 3600):
        self.sent_alerts = {}  # {node_id: timestamp}
        self.cache_duration = cache_duration_sec
    
    def should_send(self, node_id: str) -> bool:
        """Vérifier si alert déjà envoyée récemment."""
        now = time.time()
        last_sent = self.sent_alerts.get(node_id, 0)
        
        if now - last_sent > self.cache_duration:
            self.sent_alerts[node_id] = now
            return True
        
        return False
    
    def mark_sent(self, node_id: str):
        """Marquer comme envoyé."""
        self.sent_alerts[node_id] = time.time()


# ============================================================================
# ALERT PROCESSOR
# ============================================================================

class TemporalNodeAlertProcessor:
    """Traiter les détections de nodes et générer les alertes."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.dedup = AlertDeduplicator()
        self._init_db()
    
    def _init_db(self):
        """Créer table temporal_nodes si elle n'existe pas."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                timeframe INTEGER NOT NULL,
                node_type TEXT NOT NULL,
                interest TEXT NOT NULL,
                score INTEGER,
                duration_minutes REAL,
                window_start TEXT,
                window_end TEXT,
                has_convergence BOOLEAN,
                has_cross BOOLEAN,
                has_kiss_reject BOOLEAN,
                has_repulsion BOOLEAN,
                telegram_sent BOOLEAN DEFAULT 0,
                alert_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_temporal_nodes_symbol 
            ON temporal_nodes(symbol)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_temporal_nodes_node_id 
            ON temporal_nodes(node_id)
        """)
        self.conn.commit()
    
    def process_node_detection(self, symbol: str, nodes_data: Dict) -> Dict:
        """
        Traiter détection de nodes et retourner les alertes à envoyer.
        
        Returns:
            Dict avec:
            - critical_alerts: List[str] — Alertes CRITICAL (envoyer immédiat)
            - high_alerts: List[str] — Alertes HIGH (envoyer après 30sec)
            - total_nodes: int
            - summary: Dict
        """
        
        result = {
            "critical_alerts": [],
            "high_alerts": [],
            "total_nodes": 0,
            "summary": nodes_data.get("summary", {})
        }
        
        if not nodes_data.get("nodes_by_tf"):
            return result
        
        # Collecter tous les nodes
        all_nodes = []
        for tf_label, nodes_list in nodes_data.get("nodes_by_tf", {}).items():
            if isinstance(nodes_list, list):
                all_nodes.extend(nodes_list)
        
        result["total_nodes"] = len(all_nodes)
        
        # Traiter chaque node
        for node in all_nodes:
            node_type = node.get("type", "UNKNOWN")
            node_id = node.get("id", "")
            
            # Check si on doit alerter
            threshold = ALERT_THRESHOLDS.get(node_type, {})
            if not threshold.get("delay_sec"):
                continue  # Pas d'alerte pour ce type
            
            # Check déduplication
            if not self.dedup.should_send(node_id):
                continue  # Déjà envoyée récemment
            
            # Formater message
            alert_msg = self._format_alert_message(symbol, node)
            
            # Classer par niveau
            level = threshold.get("level", "LOW")
            if level == "CRITICAL":
                result["critical_alerts"].append(alert_msg)
            elif level == "HIGH":
                result["high_alerts"].append(alert_msg)
            
            # Stocker en DB
            self._store_node_to_db(symbol, node)
        
        return result
    
    def _format_alert_message(self, symbol: str, node: Dict) -> str:
        """Formater message d'alerte Telegram."""
        
        msg_parts = [
            f"🚨 <b>TEMPORAL NODE</b> — {symbol}",
            f"",
            f"<b>{node.get('type', '?')}</b>",
            f"Score: <b>{node.get('score', 0)}/10</b>",
            f"Window: {node.get('window', '?')}",
            f"TF: {node.get('tf', '?')}",
        ]
        
        if node.get('has_convergence'):
            msg_parts.append("⚠️ CONVERGENCE détectée")
        
        if node.get('has_repulsion'):
            msg_parts.append("↔ REPULSION détectée")
        
        if node.get('has_cross'):
            msg_parts.append("✕ CROSS détecté")
        
        msg_parts.append("")
        msg_parts.append(f"Action: <i>{node.get('action', 'OBSERVE')}</i>")
        
        return "\n".join(msg_parts)
    
    def _store_node_to_db(self, symbol: str, node: Dict):
        """Stocker node en DB pour historique."""
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO temporal_nodes
                (node_id, symbol, timeframe, node_type, interest, score, 
                 duration_minutes, window_start, window_end, 
                 has_convergence, has_cross, has_kiss_reject, has_repulsion, alert_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node.get("id"),
                symbol,
                int(node.get("tf", "1").replace("M", "").replace("H", "").replace("D", "").replace("W", "") or 1),
                node.get("type"),
                node.get("interest"),
                node.get("score"),
                node.get("duration_min"),
                node.get("window", "").split("->")[0] if node.get("window") else None,
                node.get("window", "").split("->")[1] if node.get("window") else None,
                node.get("has_convergence", False),
                node.get("has_cross", False),
                node.get("has_kiss_reject", False),
                node.get("has_repulsion", False),
                ALERT_THRESHOLDS.get(node.get("type", ""), {}).get("level", "LOW")
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error storing node to DB: {e}")
    
    def close(self):
        """Fermer connexion DB."""
        if self.conn:
            self.conn.close()


# ============================================================================
# ENGINE ORCHESTRATION — Intégration au cycle engine.py
# ============================================================================

class TemporalNodeEngine:
    """Orchestrateur pour intégration dans engine.py."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.processor = TemporalNodeAlertProcessor(db_path)
        self.last_update = {}  # {symbol: timestamp}
        self.cache_duration = 10  # sec
    
    def should_update_nodes(self, symbol: str) -> bool:
        """Vérifier si on doit recalculer (cache 10 sec)."""
        now = time.time()
        last = self.last_update.get(symbol, 0)
        
        if now - last > self.cache_duration:
            self.last_update[symbol] = now
            return True
        return False
    
    def run_cycle(self, symbol: str, nodes_data: Dict) -> Dict:
        """
        Exécuter cycle complet pour un symbol.
        
        Returns:
            Dict avec alertes et stats
        """
        
        # Traiter les alertes
        alerts = self.processor.process_node_detection(symbol, nodes_data)
        
        # Logging
        if alerts["critical_alerts"]:
            logger.critical(f"{symbol}: {len(alerts['critical_alerts'])} CRITICAL alerts")
        if alerts["high_alerts"]:
            logger.warning(f"{symbol}: {len(alerts['high_alerts'])} HIGH alerts")
        
        return alerts
    
    def close(self):
        """Cleanup."""
        self.processor.close()


# ============================================================================
# HELPER FUNCTIONS — Pour appels depuis engine.py
# ============================================================================

def process_temporal_nodes_for_engine(
    symbol: str,
    nodes_data: Dict,
    db_path: str,
    send_telegram_callback=None
) -> Dict:
    """
    Fonction wrapper pour appeler depuis engine.py.
    
    Usage:
        from engine_temporal_nodes import process_temporal_nodes_for_engine
        
        alerts = process_temporal_nodes_for_engine(
            symbol="GBPUSD",
            nodes_data=nodes_dict,
            db_path="powerflow.db",
            send_telegram_callback=send_to_telegram  # Optional
        )
        
        if alerts["critical_alerts"]:
            # Envoyer Telegram immédiatement
            pass
        
        if alerts["high_alerts"]:
            # Envoyer Telegram après 30 sec (avec timer)
            pass
    """
    
    engine = TemporalNodeEngine(db_path)
    result = engine.run_cycle(symbol, nodes_data)
    
    # Optionally send Telegram
    if send_telegram_callback:
        for alert_msg in result["critical_alerts"]:
            try:
                send_telegram_callback(alert_msg)
            except Exception as e:
                logger.error(f"Error sending critical alert: {e}")
        
        # High alerts avec délai
        for alert_msg in result["high_alerts"]:
            try:
                # TODO: Implémenter timer 30 sec si needed
                send_telegram_callback(alert_msg)
            except Exception as e:
                logger.error(f"Error sending high alert: {e}")
    
    engine.close()
    return result


# ============================================================================
# INTÉGRATION SIMPLE DANS engine.py — Code à copier
# ============================================================================

"""
EXEMPLE D'UTILISATION DANS engine.py:

================================================================================

from pf_temporal_nodes import get_temporal_nodes_for_engine
from engine_temporal_nodes import process_temporal_nodes_for_engine
from telegram_v6 import send_temporal_node_alert

def engine_main_loop():
    '''Moteur principal.'''
    
    symbols = ["GBPUSD", "EURUSD", "GBPJPY"]
    
    while True:
        for symbol in symbols:
            try:
                # 1. Détecter nodes (cache 10 sec)
                nodes_data = get_temporal_nodes_for_engine(
                    db_path="powerflow.db",
                    symbol=symbol,
                    timeframes=[1, 5, 15, 30, 60],
                    mode="live"
                )
                
                # 2. Traiter alertes
                alerts = process_temporal_nodes_for_engine(
                    symbol=symbol,
                    nodes_data=nodes_data,
                    db_path="powerflow.db",
                    send_telegram_callback=send_temporal_node_alert
                )
                
                # 3. Log result
                if alerts["critical_alerts"]:
                    logger.critical(f"{symbol}: CRITICAL nodes detected!")
                    # Telegram déjà envoyé par callback
                
                if alerts["high_alerts"]:
                    logger.warning(f"{symbol}: HIGH nodes detected")
                    # Telegram déjà envoyé par callback
            
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        time.sleep(1)  # Main cycle delay

================================================================================
"""

if __name__ == "__main__":
    # Test simple
    print("Engine temporal nodes module loaded successfully!")
    print("Import this in your engine.py to use.")
