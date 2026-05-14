import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_trader_labels_fr_once import format_terrain_packet_fr, load_labels


class TraderLabelsFrV76Test(unittest.TestCase):
    def test_format_packet_in_french(self):
        labels = load_labels(ROOT / "schema" / "terrain_packet_labels_fr_v76.json")
        packet = {
            "symbol": "GBPUSD",
            "film_state": "HIGH_ZONE_REJECTION",
            "last_structural_event": "HIGH_ZONE_REJECTION",
            "current_zone": "1.34840-1.34977",
            "current_zone_status": "REJECTION_HIGH",
            "current_move_role": "POST_HIGH_UNWIND",
            "raw_bias": "PAIR_DOWN",
            "qualified_bias": "POST_HIGH_UNWIND",
            "packet_quality": "STRUCTURAL_REACTION",
            "price_confirmation": "PRICE_REJECTED_HIGH",
            "propagation_state": "LTF_MTF_RELAY",
            "detachment_texture": "REJECTION_DETACHMENT",
            "data_visibility": "READING_PARTIAL",
            "technical_risks": ["EVENT_TIME_OFFSET"],
            "watch_condition": "price_acceptance_or_rejection_follow_through",
            "invalidation_condition": "opposite_price_acceptance_or_failed_follow_through",
        }
        text = format_terrain_packet_fr(packet, labels)
        self.assertIn("GBPUSD — Rejet de zone haute", text)
        self.assertIn("Signal brut baissier", text)
        self.assertIn("Déroulement baissier après rejet haut", text)
        self.assertIn("Prix rejeté en haut", text)
        self.assertIn("Lecture partielle", text)


if __name__ == "__main__":
    unittest.main()

