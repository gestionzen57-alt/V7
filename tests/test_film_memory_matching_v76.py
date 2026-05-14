# -*- coding: utf-8 -*-
"""
Tests PowerFlow V7.6 — B6 Film Memory GBPUSD.

Ces tests valident le matching explicable sur les 7 films GBPUSD calibrés.
Ils n'ont pas besoin de powerflow.db.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
READER_PATH = REPO_ROOT / "patch" / "pf_film_memory_reader_once.py"
CARDS_PATH = REPO_ROOT / "data" / "film_memory" / "gbpusd_v76_film_memory_cards.json"


def load_reader():
    spec = importlib.util.spec_from_file_location("pf_film_memory_reader_once", READER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_cards():
    with CARDS_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def packet_from_card(card):
    expected = card["expected"]
    return {
        "symbol": "GBPUSD",
        "film_state": expected["film_state"][0],
        "last_structural_event": expected["last_structural_event"][0],
        "qualified_bias": expected["qualified_bias"][0],
        "price_confirmation": expected["price_confirmation"][0],
        "propagation_state": expected["propagation_state"][0],
        "detachment_texture": expected["detachment_texture"][0],
        "data_visibility": expected["data_visibility"][0],
    }


def test_7_calibrated_films_match_themselves():
    reader = load_reader()
    cards_payload = load_cards()

    failures = []
    for card in cards_payload["cards"]:
        packet = packet_from_card(card)
        result = reader.match_memory(packet, cards_payload, symbol="GBPUSD", top_n=3)
        if result["memory_match"] != card["film_id"] or result["memory_confidence"] < 0.78:
            failures.append({
                "day": card["day"],
                "expected": card["film_id"],
                "got": result["memory_match"],
                "confidence": result["memory_confidence"],
                "reason": result["memory_reason_fr"],
            })

    assert not failures, failures


def test_20260514_reading_partial_recognized_even_with_unknowns():
    reader = load_reader()
    cards_payload = load_cards()

    packet = {
        "symbol": "GBPUSD",
        "film_state": "READING_PARTIAL",
        "last_structural_event": "UNKNOWN",
        "qualified_bias": "POST_LOW_REACTION",
        "price_confirmation": "PENDING",
        "propagation_state": "UNKNOWN",
        "detachment_texture": "UNKNOWN",
        "data_visibility": "PACKETS_STALE",
    }
    result = reader.match_memory(packet, cards_payload, symbol="GBPUSD", top_n=3)

    assert result["memory_match"] == "LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL"
    assert result["memory_confidence"] >= 0.35
    assert "Confidence" in result["memory_reason_fr"] or "Mémoire B6" in result["memory_reason_fr"]


def test_non_gbpusd_scope_is_rejected_explainably():
    reader = load_reader()
    cards_payload = load_cards()

    packet = {
        "symbol": "EURUSD",
        "film_state": "LOWER_ZONE_ACTIVE",
        "last_structural_event": "RELEASE_DOWN_VALIDATED",
        "qualified_bias": "RELEASE_DOWN_VALIDATED",
        "price_confirmation": "CONFIRMED",
        "propagation_state": "LTF_MTF_RELAY",
        "detachment_texture": "STRUCTURAL_DETACHMENT",
        "data_visibility": "TACTICAL_OK",
    }
    result = reader.match_memory(packet, cards_payload, symbol="EURUSD", top_n=3)

    assert result["memory_match"] == "UNKNOWN"
    assert result["memory_confidence"] == 0.0
    assert "GBPUSD only" in result["memory_reason_fr"]


def test_real_terrain_packet_if_present():
    """
    Non bloquant: si le terrain_packet réel existe dans le repo, vérifier que le reader
    retourne les champs attendus. Sinon le test est neutre.
    """
    terrain_packet = REPO_ROOT / "output" / "dashboard_surface" / "GBPUSD" / "terrain_packet.json"
    if not terrain_packet.exists():
        return

    reader = load_reader()
    cards_payload = load_cards()
    packet = json.loads(terrain_packet.read_text(encoding="utf-8"))
    result = reader.match_memory(packet, cards_payload, symbol="GBPUSD", top_n=3)

    assert "memory_match" in result
    assert "memory_confidence" in result
    assert "memory_reason_fr" in result
    assert "similar_historical_days" in result

