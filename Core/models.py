# ============================================================
#  PowerFlow V3 — models.py
#  Structure unique de données — circule dans tout le système
# ============================================================

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ------------------------------------------------------------
#  TICK — ce que MT4 envoie à chaque mise à jour
# ------------------------------------------------------------
@dataclass
class Tick:
    symbol:     str
    timeframe:  int          # en minutes : 1, 5, 15, 30, 60, 240
    timestamp:  datetime

    # Devises du buffer Fatman (ex: pour GBPUSD → gbp + usd)
    dev_a:      str          # "gbp"
    dev_b:      str          # "usd"
    val_a:      float        # force de dev_a   (0.0 → 100.0)
    val_b:      float        # force de dev_b   (0.0 → 100.0)

    # Prix & spread
    bid:        float
    spread:     float        # en points
    volume:     int          # tick volume brut

    # ATR estimé (optionnel, si l'indicateur l'envoie)
    atr:        float = 0.0

    # Sensibilité Kiss Reject — réglable par TF depuis l'EA (inputs MT4)
    # Valeurs par défaut appliquées si l'EA n'envoie pas ces champs
    #   M1  → 3.0 / 6.0   (marché agité, plus réactif)
    #   M5  → 5.0 / 8.0   (défaut)
    #   M15 → 6.0 / 10.0
    #   H1+ → 8.0 / 12.0
    kiss_frolement:   float = 5.0   # écart max pour détecter un frôlement
    kiss_force_rejet: float = 8.0   # accélération min pour valider le rejet

    # --- helpers ---
    @property
    def strong(self) -> str:
        """Devise dominante sur ce tick."""
        return self.dev_a if self.val_a >= self.val_b else self.dev_b

    @property
    def weak(self) -> str:
        """Devise faible sur ce tick."""
        return self.dev_b if self.val_a >= self.val_b else self.dev_a

    @property
    def val_strong(self) -> float:
        return self.val_a if self.val_a >= self.val_b else self.val_b

    @property
    def val_weak(self) -> float:
        return self.val_b if self.val_a >= self.val_b else self.val_a

    @property
    def gap(self) -> float:
        """Écart entre les deux devises."""
        return abs(self.val_a - self.val_b)

    @property
    def tf_label(self) -> str:
        labels = {1:"M1", 5:"M5", 15:"M15", 30:"M30", 60:"H1", 240:"H4"}
        return labels.get(self.timeframe, f"M{self.timeframe}")


# ------------------------------------------------------------
#  HTF CONTEXT — résultat du radar des TF supérieurs
# ------------------------------------------------------------
@dataclass
class HTFContext:
    bias:          str        # "GBP", "USD", "NEUTRAL"
    bias_state:    str        # "VALIDE", "CONTRE", "MIXTE"
    aligned_count: int        # nb de TF supérieurs alignés (0→4)
    htf_bonus:     int        # bonus de score (0, 1, 2, 3)
    leader:        str        # TF qui donne le ton ("H4", "H1"…)
    fractal_rank:  int        # qualité globale du biais (0→5)
    scenario:      str        # "TENDANCE", "RANGE", "RETOURNEMENT"
    details:       list       # ex: ["H1 ✅", "H4 ✅", "M30 ❌"]


# ------------------------------------------------------------
#  SIGNAL — ce que le moteur produit après analyse
# ------------------------------------------------------------
@dataclass
class Signal:
    # Identité
    symbol:       str
    timeframe:    int
    signal_type:  str         # "CROSS", "SUPER_SWITCH", "FAKEOUT"…
    timestamp:    datetime

    # Devises concernées
    dev_strong:   str
    dev_weak:     str

    # Scoring
    score:        int         # score total calculé
    level:        str         # "PREMIUM", "CONFIRM", "STANDARD"

    # Contexte
    htf:          Optional[HTFContext] = None
    volume_badge: str = ""    # "💰 SMART MONEY" ou ""
    note:         str = ""    # détail lisible pour Telegram

    # Flags
    spread_ok:    bool = True
    is_pullback:  bool = False
    convergence:  Optional[dict] = None  # données convergence double

    @property
    def is_premium(self) -> bool:
        return self.level == "PREMIUM"

    @property
    def tf_label(self) -> str:
        labels = {1:"M1", 5:"M5", 15:"M15", 30:"M30", 60:"H1", 240:"H4"}
        return labels.get(self.timeframe, f"M{self.timeframe}")


# ------------------------------------------------------------
#  CERVEAU CENTRAL — snapshot vivant de tous les TF
#  clé → "GBPUSDM5", "GBPUSDM15", etc.
# ------------------------------------------------------------
Brain = dict   # Brain["GBPUSDM15"] = Tick


# ------------------------------------------------------------
#  CROSS STATE — mémoire d'un croisement par paire/TF
# ------------------------------------------------------------
@dataclass
class CrossState:
    dominant:       str        # devise dominante actuelle
    last_cross_ts:  float = 0.0   # time.time() du dernier croisement
    max_gap:        float = 0.0   # écart max depuis le croisement
    reject_state:   str = "NEUTRE"
