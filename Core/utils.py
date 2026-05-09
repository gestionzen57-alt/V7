# ============================================================
#  PowerFlow V3 — utils.py
#  Fonctions utilitaires partagées
# ============================================================

from datetime import datetime


# ------------------------------------------------------------
#  SESSION DE TRADING
# ------------------------------------------------------------
def get_session(hour: int) -> str:
    """
    Retourne la session active selon l'heure UTC.
    Adapte selon ton fuseau si nécessaire.
    """
    if 22 <= hour or hour < 7:
        return "ASIE"
    elif 7 <= hour < 9:
        return "PRE_LONDON"
    elif 9 <= hour < 12:
        return "LONDON"
    elif 12 <= hour < 13:
        return "OVERLAP_LUNCH"
    elif 13 <= hour < 17:
        return "NEW_YORK"
    elif 17 <= hour < 22:
        return "LONDON_CLOSE"
    return "HORS_SESSION"


# ------------------------------------------------------------
#  TF LABEL
# ------------------------------------------------------------
TF_LABELS = {
    1:"M1", 5:"M5", 15:"M15",
    30:"M30", 60:"H1", 240:"H4"
}

def tf_label(tf: int) -> str:
    return TF_LABELS.get(tf, f"M{tf}")


# ------------------------------------------------------------
#  TIMESTAMP LISIBLE
# ------------------------------------------------------------
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")
