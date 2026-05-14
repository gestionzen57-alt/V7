# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_film_memory_reader_once import load_film_memory, match_film_context


class B6MemorySmokeV76Test(unittest.TestCase):
    def test_current_exhaustion_packet_matches_known_film(self):
        cards = load_film_memory(ROOT / "data" / "film_memory" / "gbpusd_v76_film_memory_cards.json")
        packet = {
            "symbol": "GBPUSD",
            "film_state": "HIGH_ZONE_REJECTION",
            "last_structural_event": "HIGH_ZONE_REJECTION",
            "qualified_bias": "HIGH_ZONE_EXHAUSTION_RISK",
            "price_confirmation": "PRICE_REJECTED_LOW",
            "propagation_state": "LTF_MTF_RELAY",
            "detachment_texture": "REJECTION_DETACHMENT",
            "data_visibility": "READING_PARTIAL",
        }
        result = match_film_context(packet, cards)
        self.assertNotEqual(result["memory_match"], "UNKNOWN")
        self.assertGreaterEqual(result["memory_confidence"], 0.35)
        self.assertIn("memory_reason_fr", result)
        self.assertTrue(result.get("similar_historical_days"))

    def test_legacy_cycle_api_still_exists(self):
        cards = load_film_memory(ROOT / "data" / "film_memory" / "gbpusd_v76_film_memory_cards.json")
        self.assertIsInstance(cards, dict)
        self.assertIn("cards", cards)


if __name__ == "__main__":
    unittest.main()

