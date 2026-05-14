# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_trader_playbook_once import build_playbook


class TraderPlaybookSmokeV76Test(unittest.TestCase):
    def test_high_zone_exhaustion_playbook_is_non_executing(self):
        packet = {
            "symbol": "GBPUSD",
            "qualified_bias": "HIGH_ZONE_EXHAUSTION_RISK",
            "film_state": "HIGH_ZONE_REJECTION",
            "price_confirmation": "PRICE_REJECTED_LOW",
            "data_visibility": "READING_PARTIAL",
            "packet_quality": "EXHAUSTION_RISK",
            "technical_risks": ["EVENT_TIME_OFFSET"],
        }
        out = build_playbook(packet)
        self.assertEqual(out["playbook_state"], "HIGH_ZONE_EXHAUSTION_RISK")
        self.assertTrue(out["do_not_execute"])
        self.assertTrue(out["trader_decides"])
        self.assertIn("Risque", out["playbook_label_fr"])
        self.assertIn("Lecture partielle", out["no_trade_warning_fr"])

    def test_post_high_unwind_playbook_is_not_order(self):
        packet = {
            "symbol": "GBPUSD",
            "qualified_bias": "POST_HIGH_UNWIND",
            "film_state": "HIGH_ZONE_REJECTION",
            "price_confirmation": "PRICE_REJECTED_HIGH",
            "data_visibility": "FULL_READING",
            "packet_quality": "STRUCTURAL_REACTION",
        }
        out = build_playbook(packet)
        text = str(out).upper()
        for forbidden in ("BUY", "SELL", "ENTRY", "EXIT", "TARGET", "STOP"):
            self.assertNotIn(forbidden, text)
        self.assertEqual(out["playbook_state"], "POST_HIGH_UNWIND")


if __name__ == "__main__":
    unittest.main()

