import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_telegram_qualified_alert_once import should_alert, packet_fingerprint, build_message


class TelegramQualifiedAlertV76Test(unittest.TestCase):
    def test_alert_on_qualified_structural_packet(self):
        packet = {
            "symbol": "GBPUSD",
            "film_state": "HIGH_ZONE_REJECTION",
            "raw_bias": "PAIR_DOWN",
            "qualified_bias": "POST_HIGH_UNWIND",
            "packet_quality": "STRUCTURAL_REACTION",
            "price_confirmation": "PRICE_REJECTED_HIGH",
            "data_visibility": "READING_PARTIAL",
            "technical_risks": ["EVENT_TIME_OFFSET"],
        }
        ok, reason = should_alert(packet, {}, cooldown_seconds=900)
        self.assertTrue(ok, reason)

    def test_no_alert_on_honest_unknown(self):
        packet = {
            "symbol": "GBPUSD",
            "film_state": "UNKNOWN",
            "raw_bias": "PAIR_DOWN",
            "qualified_bias": "HONEST_UNKNOWN",
            "packet_quality": "HONEST_UNKNOWN",
            "price_confirmation": "UNKNOWN",
            "data_visibility": "FULL_READING",
        }
        ok, _ = should_alert(packet, {}, cooldown_seconds=900)
        self.assertFalse(ok)

    def test_cooldown_blocks_duplicate(self):
        packet = {
            "symbol": "GBPUSD",
            "film_state": "HIGH_ZONE_REJECTION",
            "raw_bias": "PAIR_DOWN",
            "qualified_bias": "POST_HIGH_UNWIND",
            "packet_quality": "STRUCTURAL_REACTION",
            "price_confirmation": "PRICE_REJECTED_HIGH",
            "data_visibility": "READING_PARTIAL",
        }
        fp = packet_fingerprint(packet)
        ok, _ = should_alert(packet, {fp: 9999999999}, cooldown_seconds=900)
        self.assertFalse(ok)

    def test_message_contains_guardrail(self):
        packet = {
            "symbol": "GBPUSD",
            "qualified_bias": "POST_HIGH_UNWIND",
            "price_confirmation": "PRICE_REJECTED_HIGH",
            "data_visibility": "READING_PARTIAL",
        }
        msg = build_message(packet, "GBPUSD — Rejet de zone haute")
        self.assertIn("alerte qualifiée", msg)
        self.assertIn("pas ordre automatique", msg)


if __name__ == "__main__":
    unittest.main()

