# -*- coding: utf-8 -*-
"""PowerFlow V7.6.7 B9 engine orchestrator.

This module wires already validated upstream B9 organs into one window-level
pipeline. It does not create new upstream perception logic; it only sequences
visibility, false-birth guard, zone context, price verdict, terrain node snapshot,
packet requalification, and optional Telegram transmission.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict

from pf_data_visibility_guard import check_data_visibility
from pf_false_birth_filter import is_false_birth
from pf_zone_context_reader import read_zone_context
from pf_price_verdict import PricePath, ZoneBounds, compute_price_verdict
from pf_terrain_node_snapshot import create_terrain_node_snapshot
from pf_packet_requalifier_v767 import requalify_packet
from telegram_alert_sender_b9 import send_b9_alert


class PowerFlowEngineB9:
    """B9 orchestration layer.

    Config example:
        {"ENABLE_TELEGRAM": False}
    """

    def __init__(self, config: dict):
        self.config = dict(config or {})

    def process_window(self, window: dict) -> dict:
        """Run the complete B9 pipeline on a prepared window.

        Args:
            window: A dictionary containing symbol, timestamp, zone bounds,
                price path, raw packet bias/strength, and previous scene state.

        Returns:
            A status dictionary with the created node, requalified packet, and
            Telegram emission status.
        """
        if not isinstance(window, dict):
            raise TypeError("window must be a dict")

        symbol = window.get("symbol", "UNKNOWN")
        timestamp = window.get("timestamp")

        visibility = _normalise_dict(check_data_visibility(window))

        if is_false_birth(window):
            return {
                "status": "FALSE_BIRTH",
                "symbol": symbol,
                "node": None,
                "requalified": None,
                "alert_sent": False,
            }

        zone_context = _read_zone_context(window)
        price_verdict = _compute_price_verdict(window)
        node = _create_node_snapshot(window, visibility, zone_context, price_verdict)

        raw_packet = {
            "symbol": symbol,
            "timestamp": timestamp,
            "raw_bias": window.get("raw_bias", "UNKNOWN"),
            "packet_strength": float(window.get("packet_strength", 0.0) or 0.0),
        }

        previous_scene_state = _normalise_dict(window.get("previous_scene_state", {}))

        requalified = _normalise_dict(
            requalify_packet(
                raw_packet=raw_packet,
                zone_context=zone_context,
                price_verdict=price_verdict,
                previous_scene_state=previous_scene_state,
                data_visibility=visibility,
            )
        )

        should_alert = self._should_alert(requalified, visibility)
        alert_sent = False
        if should_alert:
            send_b9_alert(node, requalified, self.config)
            alert_sent = True

        return {
            "status": "NODE_CREATED",
            "symbol": symbol,
            "node": node,
            "requalified": requalified,
            "alert_sent": alert_sent,
        }

    def _should_alert(self, requalified: dict, visibility: dict) -> bool:
        """B9 alert rule: alert fast, qualify after.

        The only hard stop is DO_NOT_EMIT. Telegram must also be enabled in the
        runtime config. Reading-partial packets are still allowed when the
        requalification is strong enough.
        """
        if visibility.get("node_status") == "DO_NOT_EMIT":
            return False

        if not self.config.get("ENABLE_TELEGRAM", False):
            return False

        data_vis = visibility.get("data_visibility", "READING_PARTIAL")

        if data_vis == "TACTICAL_OK":
            return True
        if data_vis == "RECONSTRUCTED":
            return True
        if data_vis == "READING_PARTIAL":
            return float(requalified.get("requalified_confidence", 0.0) or 0.0) >= 0.6

        return False


def _normalise_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return dict(value.to_dict())
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _read_zone_context(window: dict) -> Dict[str, Any]:
    """Call the validated zone reader while tolerating signature drift."""
    try:
        return _normalise_dict(read_zone_context(window))
    except TypeError:
        pass

    try:
        return _normalise_dict(
            read_zone_context(
                symbol=window.get("symbol"),
                timestamp=window.get("timestamp"),
                zone_low=window.get("zone_low"),
                zone_high=window.get("zone_high"),
                current_price=window.get("current_price"),
                zone_touch_history=window.get("zone_touch_history", []),
                zone_bars_since_touch=window.get("zone_bars_since_touch", 0),
            )
        )
    except TypeError:
        return _normalise_dict(
            read_zone_context(
                window.get("symbol"),
                window.get("timestamp"),
                window.get("zone_low"),
                window.get("zone_high"),
                window.get("current_price"),
                window.get("zone_touch_history", []),
                window.get("zone_bars_since_touch", 0),
            )
        )


def _compute_price_verdict(window: dict) -> Dict[str, Any]:
    price_path = _build_price_path(window.get("price_path", {}))
    zone_bounds = _build_zone_bounds(window)

    try:
        verdict = compute_price_verdict(price_path, zone_bounds)
    except TypeError:
        verdict = compute_price_verdict(price_path=price_path, zone_bounds=zone_bounds)

    result = _normalise_dict(verdict)
    if "verdict" not in result and "price_verdict" in result:
        result["verdict"] = result["price_verdict"]
    result.setdefault("verdict", "INCONCLUSIVE")
    result.setdefault("confidence", 0.0)
    return result


def _build_price_path(payload: Any) -> Any:
    if isinstance(payload, PricePath):
        return payload
    if not isinstance(payload, dict):
        payload = {"values": payload}

    try:
        return PricePath(**payload)
    except TypeError:
        pass

    for key in ("prices", "path", "values"):
        if key in payload:
            try:
                return PricePath(payload[key])
            except TypeError:
                continue

    return PricePath(payload)


def _build_zone_bounds(window: dict) -> Any:
    low = window.get("zone_low")
    high = window.get("zone_high")

    constructors = (
        {"zone_low": low, "zone_high": high},
        {"low": low, "high": high},
    )
    for kwargs in constructors:
        try:
            return ZoneBounds(**kwargs)
        except TypeError:
            continue

    return ZoneBounds(low, high)


def _create_node_snapshot(
    window: dict,
    visibility: Dict[str, Any],
    zone_context: Dict[str, Any],
    price_verdict: Dict[str, Any],
) -> Dict[str, Any]:
    """Create terrain node snapshot through validated upstream adapter."""
    try:
        node = create_terrain_node_snapshot(
            window=window,
            visibility=visibility,
            zone_context=zone_context,
            price_verdict=price_verdict,
        )
    except TypeError:
        try:
            node = create_terrain_node_snapshot(window, visibility, zone_context, price_verdict)
        except TypeError:
            node = create_terrain_node_snapshot(
                symbol=window.get("symbol"),
                timestamp=window.get("timestamp"),
                zone_low=window.get("zone_low"),
                zone_high=window.get("zone_high"),
                current_price=window.get("current_price"),
                visibility=visibility,
                zone_context=zone_context,
                price_verdict=price_verdict,
            )

    return _normalise_dict(node)
