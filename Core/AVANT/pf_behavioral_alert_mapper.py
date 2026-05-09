"""
pf_behavioral_alert_mapper.py
PowerFlow V6 — Behavioral Alert Mapper V0.8.2.1

Transforme les sorties JSON existantes (temporal_node_state, currency_energy_state)
en alertes comportementales PowerFlow nommées.

Règles dures :
- Aucune écriture DB
- Aucune dépendance cockpit
- Aucune dépendance Telegram
- Ne pas modifier capture_bridge.py ni pf_temporal_node_state.py
- NODE_HEAT ≠ CURRENCY_ENERGY
- Energy ne produit jamais BUY/SELL ni HOT seule
- COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED
- Pas de first_detachment = pas de release confirmée

Priorité des données energy (V0.8.2.1) :
  1. tns.energy_context          si présent ET mode != ENERGY_ABSENT
  2. tns.energy_release_alignment si présent (fallback TNS intermédiaire — runtime V0.8.x)
  3. currency_energy_state        standalone (fallback externe)
  4. {}                           checkers energy désactivés silencieusement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

ALERT_LEVELS = ("HOT", "WATCH", "DEGRADED", "INFO")

# Modes energy_context qui signalent l'absence de données
_ENERGY_ABSENT_MODES = frozenset({"ENERGY_ABSENT", "ABSENT", "NONE"})


@dataclass
class BehavioralAlert:
    name: str
    level: str                    # HOT | WATCH | DEGRADED | INFO
    reason: str
    source_fields: list[str]
    dashboard_badge: str
    telegram_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "reason": self.reason,
            "source_fields": self.source_fields,
            "dashboard_badge": self.dashboard_badge,
            "telegram_text": self.telegram_text,
        }


@dataclass
class MapperOutput:
    behavioral_alerts: list[dict[str, Any]] = field(default_factory=list)
    degraded_alerts: list[dict[str, Any]] = field(default_factory=list)
    next_watch_enriched: list[str] = field(default_factory=list)
    film_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "behavioral_alerts": self.behavioral_alerts,
            "degraded_alerts": self.degraded_alerts,
            "next_watch_enriched": self.next_watch_enriched,
            "film_steps": self.film_steps,
        }


# ---------------------------------------------------------------------------
# Accesseurs sécurisés
# ---------------------------------------------------------------------------

def _get(d: dict, *keys: str, default: Any = None) -> Any:
    """Navigation imbriquée sans exception."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is None:
            return default
    return cur


def _str(d: dict, *keys: str, default: str = "") -> str:
    v = _get(d, *keys, default=default)
    return str(v) if v is not None else default


def _bool(d: dict, *keys: str, default: bool = False) -> bool:
    v = _get(d, *keys, default=default)
    return bool(v)


def _float(d: dict, *keys: str, default: float = 0.0) -> float:
    v = _get(d, *keys, default=default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _list(d: dict, *keys: str) -> list:
    v = _get(d, *keys, default=[])
    return v if isinstance(v, list) else []


# ---------------------------------------------------------------------------
# EnergyView — vue normalisée indépendante de la source
# ---------------------------------------------------------------------------

@dataclass
class EnergyView:
    """
    Vue normalisée des données energy pour les checkers.
    Indépendante de la source (energy_context / energy_release_alignment / standalone).

    Règles :
    - is_present = False → tous les checkers energy sont silencieux
    - node_energy_relation est observationnel — jamais un signal
    - Energy ne produit jamais HOT ni BUY/SELL
    """
    source: str = "NONE"  # "energy_context" | "energy_release_alignment" | "standalone" | "NONE"

    base_currency: str = ""
    base_energy_label: str = ""
    quote_currency: str = ""
    quote_energy_label: str = ""

    node_energy_relation: str = ""   # ALIGNED | DIVERGENT | NEUTRAL | UNKNOWN
    alignment_state: str = ""
    secondary_state: str = ""        # COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY | null | ...
    field_quality: str = ""          # ENERGY_STRONG | ENERGY_THIN_OR_MIXED | ENERGY_ABSENT

    # Currencies brutes — pour fallback standalone uniquement
    currencies: dict = field(default_factory=dict)

    @property
    def is_present(self) -> bool:
        return self.source != "NONE"

    @property
    def is_divergent(self) -> bool:
        return self.node_energy_relation == "DIVERGENT"

    @property
    def is_thin_or_absent(self) -> bool:
        return self.field_quality in ("ENERGY_THIN_OR_MIXED", "ENERGY_ABSENT", "")

    @property
    def counter_release_unsupported(self) -> bool:
        return self.secondary_state == "COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY"


# ---------------------------------------------------------------------------
# Résolveur de source energy — V0.8.2.1
# ---------------------------------------------------------------------------

def _resolve_energy(tns: dict, standalone: dict) -> EnergyView:
    """
    Résout la meilleure source energy disponible → EnergyView normalisé.

    Priorité :
      1. tns.energy_context          (V0.8.2+)
      2. tns.energy_release_alignment (V0.8.x runtime — fallback TNS)
      3. standalone currency_energy_state
      4. EnergyView vide
    """
    # Priorité 1 : energy_context (V0.8.2+)
    ec = _get(tns, "energy_context", default={}) or {}
    if ec:
        mode = _str(ec, "mode")
        if mode and mode not in _ENERGY_ABSENT_MODES:
            return _ev_from_context(ec)

    # Priorité 2 : energy_release_alignment (V0.8.x runtime)
    era = _get(tns, "energy_release_alignment", default={}) or {}
    if era and _str(era, "status") == "OK":
        return _ev_from_alignment(era, tns)

    # Priorité 3 : standalone
    if standalone:
        return _ev_from_standalone(standalone, tns)

    return EnergyView(source="NONE")


def _ev_from_context(ec: dict) -> EnergyView:
    """EnergyView depuis tns.energy_context (V0.8.2+)."""
    return EnergyView(
        source="energy_context",
        base_currency=_str(ec, "base_currency"),
        base_energy_label=_str(ec, "base_energy_label"),
        quote_currency=_str(ec, "quote_currency"),
        quote_energy_label=_str(ec, "quote_energy_label"),
        node_energy_relation=_str(ec, "node_energy_relation"),
        alignment_state=_str(ec, "alignment_state"),
        secondary_state=_str(ec, "secondary_state"),
        field_quality=_str(ec, "field_quality"),
        currencies={},
    )


def _ev_from_alignment(era: dict, tns: dict) -> EnergyView:
    """EnergyView depuis tns.energy_release_alignment (V0.8.x runtime)."""
    symbol = _str(_get(tns, "meta", default={}), "symbol", default="GBPUSD")
    base = symbol[:3].upper() if len(symbol) >= 6 else ""
    quote = symbol[3:6].upper() if len(symbol) >= 6 else ""

    # Labels depuis energy_snapshots M1
    snapshots = _get(era, "energy_snapshots", default={}) or {}
    m1_snap = snapshots.get("M1", {}) or {}
    base_label = _str(m1_snap.get(base, {}), "label") if base else ""
    quote_label = _str(m1_snap.get(quote, {}), "label") if quote else ""

    # node_energy_relation dérivé
    tf_votes = _get(era, "tf_votes", default={}) or {}
    node_energy_relation = _derive_relation_from_alignment(tf_votes, era)

    # secondary_state : champ direct ou inférence
    secondary_state = _str(era, "secondary_state") or ""
    if not secondary_state:
        release_state = _str(era, "release_state")
        field_quality = _str(era, "field_quality")
        if (release_state == "COUNTER_RELEASE_ATTEMPT"
                and field_quality in ("ENERGY_THIN_OR_MIXED", "ENERGY_ABSENT")):
            secondary_state = "COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY"

    return EnergyView(
        source="energy_release_alignment",
        base_currency=base,
        base_energy_label=base_label,
        quote_currency=quote,
        quote_energy_label=quote_label,
        node_energy_relation=node_energy_relation,
        alignment_state=_str(era, "state"),
        secondary_state=secondary_state,
        field_quality=_str(era, "field_quality"),
        currencies={},
    )


def _derive_relation_from_alignment(tf_votes: dict, era: dict) -> str:
    """Dérive node_energy_relation depuis tf_votes + release_state + field_quality."""
    release_state = _str(era, "release_state")
    field_quality = _str(era, "field_quality")

    # COUNTER_RELEASE + champ thin → DIVERGENT
    # (node pousse dans un sens, energy ne supporte pas)
    if (release_state == "COUNTER_RELEASE_ATTEMPT"
            and field_quality in ("ENERGY_THIN_OR_MIXED", "ENERGY_ABSENT")):
        return "DIVERGENT"

    # Tous les votes WEAK_NEUTRAL → NEUTRAL
    votes = list(tf_votes.values()) if tf_votes else []
    if votes and all("WEAK_NEUTRAL" in v for v in votes):
        return "NEUTRAL"

    # alignment_state explicite
    state = _str(era, "state")
    if "DIVERGENT" in state:
        return "DIVERGENT"
    if "ALIGNED" in state:
        return "ALIGNED"

    return "NEUTRAL"


def _ev_from_standalone(standalone: dict, tns: dict) -> EnergyView:
    """EnergyView depuis currency_energy_state standalone (rétrocompatibilité V0.1)."""
    symbol = _str(_get(tns, "meta", default={}), "symbol", default="GBPUSD")
    base = symbol[:3].upper() if len(symbol) >= 6 else ""
    quote = symbol[3:6].upper() if len(symbol) >= 6 else ""

    curs = _get(standalone, "currencies", default={}) or {}
    base_label = _str(curs.get(base, {}), "energy_label") if base in curs else ""
    quote_label = _str(curs.get(quote, {}), "energy_label") if quote in curs else ""

    LOW_LABELS = frozenset({"ENERGY_LOW", "ENERGY_WEAK", "ENERGY_NONE"})

    # Inférer node_energy_relation depuis direction + labels
    relation = "UNKNOWN"
    direction = _dominant_direction(tns)
    highest = _highest_level(tns)
    if direction and highest:
        dominant_ccy = None
        if base and base.lower() in direction.lower():
            tail = direction.lower().split(base.lower())[-1].split("/")[0]
            if "up" in tail:
                dominant_ccy = base
        if not dominant_ccy and quote and quote.lower() in direction.lower():
            tail = direction.lower().split(quote.lower())[-1].split("/")[0]
            if "up" in tail:
                dominant_ccy = quote
        if dominant_ccy:
            dom_label = base_label if dominant_ccy == base else quote_label
            relation = "DIVERGENT" if dom_label in LOW_LABELS else "ALIGNED"
        else:
            relation = "NEUTRAL"

    # field_quality inférée
    field_quality = (
        "ENERGY_THIN_OR_MIXED"
        if base_label in LOW_LABELS and quote_label in LOW_LABELS
        else "ENERGY_STRONG"
    )

    return EnergyView(
        source="standalone",
        base_currency=base,
        base_energy_label=base_label,
        quote_currency=quote,
        quote_energy_label=quote_label,
        node_energy_relation=relation,
        alignment_state="",
        secondary_state="",
        field_quality=field_quality,
        currencies=curs,
    )


# ---------------------------------------------------------------------------
# Extracteurs contexte TNS
# ---------------------------------------------------------------------------

def _extract_kinematics(tns: dict) -> dict:
    return _get(tns, "kinematics_state", default={}) or {}


def _extract_release(tns: dict) -> dict:
    kin = _extract_kinematics(tns)
    return _get(kin, "release_candidate", default={}) or {}


def _extract_relay(tns: dict) -> dict:
    return _get(tns, "telegram_gating", default={}) or {}


def _extract_node_summary(tns: dict) -> dict:
    return _get(tns, "node_summary", default={}) or {}


def _extract_nodes(tns: dict) -> list[dict]:
    return _list(tns, "nodes")


def _m1_node(nodes: list[dict]) -> dict | None:
    for n in nodes:
        if _str(n, "timeframe") == "M1":
            return n
    return None


def _m5_role(tns: dict) -> str:
    relay = _extract_relay(tns)
    r = _str(relay, "m5_role")
    if r:
        return r
    nodes = _extract_nodes(tns)
    for n in nodes:
        v = _str(n, "context", "m5_role")
        if v:
            return v
    return ""


def _highest_level(tns: dict) -> str:
    return _str(_extract_node_summary(tns), "highest_level")


def _dominant_direction(tns: dict) -> str:
    return _str(_extract_node_summary(tns), "dominant_direction")


# ---------------------------------------------------------------------------
# Checkers — signature : (tns: dict, ev: EnergyView) → BehavioralAlert | None
# ---------------------------------------------------------------------------

def _check_first_detachment_with_clean_relay(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """FIRST_DETACHMENT_WITH_CLEAN_RELAY — HOT : détachement + relay clean."""
    kin = _extract_kinematics(tns)
    det = _get(kin, "first_detachment", default={}) or {}
    if not _bool(det, "detected"):
        return None
    relay = _extract_relay(tns)
    if _str(relay, "relay_quality") != "CLEAN":
        return None

    det_label = _str(det, "label", default="DETACHMENT")
    direction = _dominant_direction(tns)
    return BehavioralAlert(
        name="FIRST_DETACHMENT_WITH_CLEAN_RELAY",
        level="HOT",
        reason=f"Premier détachement confirmé ({det_label}) avec relais M5 propre — {direction}",
        source_fields=["kinematics_state.first_detachment", "telegram_gating.relay_quality"],
        dashboard_badge="🔥 DETACH+RELAY",
        telegram_text=f"⚡ FIRST DETACHMENT + RELAY CLEAN\n{direction}\nKinematics: {det_label}",
    )


def _check_hot_degraded_by_missing_relay(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """HOT_DEGRADED_BY_MISSING_RELAY — DEGRADED : HOT_NODE + relay manquant/thin."""
    highest = _highest_level(tns)
    if highest not in ("HOT_NODE", "NODE_CONFIRMED"):
        return None
    relay = _extract_relay(tns)
    relay_sample = _str(relay, "relay_sample_state")
    relay_quality = _str(relay, "relay_quality")
    if not (relay_sample in ("M5_RELAY_MISSING_IN_DB", "M5_RELAY_THIN_SAMPLE") or relay_quality == "MISSING"):
        return None
    direction = _dominant_direction(tns)
    return BehavioralAlert(
        name="HOT_DEGRADED_BY_MISSING_RELAY",
        level="DEGRADED",
        reason=f"Node HOT présent ({highest}) mais relais M5 dégradé ({relay_sample}) — lecture affaiblie",
        source_fields=["node_summary.highest_level", "telegram_gating.relay_sample_state"],
        dashboard_badge="⚠️ HOT↓RELAY",
        telegram_text=f"⚠️ HOT DÉGRADÉ — relay M5 absent/thin\n{direction}\nRelay: {relay_sample}",
    )


def _check_m5_relay_thin(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """M5_RELAY_THIN_ALERT — WATCH : relay thin."""
    relay = _extract_relay(tns)
    if _str(relay, "relay_sample_state") != "M5_RELAY_THIN_SAMPLE":
        return None
    return BehavioralAlert(
        name="M5_RELAY_THIN_ALERT",
        level="WATCH",
        reason="M5 présent mais échantillon trop petit — relais tactique fragile",
        source_fields=["telegram_gating.relay_sample_state"],
        dashboard_badge="👁 M5 THIN",
        telegram_text="👁 M5 RELAY THIN\nÉchantillon M5 insuffisant — filtrer lecture tactique",
    )


def _check_release_rejected_no_detachment(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """RELEASE_REJECTED_NO_DETACHMENT_ALERT — INFO : release rejetée."""
    rel = _extract_release(tns)
    if _str(rel, "release_state") != "RELEASE_REJECTED":
        return None
    reasons_nok = _list(rel, "reasons_nok")
    has_no_detach = "no_first_detachment" in reasons_nok
    reason_txt = "Pas de premier détachement détecté" if has_no_detach else f"Release rejetée : {', '.join(reasons_nok)}"
    return BehavioralAlert(
        name="RELEASE_REJECTED_NO_DETACHMENT_ALERT",
        level="INFO",
        reason=reason_txt,
        source_fields=[
            "kinematics_state.release_candidate.release_state",
            "kinematics_state.release_candidate.reasons_nok",
        ],
        dashboard_badge="ℹ RELEASE✗",
        telegram_text=f"ℹ RELEASE REJETÉE\n{reason_txt}",
    )


def _check_counter_release_attempt(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """
    COUNTER_RELEASE_ATTEMPT_ALERT — WATCH.
    ≠ RELEASE_CONFIRMED.

    Enrichissement V0.8.2.1 :
      Si energy_context.secondary_state = COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
      → reason et source_fields enrichis.
    """
    rel = _extract_release(tns)
    if _str(rel, "release_state") != "COUNTER_RELEASE_ATTEMPT":
        return None

    direction = _dominant_direction(tns)

    energy_qualifier = ""
    source_fields = ["kinematics_state.release_candidate.release_state"]

    if ev.is_present and ev.counter_release_unsupported:
        energy_qualifier = " — counter release non supportée par energy"
        source_fields.append("energy_context.secondary_state")

    reason = (
        "Tentative de contre-libération détectée — CONTRE la direction dominante, "
        f"non confirmée (COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED){energy_qualifier}"
    )

    return BehavioralAlert(
        name="COUNTER_RELEASE_ATTEMPT_ALERT",
        level="WATCH",
        reason=reason,
        source_fields=source_fields,
        dashboard_badge="👁 COUNTER REL",
        telegram_text=f"👁 COUNTER RELEASE ATTEMPT\nContre {direction}\nNon confirmé — observer absorption",
    )


def _check_node_heat_energy_divergence(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """
    NODE_HEAT_ENERGY_DIVERGENCE — WATCH.
    Energy ≠ Node Heat.

    Enrichissement V0.8.2.1 :
      - source energy_context / alignment → utilise ev.node_energy_relation directement.
      - source standalone → logique currencies (rétrocompatibilité V0.1).
    """
    if not ev.is_present:
        return None

    highest = _highest_level(tns)
    if highest not in ("HOT_NODE", "NODE_CONFIRMED", "FAST_NODE_BIRTH"):
        return None

    direction = _dominant_direction(tns)
    if not direction:
        return None

    # --- energy_context ou energy_release_alignment ---
    if ev.source in ("energy_context", "energy_release_alignment"):
        if not ev.is_divergent:
            return None

        base = ev.base_currency or "BASE"
        quote = ev.quote_currency or "QUOTE"
        base_lbl = ev.base_energy_label or "?"
        quote_lbl = ev.quote_energy_label or "?"

        return BehavioralAlert(
            name="NODE_HEAT_ENERGY_DIVERGENCE",
            level="WATCH",
            reason=(
                f"Node {highest} — direction {direction} — "
                f"mais {base}={base_lbl} / {quote}={quote_lbl} "
                f"(node_energy_relation={ev.node_energy_relation}) — "
                f"Node Heat ≠ Currency Energy"
            ),
            source_fields=[
                "node_summary.highest_level",
                "energy_context.node_energy_relation",
                "energy_context.field_quality",
            ],
            dashboard_badge="👁 HEAT≠ENERGY",
            telegram_text=(
                f"👁 NODE HEAT / ENERGY DIVERGENCE\n"
                f"Node: {highest} | relation: {ev.node_energy_relation}\n"
                f"{base}={base_lbl} | {quote}={quote_lbl}\n"
                f"Ne pas confondre — observer les deux"
            ),
        )

    # --- standalone (rétrocompatibilité V0.1) ---
    symbol = _str(_get(tns, "meta", default={}), "symbol", default="GBPUSD")
    if len(symbol) < 6:
        return None

    base = symbol[:3].upper()
    quote = symbol[3:6].upper()
    curs = ev.currencies

    dominant_ccy = None
    if base.lower() in direction.lower() and "up" in direction.lower().split(base.lower())[-1].split("/")[0]:
        dominant_ccy = base
    elif quote.lower() in direction.lower() and "up" in direction.lower().split(quote.lower())[-1].split("/")[0]:
        dominant_ccy = quote

    if not dominant_ccy or dominant_ccy not in curs:
        return None

    energy_label = _str(curs[dominant_ccy], "energy_label")
    LOW_LABELS = frozenset({"ENERGY_LOW", "ENERGY_WEAK", "ENERGY_NONE"})
    if energy_label not in LOW_LABELS:
        return None

    return BehavioralAlert(
        name="NODE_HEAT_ENERGY_DIVERGENCE",
        level="WATCH",
        reason=f"Node {highest} signale {dominant_ccy} dominant mais Currency Energy = {energy_label} — lire sans confondre Node Heat et Energy",
        source_fields=[
            "node_summary.highest_level",
            f"currencies.{dominant_ccy}.energy_label",
        ],
        dashboard_badge="👁 HEAT≠ENERGY",
        telegram_text=f"👁 NODE HEAT / ENERGY DIVERGENCE\nNode: {highest} | {dominant_ccy} Energy: {energy_label}\nNe pas confondre — observer les deux",
    )


def _check_m1_active_m5_weak(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """M1_ACTIVE_M5_WEAK — WATCH : M1 actif + M5 absent/weak."""
    nodes = _extract_nodes(tns)
    m1 = _m1_node(nodes)
    if m1 is None:
        return None
    m5_r = _m5_role(tns)
    WEAK_M5 = frozenset({"M5_RELAY_MISSING_IN_DB", "M5_RELAY_THIN_SAMPLE", "M5_WEAK", "M5_NODE_ABSENT", ""})
    if m5_r not in WEAK_M5:
        return None
    level = _str(m1, "level")
    direction = _str(m1, "direction_bias")
    return BehavioralAlert(
        name="M1_ACTIVE_M5_WEAK",
        level="WATCH",
        reason=f"M1 actif ({level}) sans relais M5 fort ({m5_r or 'absent'}) — naissance sans confirmation tactique",
        source_fields=["nodes[M1].level", "telegram_gating.m5_role"],
        dashboard_badge="👁 M1↑ M5↓",
        telegram_text=f"👁 M1 ACTIF / M5 FAIBLE\n{direction}\nM1: {level} | M5: {m5_r or 'absent'}",
    )


def _check_acceleration_spike_without_zone_tension(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """ACCELERATION_SPIKE_WITHOUT_ZONE_TENSION_ALERT — WATCH."""
    kin = _extract_kinematics(tns)
    accel_state = _str(kin, "acceleration_state")
    if accel_state not in ("SPIKE", "HIGH", "EXPANDING"):
        return None
    nodes = _extract_nodes(tns)
    has_compression = any(_bool(n, "has_compression") for n in nodes)
    has_zone_reason = any(
        "zone_tension" in _list(n, "reasons") or "compression" in _list(n, "reasons")
        for n in nodes
    )
    if has_compression or has_zone_reason:
        return None
    return BehavioralAlert(
        name="ACCELERATION_SPIKE_WITHOUT_ZONE_TENSION_ALERT",
        level="WATCH",
        reason=f"Accélération cinématique ({accel_state}) sans tension de zone — spike possiblement non ancré",
        source_fields=["kinematics_state.acceleration_state", "nodes[].has_compression"],
        dashboard_badge="👁 ACCEL/NOZONE",
        telegram_text=f"👁 ACCELERATION SPIKE — ZONE ABSENTE\nAccel: {accel_state}\nSpike sans ancrage zone — filtrer",
    )


def _check_tight_gravity_cluster(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """
    TIGHT_GRAVITY_CLUSTER_ALERT — INFO.

    Enrichissement V0.8.2.1 :
      Si ev.is_thin_or_absent → note dans reason + source_fields.
    """
    kin = _extract_kinematics(tns)
    cluster = _get(kin, "tight_gravity_cluster", default={}) or {}
    label = _str(cluster, "label")

    CLUSTER_LABELS = frozenset({
        "M15_TIGHT_GRAVITY_GROUP",
        "M1_TIGHT_GRAVITY_GROUP",
        "M5_TIGHT_GRAVITY_GROUP",
        "TIGHT_GRAVITY_GROUP",
    })
    if label not in CLUSTER_LABELS:
        return None

    currencies = _list(cluster, "currencies")
    spread = _float(cluster, "force_spread")
    ccy_str = "+".join(currencies) if currencies else "?"

    energy_note = ""
    source_fields = ["kinematics_state.tight_gravity_cluster"]
    if ev.is_present and ev.is_thin_or_absent:
        energy_note = " — champ energy thin/mixed"
        source_fields.append("energy_context.field_quality")

    return BehavioralAlert(
        name="TIGHT_GRAVITY_CLUSTER_ALERT",
        level="INFO",
        reason=f"Cluster de gravité serré détecté ({label}) — {ccy_str} en compression (spread force: {spread:.1f}){energy_note}",
        source_fields=source_fields,
        dashboard_badge="ℹ GRAVITY CLUSTER",
        telegram_text=f"ℹ TIGHT GRAVITY CLUSTER\n{label}\nDevises: {ccy_str} | Spread: {spread:.1f}",
    )


def _check_same_angle_cluster(tns: dict, ev: EnergyView) -> BehavioralAlert | None:
    """SAME_ANGLE_CLUSTER_ALERT — INFO."""
    kin = _extract_kinematics(tns)
    cluster = _get(kin, "same_angle_cluster", default={}) or {}
    label = _str(cluster, "label")
    if label in ("NO_CLUSTER", "", None):
        return None
    currencies = _list(cluster, "currencies")
    if not currencies:
        return None
    ccy_str = "+".join(currencies)
    return BehavioralAlert(
        name="SAME_ANGLE_CLUSTER_ALERT",
        level="INFO",
        reason=f"Cluster d'angles identiques ({label}) — {ccy_str} en mouvement synchronisé",
        source_fields=["kinematics_state.same_angle_cluster"],
        dashboard_badge="ℹ SAME ANGLE",
        telegram_text=f"ℹ SAME ANGLE CLUSTER\n{label}\nDevises: {ccy_str}",
    )


# ---------------------------------------------------------------------------
# Film de séquence
# ---------------------------------------------------------------------------

_FILM_MATURITY_SEQUENCE = [
    "BIRTH",
    "CONFIRMING",
    "ABSORBING",
    "SECOND_LEG",
    "LATE",
    "CHAOTIC",
]


def _build_film_steps(tns: dict, ev: EnergyView) -> list[str]:
    """Construit un film de séquence lisible depuis l'état courant."""
    steps: list[str] = []

    summary = _extract_node_summary(tns)
    nodes = _extract_nodes(tns)
    best_node = max(nodes, key=lambda n: _float(n, "score")) if nodes else None
    maturity = _str(best_node, "maturity") if best_node else None

    direction = _str(summary, "dominant_direction")
    relay = _extract_relay(tns)
    relay_quality = _str(relay, "relay_quality")
    kin = _extract_kinematics(tns)
    release = _extract_release(tns)

    # 1 — fractal
    fractal = _str(summary, "fractal_state")
    if fractal:
        steps.append(f"[FRACTAL] {fractal}")

    # 2 — node actif
    if best_node:
        level = _str(best_node, "level")
        tf = _str(best_node, "timeframe")
        steps.append(f"[NODE] {level} @ {tf} — {direction}")

    # 3 — relay M5
    if relay_quality == "CLEAN":
        steps.append("[RELAY] M5 relais propre — confirmation tactique disponible")
    elif relay_quality in ("MISSING", "THIN"):
        steps.append(f"[RELAY] M5 {relay_quality} — relais tactique fragile")

    # 4 — cinématique
    accel = _str(kin, "acceleration_state")
    speed = _str(kin, "speed_state")
    angle = _str(kin, "angle_state")
    if accel or speed:
        steps.append(f"[KINEM] angle={angle} | speed={speed} | accel={accel}")

    # 5 — first detachment
    det = _get(kin, "first_detachment", default={}) or {}
    if _bool(det, "detected"):
        steps.append(f"[DETACH] {_str(det, 'label')} — détachement actif")
    else:
        steps.append(f"[DETACH] {_str(det, 'label', default='NO_DETACHMENT')} — pas de détachement")

    # 6 — release state
    release_state = _str(release, "release_state")
    if release_state:
        reasons_ok = _list(release, "reasons_ok")
        reasons_nok = _list(release, "reasons_nok")
        ok_str = ",".join(reasons_ok) if reasons_ok else "—"
        nok_str = ",".join(reasons_nok) if reasons_nok else "—"
        steps.append(f"[RELEASE] {release_state} | ok={ok_str} | nok={nok_str}")

    # 7 — [ENERGY_CONTEXT] V0.8.2.1 (priorité sur [ENERGY] legacy)
    if ev.source in ("energy_context", "energy_release_alignment"):
        base = ev.base_currency or "BASE"
        quote = ev.quote_currency or "QUOTE"
        base_lbl = ev.base_energy_label or "?"
        quote_lbl = ev.quote_energy_label or "?"
        relation = ev.node_energy_relation or "UNKNOWN"
        field_q = ev.field_quality or "?"
        steps.append(
            f"[ENERGY_CONTEXT] OBSERVATION_ONLY | {base}={base_lbl} | {quote}={quote_lbl}"
            f" | relation={relation} | field={field_q}"
        )
    elif ev.source == "standalone" and (ev.base_currency or ev.quote_currency):
        # Rétrocompatibilité V0.1
        base = ev.base_currency
        quote = ev.quote_currency
        base_lbl = ev.base_energy_label or "N/A"
        quote_lbl = ev.quote_energy_label or "N/A"
        steps.append(f"[ENERGY] {base}={base_lbl} | {quote}={quote_lbl} (≠ Node Heat)")

    # 8 — maturité
    if maturity:
        idx = _FILM_MATURITY_SEQUENCE.index(maturity) if maturity in _FILM_MATURITY_SEQUENCE else -1
        if idx >= 0 and idx + 1 < len(_FILM_MATURITY_SEQUENCE):
            nxt = _FILM_MATURITY_SEQUENCE[idx + 1]
            steps.append(f"[MATURITY] {maturity} → surveiller {nxt}")

    return steps


# ---------------------------------------------------------------------------
# Next watch enrichi
# ---------------------------------------------------------------------------

def _build_next_watch(tns: dict, behavioral_alerts: list[BehavioralAlert]) -> list[str]:
    """Enrichit next_watch avec contexte des alertes."""
    base_nw = _list(tns, "next_watch")
    extra: list[str] = []

    alert_names = {a.name for a in behavioral_alerts}

    if "FIRST_DETACHMENT_WITH_CLEAN_RELAY" in alert_names:
        extra.append("WATCH_RELEASE_CONFIRMATION — détachement + relay clean actif")
    if "HOT_DEGRADED_BY_MISSING_RELAY" in alert_names:
        extra.append("WATCH_RELAY_RETURN — HOT sans relay, attendre M5 clean")
    if "M5_RELAY_THIN_ALERT" in alert_names:
        extra.append("WATCH_M5_THICKENING — relay thin, surveiller consolidation M5")
    if "COUNTER_RELEASE_ATTEMPT_ALERT" in alert_names:
        extra.append("WATCH_ABSORPTION_OR_REJECTION — counter attempt en cours")
    if "RELEASE_REJECTED_NO_DETACHMENT_ALERT" in alert_names:
        extra.append("WATCH_FIRST_DETACHMENT — pas encore de détachement confirmé")
    if "M1_ACTIVE_M5_WEAK" in alert_names:
        extra.append("WATCH_M5_CONFIRMATION — M1 allumé sans relais tactique")
    if "TIGHT_GRAVITY_CLUSTER_ALERT" in alert_names:
        extra.append("WATCH_GRAVITY_BREAK — cluster serré, surveiller rupture")
    if "NODE_HEAT_ENERGY_DIVERGENCE" in alert_names:
        extra.append("WATCH_ENERGY_ALIGNMENT — divergence Heat/Energy à surveiller")

    seen = set()
    result = []
    for item in base_nw + extra:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Relational Gravity checkers — guard-aware (V0.8.3)
# Signature : (rg: dict) → BehavioralAlert | None
# Règle absolue : jamais de HOT si topline_reliable == False
# Jamais de BUY/SELL. Jamais de DB. Jamais de Telegram direct.
# ---------------------------------------------------------------------------

def _rg_safe(rg: dict) -> tuple[bool, str, str, str, str, bool]:
    """
    Extrait les champs clés du bloc relational_gravity.
    Retourne (is_valid, cross_tf_state, topline_state,
               direction_consistency, leader_consistency, topline_reliable)
    is_valid = False si bloc absent ou malformé → checkers silencieux.
    """
    if not rg or not isinstance(rg, dict):
        return False, "", "", "", "", False
    cross = rg.get("cross_tf_state", "")
    if not cross:
        return False, "", "", "", "", False
    topline_state      = rg.get("topline_state", "")
    dir_cons           = rg.get("direction_consistency", "")
    ldr_cons           = rg.get("leader_consistency", "")
    topline_reliable   = bool(rg.get("topline_reliable", False))
    return True, cross, topline_state, dir_cons, ldr_cons, topline_reliable


def _check_rg_direction_aligned_leader_conflict(rg: dict) -> BehavioralAlert | None:
    """
    RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
    Condition : topline_state = RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT
    Niveau    : WATCH si direction_consistency == ALIGNED, sinon INFO
    Guard     : jamais HOT (topline_reliable est False dans ce cas par définition)
    """
    valid, cross, topline_state, dir_cons, ldr_cons, topline_reliable = _rg_safe(rg)
    if not valid:
        return None
    if topline_state != "RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT":
        return None

    # Guard absolu — ne devrait jamais être True ici, mais on vérifie
    level = "INFO" if topline_reliable else ("WATCH" if dir_cons == "ALIGNED" else "INFO")

    dominant_direction = rg.get("dominant_direction", "UNKNOWN")
    antagonist         = rg.get("dominant_antagonist", "NONE")

    return BehavioralAlert(
        name="RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO",
        level=level,
        reason=(
            f"Direction relationnelle alignée ({dominant_direction}) "
            f"mais leadership conflictuel entre TFs — lire tf_details. "
            f"Antagoniste : {antagonist}."
        ),
        source_fields=[
            "relational_gravity.topline_state",
            "relational_gravity.direction_consistency",
            "relational_gravity.leader_consistency",
            "relational_gravity.tf_details",
        ],
        dashboard_badge="👁 RG DIR/LEAD CONFLICT",
        telegram_text=(
            f"👁 RG DIRECTION ALIGNÉE / LEADER CONFLIT\n"
            f"Direction : {dominant_direction} | Antagoniste : {antagonist}\n"
            f"Lire tf_details — pas de leader fiable"
        ),
    )


def _check_rg_leader_conflict(rg: dict) -> BehavioralAlert | None:
    """
    LEADER_CONFLICT_INFO
    Condition : leader_consistency == CONFLICT ou dominant_leader == MIXED
    Niveau    : INFO
    Guard     : jamais si topline_reliable == True (CONSISTENT = pas de conflit)
                jamais si topline_state == DIRECTION_ALIGNED (déjà couvert ci-dessus)
                jamais si dominant_leader est une devise réelle unique
    """
    valid, cross, topline_state, dir_cons, ldr_cons, topline_reliable = _rg_safe(rg)
    if not valid:
        return None

    # Déjà couvert par le checker précédent
    if topline_state == "RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT":
        return None

    dominant_leader = rg.get("dominant_leader", "")
    ldr_conflict = (ldr_cons == "CONFLICT" or dominant_leader == "MIXED")
    if not ldr_conflict:
        return None

    # topline_reliable True = leader fiable → pas de conflit à signaler
    if topline_reliable:
        return None

    antagonist = rg.get("dominant_antagonist", "NONE")

    return BehavioralAlert(
        name="LEADER_CONFLICT_INFO",
        level="INFO",
        reason=(
            "Relational Gravity leader conflict — "
            f"dominant_leader={dominant_leader!r} | leader_consistency={ldr_cons}. "
            "Pas de topline leader fiable. "
            f"Antagoniste : {antagonist}."
        ),
        source_fields=[
            "relational_gravity.dominant_leader",
            "relational_gravity.leader_consistency",
            "relational_gravity.topline_reliable",
        ],
        dashboard_badge="ℹ RG LEADER CONFLICT",
        telegram_text=(
            f"ℹ RG LEADER CONFLICT\n"
            f"dominant_leader={dominant_leader} | consistency={ldr_cons}\n"
            f"No reliable topline leader"
        ),
    )


def _check_rg_mixed_topline(rg: dict) -> BehavioralAlert | None:
    """
    RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO
    Condition : topline_state in (
        RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE,
        RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT
    )
    Niveau    : INFO
    Guard     : jamais HOT (topline_reliable == False dans ces états)
    """
    valid, cross, topline_state, dir_cons, ldr_cons, topline_reliable = _rg_safe(rg)
    if not valid:
        return None

    _MIXED_STATES = frozenset({
        "RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE",
        "RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
    })
    if topline_state not in _MIXED_STATES:
        return None

    dominant_direction = rg.get("dominant_direction", "UNKNOWN")
    dominant_leader    = rg.get("dominant_leader", "MIXED")
    aligned_tfs        = rg.get("aligned_tfs", [])
    counter_tf         = rg.get("counter_tf")

    counter_note = f" | counter_tf=M{counter_tf}" if counter_tf else ""

    return BehavioralAlert(
        name="RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO",
        level="INFO",
        reason=(
            f"Relational Gravity topline mixed/unreliable — "
            f"topline_state={topline_state} | "
            f"direction={dominant_direction} | "
            f"leader={dominant_leader} | "
            f"aligned_tfs={aligned_tfs}{counter_note}. "
            "Pas de lecture topline fiable."
        ),
        source_fields=[
            "relational_gravity.topline_state",
            "relational_gravity.dominant_direction",
            "relational_gravity.dominant_leader",
            "relational_gravity.aligned_tfs",
        ],
        dashboard_badge="ℹ RG MIXED TOPLINE",
        telegram_text=(
            f"ℹ RG TOPLINE MIXED/UNRELIABLE\n"
            f"{topline_state}\n"
            f"dir={dominant_direction} | leader={dominant_leader}{counter_note}"
        ),
    )


_RG_CHECKERS = [
    _check_rg_direction_aligned_leader_conflict,
    _check_rg_leader_conflict,
    _check_rg_mixed_topline,
]


# ---------------------------------------------------------------------------
# Checkers registry
# ---------------------------------------------------------------------------

_CHECKERS = [
    _check_first_detachment_with_clean_relay,
    _check_hot_degraded_by_missing_relay,
    _check_m5_relay_thin,
    _check_release_rejected_no_detachment,
    _check_counter_release_attempt,
    _check_node_heat_energy_divergence,
    _check_m1_active_m5_weak,
    _check_acceleration_spike_without_zone_tension,
    _check_tight_gravity_cluster,
    _check_same_angle_cluster,
]


# ---------------------------------------------------------------------------
# Point d'entrée public
# ---------------------------------------------------------------------------

def map_behavioral_alerts(
    temporal_node_state: dict,
    currency_energy_state: dict | None = None,
    relational_gravity: dict | None = None,
) -> dict[str, Any]:
    """
    Transforme temporal_node_state + currency_energy_state en alertes comportementales.

    Priorité energy (V0.8.2.1) :
      1. tns.energy_context          si présent et mode != ENERGY_ABSENT
      2. tns.energy_release_alignment si présent (fallback TNS intermédiaire)
      3. currency_energy_state        standalone
      4. Aucune donnée               → checkers energy silencieux

    Relational Gravity (V0.8.3) :
      - relational_gravity : bloc optionnel issu de cockpit_agentic_state["relational_gravity"]
      - Guard-aware : aucune alerte HOT possible depuis RG si topline_reliable == False
      - Si absent → checkers RG silencieux, zéro crash

    Args:
        temporal_node_state: dict issu de pf_temporal_node_state.py
        currency_energy_state: dict issu de pf_currency_energy_probe.py (optionnel)
        relational_gravity: dict issu de pf_relational_gravity_bridge.py (optionnel)

    Returns:
        dict avec behavioral_alerts, degraded_alerts, next_watch_enriched, film_steps
    """
    tns = temporal_node_state or {}
    standalone = currency_energy_state or {}
    rg = relational_gravity or {}

    ev = _resolve_energy(tns, standalone)

    behavioral: list[BehavioralAlert] = []
    degraded: list[BehavioralAlert] = []

    for checker in _CHECKERS:
        try:
            result = checker(tns, ev)
        except Exception:
            continue

        if result is None:
            continue

        if result.level == "DEGRADED":
            degraded.append(result)
        else:
            behavioral.append(result)

    # ── Relational Gravity checkers — guard-aware (V0.8.3) ──────
    # topline_reliable == False → aucune alerte HOT depuis RG
    for rg_checker in _RG_CHECKERS:
        try:
            result = rg_checker(rg)
        except Exception:
            continue
        if result is None:
            continue
        if result.level == "DEGRADED":
            degraded.append(result)
        else:
            behavioral.append(result)
    # ─────────────────────────────────────────────────────────────

    film_steps = _build_film_steps(tns, ev)
    next_watch = _build_next_watch(tns, behavioral + degraded)

    output = MapperOutput(
        behavioral_alerts=[a.to_dict() for a in behavioral],
        degraded_alerts=[a.to_dict() for a in degraded],
        next_watch_enriched=next_watch,
        film_steps=film_steps,
    )
    return output.to_dict()
