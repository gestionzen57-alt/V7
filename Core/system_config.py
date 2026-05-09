# ============================================================
# PowerFlow V5 — config.py
# UNE SEULE VÉRITÉ : tous les paramètres ici
# Seuils dynamiques par TF — ZERO seuil dans les EA
# ============================================================

# --- TELEGRAM ---
TELEGRAM_TOKEN   = "8656365767:AAHRsPA4DgFvsIUFqB9M7Df9rJmKelWpwNk"
TELEGRAM_CHAT_ID = "1401055223"

# --- SERVEUR TCP (réception depuis MT4) ---
TCP_HOST = "127.0.0.1"
TCP_PORT = 55555

# --- PAIRES ACTIVES (utilisées par engine pour filtrage) ---
PAIRS = [
    "GBPUSD", "GBPJPY", "EURUSD",
    "USDJPY", "EURGBP", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD",
]

# --- DEVISES ACTIVES ---
CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD", "NZD"]

# --- TIMEFRAMES ACTIFS (en minutes) ---
TIMEFRAMES = [1, 5, 15, 30, 60, 240]

# ============================================================
# SEUILS DYNAMIQUES PAR TF
# Anciennement dans l'EA — maintenant gérés ici par engine.py
# ============================================================

# --- NIVEAUX EXTRÊMES (Lock / Dominance) ---
# Au-dessus de LEVEL_HIGH → devise forte / dominante (LOCK)
# En dessous de LEVEL_LOW  → devise faible
LEVEL_HIGH = {
    1:   72.0,   # M1  : réactif, seuil plus bas
    5:   72.0,   # M5
    15:  73.0,   # M15
    30:  74.0,   # M30
    60:  75.0,   # H1
    240: 78.0,   # H4  : signaux rares mais forts
}
LEVEL_LOW = {
    1:   28.0,
    5:   28.0,
    15:  27.0,
    30:  26.0,
    60:  25.0,
    240: 22.0,
}

# Helpers pour récupérer les seuils avec fallback
def get_level_high(tf: int) -> float:
    return LEVEL_HIGH.get(tf, 75.0)

def get_level_low(tf: int) -> float:
    return LEVEL_LOW.get(tf, 25.0)

# --- KISS REJECT (frôlement + rejet de niveau) ---
# Frolement : distance mini pour qualifier un "toucher" de niveau
# Force_Rejet : delta mini du rebond pour valider le rejet
KISS_FROLEMENT = {
    1:   4.0,
    5:   5.0,
    15:  6.0,
    30:  7.0,
    60:  8.0,
    240: 10.0,
}
KISS_FORCE_REJET = {
    1:   7.0,
    5:   8.0,
    15:  10.0,
    30:  11.0,
    60:  12.0,
    240: 14.0,
}

def get_kiss_frolement(tf: int) -> float:
    return KISS_FROLEMENT.get(tf, 6.0)

def get_kiss_force_rejet(tf: int) -> float:
    return KISS_FORCE_REJET.get(tf, 10.0)

# --- FAKEOUT ---
FAKEOUT_DELAY_SEC = {
    1:   300,    # M1  : 5 min
    5:   600,    # M5  : 10 min
    15:  1200,   # M15 : 20 min
    30:  1800,   # M30 : 30 min
    60:  3600,   # H1  : 1h
    240: 7200,   # H4  : 2h
}
FAKEOUT_MIN_GAP = {
    1:   1.5,
    5:   2.0,
    15:  3.0,
    30:  3.5,
    60:  4.0,
    240: 5.0,
}

def get_fakeout_delay(tf: int) -> int:
    return FAKEOUT_DELAY_SEC.get(tf, 1200)

def get_fakeout_gap(tf: int) -> float:
    return FAKEOUT_MIN_GAP.get(tf, 3.0)

# --- CROISEMENT ---
MARGE_CROISEMENT = {
    1:   0.5,
    5:   1.0,
    15:  1.0,
    30:  1.5,
    60:  1.5,
    240: 2.0,
}

def get_marge_croisement(tf: int) -> float:
    return MARGE_CROISEMENT.get(tf, 1.0)

# ============================================================
# COMPRESSION / LIBERATION (detect_nodes)
# ============================================================
COMPRESSION_THRESHOLD = {
    1:   5.0,
    5:   8.0,
    15:  13.0,
    30:  15.0,
    60:  18.0,
    240: 22.0,
}
COMPRESSION_MIN_BARS = {
    1:   5,
    5:   3,
    15:  3,
    30:  3,
    60:  3,
    240: 2,
}
LIBERATION_THRESHOLD = {
    1:   8.0,
    5:   10.0,
    15:  15.0,
    30:  18.0,
    60:  20.0,
    240: 25.0,
}
LIBERATION_MAX_BARS = 40
PENTE_THRESHOLD     = 3.0
CROSS_MIN_DELTA     = 3.0

# Lock
LOCK_DOMINANT_MIN = {tf: get_level_high(tf) for tf in [1,5,15,30,60,240]}
LOCK_OTHERS_MAX   = {
    1:   58.0,
    5:   58.0,
    15:  60.0,
    30:  60.0,
    60:  62.0,
    240: 65.0,
}
LOCK_MIN_BARS = 3

# ============================================================
# ANTI-SPAM / ALERTES
# ============================================================
ANTISPAM_SECONDS = 300
MAX_SPREAD       = 25

ALERT_CROSS_BASIC         = True
ALERT_SUPER_SWITCH        = True
ALERT_FAKEOUT             = True
ALERT_KISS_REJECT         = True
ALERT_SNIPER_REVERSAL     = True
ALERT_CONVERGENCE         = True
ALERT_SLINGSHOT           = True
ALERT_PULLBACK_M1         = True
ALERT_EXTREME_LEVELS      = True
ALERT_MUR_INSTIT          = False
ALERT_COMPRESSION         = True
ALERT_COMPRESSION_SQUEEZE = True

# ============================================================
# DATABASE & SNAPSHOTS
# ============================================================
DB_PATH                   = "powerflow.db"
FORCE_SNAPSHOTS_ENABLED   = True

# Interval minimum entre 2 snapshots pour la même bougie
# V5 : géré par bar_time (anti-doublon par bougie fermée)
FORCE_SNAPSHOTS_INTERVAL_SEC = 0  # désactivé — logique bar_time dans bridge.py

# ============================================================
# HTF / VOLUME / GRAPH
# ============================================================
HTF_RADAR_ENABLED    = True
VOLUME_FILTER_ENABLED = True
VOLUME_SPIKE_RATIO    = 2.5
VOLUME_SPIKE_MIN_TICKS = 15

GRAPH_ENABLED      = True
GRAPH_PREMIUM_ONLY = False
GRAPH_HISTORY_LEN  = 60

# ============================================================
# DEBUG
# ============================================================
DEBUG_CROSS       = False
DEBUG_CONVERGENCE = False
DB_CONTEXT_ENABLED = False
