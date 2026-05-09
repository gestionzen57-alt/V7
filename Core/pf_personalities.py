"""
PowerFlow V6 — pf_personalities.py
Mission 1 : Profils cinématiques par devise + Index comportemental borné.

Doctrine :
  Chaque devise a son propre tempo, son amplitude naturelle, son rôle stratégique.
  Lire JPY comme on lit EUR est une erreur — leurs horloges internes diffèrent.
  
  L'index comportemental borné mesure l'écart d'une devise par rapport à 
  son étalon (l'USD), normalisé par sa propre histoire récente.
  C'est un Z-score relatif, ancré sur USD comme pivot universel du marché.

Architecture :
  - DevisePersonality : dataclass immuable décrivant le caractère d'une devise.
  - DEVISE_PROFILES   : registre des 8 devises majeures.
  - behavioral_index() : Z-score (force_devise - force_usd) sur fenêtre glissante.
  - get_devise_profile() : accès sécurisé au registre.

Compatibilité :
  - Format des données identique à pf_relations.py / pf_sync_detector.py
  - rows = [(bar_time, force_d1, force_d2, ...), ...]
  - devise_cols = [(devise_lowercase, col_name), ...]

Usage :
    from pf_personalities import (
        DEVISE_PROFILES,
        get_devise_profile,
        behavioral_index,
    )
    
    profile = get_devise_profile("JPY")
    z = behavioral_index("EUR", rows, bar_index, devise_cols, lookback=20)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


# ════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION GÉNÉRALE
# ════════════════════════════════════════════════════════════════════════════

DEFAULT_LOOKBACK: int = 20
"""Fenêtre glissante par défaut pour le calcul du Z-score (en barres)."""

ZSCORE_CLIP: float = 3.0
"""Bornage du Z-score à ±3.0 sigma. Au-delà, on plafonne."""

ZSCORE_EXTREME: float = 2.0
"""Seuil au-delà duquel le comportement est qualifié d'extrême."""

EPSILON: float = 1e-9
"""Petite valeur pour éviter les divisions par zéro."""


# ════════════════════════════════════════════════════════════════════════════
#  DATACLASS — DEVISE PERSONALITY
# ════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DevisePersonality:
    """
    Profil cinématique immuable d'une devise.
    
    Attributs :
        devise           : Code 3 lettres (JPY, EUR, GBP, USD, CAD, AUD, NZD, CHF).
        tempo_tf         : Timeframe natif optimal en minutes (5 = M5, 15 = M15, etc.).
                           C'est le TF où le signal est le plus frais et exploitable.
        amplitude_norm   : Amplitude normale du mouvement par barre sur le tempo natif,
                           en points de force [0-100]. Utile pour normaliser la vitesse.
        volatility_class : "HIGH" / "MEDIUM" / "LOW" — caractère de volatilité globale.
        role             : "REFUGE" / "RISK" / "PIVOT" — rôle stratégique en macro.
        lag_ref          : Devise de référence si la devise est follower (ex: NZD → AUD).
                           None si la devise est autonome.
        lag_bars         : Nombre de barres de retard typique vs lag_ref (sur tempo natif).
                           0 si autonome.
        notes            : Remarques libres sur le caractère (oscillation, accélération...).
    """
    devise: str
    tempo_tf: int
    amplitude_norm: float
    volatility_class: str
    role: str
    lag_ref: Optional[str] = None
    lag_bars: int = 0
    notes: str = ""

    def __post_init__(self) -> None:
        # Validation légère pour catch les fautes de frappe à l'enregistrement.
        if self.volatility_class not in ("HIGH", "MEDIUM", "LOW"):
            raise ValueError(
                f"volatility_class invalide pour {self.devise}: {self.volatility_class}"
            )
        if self.role not in ("REFUGE", "RISK", "PIVOT"):
            raise ValueError(
                f"role invalide pour {self.devise}: {self.role}"
            )
        if self.tempo_tf <= 0:
            raise ValueError(
                f"tempo_tf doit être positif pour {self.devise}"
            )


        if self.amplitude_norm < 0:
            raise ValueError(
                f"amplitude_norm doit être >= 0 pour {self.devise}"
            )
        if self.lag_bars < 0:
            raise ValueError(
                f"lag_bars doit être >= 0 pour {self.devise}"
            )
        if self.lag_ref is not None:
            if len(self.lag_ref) != 3:
                raise ValueError(
                    f"lag_ref invalide pour {self.devise}: {self.lag_ref}"
                )
            object.__setattr__(self, "lag_ref", self.lag_ref.upper())
    def is_follower(self) -> bool:
        """True si cette devise suit une autre avec un lag connu."""
        return self.lag_ref is not None and self.lag_bars > 0

    def is_refuge(self) -> bool:
        return self.role == "REFUGE"

    def is_risk(self) -> bool:
        return self.role == "RISK"

    def is_pivot(self) -> bool:
        return self.role == "PIVOT"


# ════════════════════════════════════════════════════════════════════════════
#  REGISTRE DES PROFILS — 8 DEVISES MAJEURES
# ════════════════════════════════════════════════════════════════════════════
#
# Calibration basée sur observation directe des graphiques M15/M5 du 30 avril 2026
# et discussions de Doctrine Architecte. Ces valeurs sont des points de départ
# raisonnables — ils seront affinés empiriquement avec l'accumulation de données.
#
# Convention : clé du dict en MAJUSCULES pour cohérence avec les codes ISO 4217.
#
DEVISE_PROFILES: Dict[str, DevisePersonality] = {

    "JPY": DevisePersonality(
        devise="JPY",
        tempo_tf=5,
        amplitude_norm=18.0,
        volatility_class="HIGH",
        role="REFUGE",
        lag_ref=None,
        lag_bars=0,
        notes="Mouvement violent et vertical. Refuge absolu. Cycle court — un cross JPY sur M30 est déjà périmé.",
    ),

    "CHF": DevisePersonality(
        devise="CHF",
        tempo_tf=30,
        amplitude_norm=3.0,
        volatility_class="LOW",
        role="REFUGE",
        lag_ref="JPY",
        lag_bars=3,
        notes="Refuge confirmateur lent. Suit JPY avec 2-3 barres de retard. Pas exploitable sur M5.",
    ),

    "EUR": DevisePersonality(
        devise="EUR",
        tempo_tf=15,
        amplitude_norm=4.0,
        volatility_class="MEDIUM",
        role="RISK",
        lag_ref=None,
        lag_bars=0,
        notes="Oscillation régulière, sinusoïdale. Cycles propres sur M15-M30. Zone de lisibilité optimale.",
    ),

    "GBP": DevisePersonality(
        devise="GBP",
        tempo_tf=15,
        amplitude_norm=5.0,
        volatility_class="MEDIUM",
        role="RISK",
        lag_ref=None,
        lag_bars=0,
        notes="Imprévisible. Ruptures nettes, retournements violents. Pivot des coalitions risque.",
    ),

    "USD": DevisePersonality(
        devise="USD",
        tempo_tf=30,
        amplitude_norm=3.0,
        volatility_class="MEDIUM",
        role="PIVOT",
        lag_ref=None,
        lag_bars=0,
        notes="Inertie forte. Mouvement lent et pesant. Étalon de référence pour l'index comportemental.",
    ),

    "CAD": DevisePersonality(
        devise="CAD",
        tempo_tf=15,
        amplitude_norm=4.0,
        volatility_class="MEDIUM",
        role="PIVOT",
        lag_ref=None,
        lag_bars=0,
        notes="Leader vs USD de 1-2 barres. Corrélation pétrolière. Pivot dans coalitions risque.",
    ),

    "AUD": DevisePersonality(
        devise="AUD",
        tempo_tf=5,
        amplitude_norm=6.0,
        volatility_class="HIGH",
        role="RISK",
        lag_ref=None,
        lag_bars=0,
        notes="Très volatile, réactif risk-on/off. Oscillations amples sur M5. Souvent leader vs NZD.",
    ),

    "NZD": DevisePersonality(
        devise="NZD",
        tempo_tf=15,
        amplitude_norm=5.0,
        volatility_class="MEDIUM",
        role="RISK",
        lag_ref="AUD",
        lag_bars=3,
        notes="Follower AUD avec retard de 2-4 barres M5. Confirmateur silencieux du flux risque.",
    ),
}


# ════════════════════════════════════════════════════════════════════════════
#  ACCÈS SÉCURISÉ AU REGISTRE
# ════════════════════════════════════════════════════════════════════════════

def get_devise_profile(devise: str) -> Optional[DevisePersonality]:
    """
    Retourne le profil d'une devise. Insensible à la casse.
    
    Args:
        devise: Code de la devise (ex: "jpy", "JPY", "Jpy" tous valides).
    
    Returns:
        DevisePersonality si la devise est connue, None sinon.
    """
    if not devise:
        return None
    return DEVISE_PROFILES.get(devise.upper())


def list_devises_by_role(role: str) -> List[str]:
    """
    Liste les devises ayant un rôle donné.
    
    Args:
        role: "REFUGE", "RISK" ou "PIVOT".
    
    Returns:
        Liste des codes devises (ex: ["JPY", "CHF"] pour role="REFUGE").
    """
    role = role.upper()
    return [
        code for code, profile in DEVISE_PROFILES.items()
        if profile.role == role
    ]


def list_followers() -> List[Tuple[str, str, int]]:
    """
    Liste les relations follower connues.
    
    Returns:
        Liste de tuples (follower, leader, lag_bars).
        Exemple : [("CHF", "JPY", 3), ("NZD", "AUD", 3)]
    """
    out: List[Tuple[str, str, int]] = []
    for code, profile in DEVISE_PROFILES.items():
        if profile.is_follower():
            out.append((code, profile.lag_ref, profile.lag_bars))
    return out


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS BAS-NIVEAU — ACCÈS AUX DONNÉES (cohérent avec pf_relations.py)
# ════════════════════════════════════════════════════════════════════════════

def _col_idx(devise: str, devise_cols: Sequence[Tuple[str, str]]) -> Optional[int]:
    """
    Retourne l'index de colonne d'une devise dans une row.
    Convention : col 0 = bar_time, col 1+ = forces dans l'ordre de devise_cols.
    """
    devise = devise.lower()
    for idx, (d, _c) in enumerate(devise_cols):
        if d == devise:
            return idx + 1   # +1 pour décaler après bar_time
    return None


def _extract_series(
    rows: Sequence[Tuple],
    col_idx: int,
    start: int,
    end: int,
) -> List[float]:
    """
    Extrait une série de valeurs float, en filtrant les None.
    
    Args:
        rows     : Liste de tuples (bar_time, val1, val2, ...).
        col_idx  : Index de colonne à extraire.
        start    : Index de début (inclus, clipé à 0).
        end      : Index de fin (inclus, clipé à len-1).
    
    Returns:
        Liste de valeurs float, sans None.
    """
    start = max(0, start)
    end = min(len(rows) - 1, end)
    out: List[float] = []
    for i in range(start, end + 1):
        v = rows[i][col_idx]
        if v is not None:
            out.append(float(v))
    return out


# ════════════════════════════════════════════════════════════════════════════
#  CALCUL Z-SCORE — IMPLÉMENTATION ROBUSTE (math standard, sans Numpy)
# ════════════════════════════════════════════════════════════════════════════

def _mean(values: Sequence[float]) -> float:
    """Moyenne arithmétique. Retourne 0.0 si vide."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: Sequence[float], ddof: int = 0) -> float:
    """
    Écart-type. ddof=0 = population, ddof=1 = échantillon.
    Retourne 0.0 si moins de 2 valeurs.
    """
    n = len(values)
    if n < 2 or ddof < 0 or n - ddof <= 0:
        return 0.0
    m = _mean(values)
    var = sum((v - m) ** 2 for v in values) / max(1, n - ddof)
    return math.sqrt(var)


def _clip(value: float, low: float, high: float) -> float:
    """Bornage simple."""
    return max(low, min(high, value))


# ════════════════════════════════════════════════════════════════════════════
#  FONCTION PRINCIPALE — INDEX COMPORTEMENTAL BORNÉ
# ════════════════════════════════════════════════════════════════════════════

def behavioral_index(
    devise: str,
    rows: Sequence[Tuple],
    bar_index: int,
    devise_cols: Sequence[Tuple[str, str]],
    lookback: int = DEFAULT_LOOKBACK,
    clip: float = ZSCORE_CLIP,
) -> Optional[float]:
    """
    Calcule l'index comportemental borné d'une devise par rapport à l'USD.
    
    Logique mathématique :
        spread(t) = force_devise(t) - force_usd(t)
        Z(t)      = (spread(t) - mean(spread, lookback)) / std(spread, lookback)
        Index(t)  = clip(Z(t), -clip, +clip)
    
    Interprétation :
        Index > +2  : la devise est anormalement haute par rapport à l'USD
                      (comportement extrême haut, écart vs étalon supérieur à sa norme).
        Index ≈ 0   : comportement normal, écart vs USD dans la moyenne historique.
        Index < -2  : la devise est anormalement basse par rapport à l'USD
                      (comportement extrême bas, élastique potentiellement chargé).
    
    Args:
        devise      : Code de la devise à mesurer (ex: "EUR").
        rows        : Données issues de la DB. Format : [(bar_time, val1, val2, ...), ...]
        bar_index   : Index de la barre courante (0-based).
        devise_cols : Mapping [(devise_lower, col_name), ...] (issu de get_relation_rows).
        lookback    : Nombre de barres pour le calcul de moyenne et écart-type.
        clip        : Bornage du Z-score (±clip).
    
    Returns:
        Float dans [-clip, +clip] si calcul valide, None sinon.
        None retourné si :
        - devise ou USD absente des colonnes
        - bar_index invalide
        - données insuffisantes (< 3 points)
        - écart-type trop faible (série constante)
    
    Note :
        Si la devise demandée EST l'USD, retourne 0.0 (l'USD ne dévie pas de lui-même).
    """
    # ── Vérifications préliminaires ─────────────────────────────────────────
    if not rows or bar_index < 0 or bar_index >= len(rows):
        return None
    
    devise_low = devise.lower()
    
    # Cas trivial : USD vs USD = 0 par construction.
    if devise_low == "usd":
        return 0.0
    
    # ── Récupération des index de colonnes ──────────────────────────────────
    idx_dev = _col_idx(devise_low, devise_cols)
    idx_usd = _col_idx("usd",    devise_cols)
    
    if idx_dev is None or idx_usd is None:
        return None
    
    # ── Construction de la série spread = devise - usd sur lookback ─────────
    start = bar_index - lookback + 1
    series_dev = _extract_series(rows, idx_dev, start, bar_index)
    series_usd = _extract_series(rows, idx_usd, start, bar_index)
    
    # Aligner les deux séries (cas où certaines barres ont des None).
    # On reconstruit en parcourant les indices et en gardant uniquement les paires complètes.
    spreads: List[float] = []
    for i in range(max(0, start), bar_index + 1):
        v_dev = rows[i][idx_dev]
        v_usd = rows[i][idx_usd]
        if v_dev is not None and v_usd is not None:
            spreads.append(float(v_dev) - float(v_usd))
    
    if len(spreads) < 3:
        return None
    
    # ── Calcul du Z-score ───────────────────────────────────────────────────
    spread_now = spreads[-1]
    mu         = _mean(spreads)
    sigma      = _std(spreads, ddof=0)
    
    # Garde-fou : série quasi-constante, le Z-score n'a pas de sens.
    if sigma < EPSILON:
        return 0.0
    
    z = (spread_now - mu) / sigma
    return round(_clip(z, -clip, clip), 4)


# ════════════════════════════════════════════════════════════════════════════
#  FONCTION COMPLÉMENTAIRE — ÉTAT QUALITATIF
# ════════════════════════════════════════════════════════════════════════════

def behavioral_state(z_score: Optional[float]) -> str:
    """
    Convertit un Z-score en label qualitatif lisible.
    
    Args:
        z_score: Valeur retournée par behavioral_index() ou None.
    
    Returns:
        Label parmi:
            "N/A"             : calcul impossible
            "EXTREME_HIGH"    : z > +2
            "HIGH"            : +1 < z ≤ +2
            "NORMAL"          : -1 ≤ z ≤ +1
            "LOW"             : -2 ≤ z < -1
            "EXTREME_LOW"     : z < -2
    """
    if z_score is None:
        return "N/A"
    if z_score >  ZSCORE_EXTREME:
        return "EXTREME_HIGH"
    if z_score >  1.0:
        return "HIGH"
    if z_score >= -1.0:
        return "NORMAL"
    if z_score >= -ZSCORE_EXTREME:
        return "LOW"
    return "EXTREME_LOW"


def behavioral_index_all(
    rows: Sequence[Tuple],
    bar_index: int,
    devise_cols: Sequence[Tuple[str, str]],
    lookback: int = DEFAULT_LOOKBACK,
) -> Dict[str, Optional[float]]:
    """
    Calcule l'index comportemental pour TOUTES les devises présentes dans devise_cols.
    
    Returns:
        Dict { "DEVISE_UPPER": z_score, ... }
        Exemple : {"JPY": 2.31, "EUR": -1.85, "GBP": -2.10, ...}
    """
    out: Dict[str, Optional[float]] = {}
    for dev, _col in devise_cols:
        z = behavioral_index(dev, rows, bar_index, devise_cols, lookback=lookback)
        out[dev.upper()] = z
    return out


# ════════════════════════════════════════════════════════════════════════════
#  SCRIPT DE TEST AVEC MOCK DATA
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 78)
    print("  PowerFlow V6 — pf_personalities.py — Test de validation")
    print("=" * 78)
    
    # ── Test 1 : Profils cinématiques ───────────────────────────────────────
    print("\n[TEST 1] Profils cinématiques (DEVISE_PROFILES)")
    print("-" * 78)
    print(f"{'Devise':<8}{'Tempo':<10}{'Ampl.':<10}{'Vol.':<10}{'Rôle':<12}{'Lag':<20}")
    print("-" * 78)
    for code, profile in DEVISE_PROFILES.items():
        lag_info = ""
        if profile.is_follower():
            lag_info = f"→ {profile.lag_ref} (+{profile.lag_bars} bars)"
        print(
            f"{code:<8}"
            f"M{profile.tempo_tf:<8}"
            f"{profile.amplitude_norm:<10.1f}"
            f"{profile.volatility_class:<10}"
            f"{profile.role:<12}"
            f"{lag_info:<20}"
        )
    
    print(f"\n  Refuges : {list_devises_by_role('REFUGE')}")
    print(f"  Risque  : {list_devises_by_role('RISK')}")
    print(f"  Pivots  : {list_devises_by_role('PIVOT')}")
    print(f"  Followers : {list_followers()}")
    
    # ── Test 2 : Accès sécurisé ─────────────────────────────────────────────
    print("\n[TEST 2] Accès sécurisé via get_devise_profile()")
    print("-" * 78)
    for test_input in ["JPY", "jpy", "Jpy", "XYZ", "", None]:
        try:
            p = get_devise_profile(test_input)
            label = "OK" if p else "None (inconnu)"
            print(f"  get_devise_profile({test_input!r:>10}) → {label}")
        except Exception as e:
            print(f"  get_devise_profile({test_input!r:>10}) → ERREUR: {e}")
    
    # ── Test 3 : Index comportemental sur mock data ─────────────────────────
    print("\n[TEST 3] Index comportemental — Scénario : effondrement EUR vs USD stable")
    print("-" * 78)
    
    # Mock data : 25 barres simulées
    # USD reste stable autour de 50, EUR descend progressivement
    # JPY explose vers le haut (refuge actif)
    mock_devise_cols: List[Tuple[str, str]] = [
        ("eur", "force_eur"),
        ("usd", "force_usd"),
        ("jpy", "force_jpy"),
        ("gbp", "force_gbp"),
    ]
    
    mock_rows: List[Tuple] = []
    base_eur = 50.0
    base_usd = 50.0
    base_jpy = 50.0
    base_gbp = 50.0
    
    for i in range(25):
        bar_time = f"2026-04-30 {10 + i // 4:02d}:{(i % 4) * 15:02d}"
        # USD oscille très légèrement autour de 50 (inertie)
        v_usd = base_usd + math.sin(i * 0.3) * 1.5
        # EUR : stable au début, puis effondrement progressif après bar 12
        if i < 12:
            v_eur = base_eur + math.sin(i * 0.4) * 2.0
        else:
            v_eur = base_eur - (i - 12) * 3.5 + math.sin(i * 0.4) * 1.5
        # JPY : explosion vers le haut après bar 12
        if i < 12:
            v_jpy = base_jpy + math.sin(i * 0.5) * 2.0
        else:
            v_jpy = base_jpy + (i - 12) * 4.0 + math.sin(i * 0.5) * 1.0
        # GBP : tendance baissière modérée
        v_gbp = base_gbp - i * 0.8 + math.sin(i * 0.6) * 1.5
        
        mock_rows.append((bar_time, v_eur, v_usd, v_jpy, v_gbp))
    
    print(f"  Mock data : {len(mock_rows)} barres simulées")
    print(f"  Première  : {mock_rows[0]}")
    print(f"  Dernière  : {mock_rows[-1]}")
    
    # Affichage tabulaire de l'évolution des Z-scores
    print(f"\n  {'Bar':<5}{'Time':<18}{'EUR':<10}{'USD':<10}{'JPY':<10}"
          f"{'Z(EUR)':<10}{'Z(JPY)':<10}{'Z(GBP)':<10}{'État EUR':<14}")
    print("  " + "-" * 95)
    
    for i in range(len(mock_rows)):
        if i < 5 and i != 0:
            continue   # On affiche bar 0 puis on saute jusqu'à bar 5+ pour lisibilité
        if i % 2 != 0 and i < 18:
            continue
        
        z_eur = behavioral_index("EUR", mock_rows, i, mock_devise_cols, lookback=10)
        z_jpy = behavioral_index("JPY", mock_rows, i, mock_devise_cols, lookback=10)
        z_gbp = behavioral_index("GBP", mock_rows, i, mock_devise_cols, lookback=10)
        state_eur = behavioral_state(z_eur)
        
        z_eur_s = f"{z_eur:+.2f}" if z_eur is not None else "N/A"
        z_jpy_s = f"{z_jpy:+.2f}" if z_jpy is not None else "N/A"
        z_gbp_s = f"{z_gbp:+.2f}" if z_gbp is not None else "N/A"
        
        print(
            f"  [{i:>2}]  {mock_rows[i][0]:<18}"
            f"{mock_rows[i][1]:<10.1f}{mock_rows[i][2]:<10.1f}{mock_rows[i][3]:<10.1f}"
            f"{z_eur_s:<10}{z_jpy_s:<10}{z_gbp_s:<10}{state_eur:<14}"
        )
    
    # ── Test 4 : behavioral_index_all sur la dernière barre ──────────────────
    print("\n[TEST 4] behavioral_index_all() — snapshot sur dernière barre")
    print("-" * 78)
    last_idx = len(mock_rows) - 1
    snapshot = behavioral_index_all(mock_rows, last_idx, mock_devise_cols, lookback=10)
    for dev, z in snapshot.items():
        z_str = f"{z:+.3f}" if z is not None else "N/A"
        state = behavioral_state(z)
        print(f"  {dev:<5} : Z = {z_str:<8}  →  {state}")
    
    # ── Test 5 : Cas limites ────────────────────────────────────────────────
    print("\n[TEST 5] Cas limites — robustesse du calcul")
    print("-" * 78)
    
    # Cas 5a : devise inconnue
    z = behavioral_index("XYZ", mock_rows, 20, mock_devise_cols)
    print(f"  Devise inconnue (XYZ)         : {z}  (attendu: None)")
    
    # Cas 5b : bar_index hors borne
    z = behavioral_index("EUR", mock_rows, 999, mock_devise_cols)
    print(f"  bar_index hors borne (999)    : {z}  (attendu: None)")
    
    # Cas 5c : USD vs USD
    z = behavioral_index("USD", mock_rows, 20, mock_devise_cols)
    print(f"  USD vs USD                    : {z}  (attendu: 0.0)")
    
    # Cas 5d : pas assez de données (bar_index = 1)
    z = behavioral_index("EUR", mock_rows, 1, mock_devise_cols, lookback=20)
    print(f"  Données insuffisantes (idx=1) : {z}  (attendu: None ou Z partiel)")
    
    # Cas 5e : série constante (sigma ≈ 0)
    flat_cols: List[Tuple[str, str]] = [("eur", "force_eur"), ("usd", "force_usd")]
    flat_rows = [(f"2026-04-30 10:{i:02d}", 50.0, 50.0) for i in range(15)]
    z = behavioral_index("EUR", flat_rows, 14, flat_cols, lookback=10)
    print(f"  Série constante (sigma≈0)     : {z}  (attendu: 0.0)")
    
    print("\n" + "=" * 78)
    print("  Validation terminée.")
    print("=" * 78)
