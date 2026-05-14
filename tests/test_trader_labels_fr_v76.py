import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_trader_labels_fr_once import (  # noqa: E402
    format_terrain_packet_fr,
    label_condition,
    load_labels,
)


class TraderLabelsFrV76Test(unittest.TestCase):
    def setUp(self):
        self.labels = load_labels(ROOT / "schema" / "terrain_packet_labels_fr_v76.json")

    def _base_packet(self):
        return {
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
            "watch_condition": "WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION",
            "invalidation_condition": "HIGH_REJECTION_OR_UNWIND",
        }

    def test_format_packet_in_french(self):
        text = format_terrain_packet_fr(self._base_packet(), self.labels)

        self.assertIn("GBPUSD — Rejet de zone haute", text)
        self.assertIn("Signal brut baissier", text)
        self.assertIn("Déroulement baissier après rejet haut", text)
        self.assertIn("Prix rejeté en haut", text)
        self.assertIn("Lecture partielle", text)

    def test_watch_condition_enum_is_translated_for_telegram(self):
        text = format_terrain_packet_fr(self._base_packet(), self.labels)

        self.assertIn(
            "À surveiller : vraie acceptation prix, pas extension tardive.",
            text,
        )
        self.assertNotIn("WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION", text)

    def test_invalidation_condition_enum_is_translated_for_telegram(self):
        text = format_terrain_packet_fr(self._base_packet(), self.labels)

        self.assertIn(
            "Invalidation : rejet haut confirmé ou déroulement inverse.",
            text,
        )
        self.assertNotIn("HIGH_REJECTION_OR_UNWIND", text)

    def test_legacy_lowercase_conditions_are_translated(self):
        packet = self._base_packet()
        packet["watch_condition"] = "price_acceptance_or_rejection_follow_through"
        packet["invalidation_condition"] = "opposite_price_acceptance_or_failed_follow_through"

        text = format_terrain_packet_fr(packet, self.labels)

        self.assertIn("À surveiller : suite d’acceptation ou de rejet prix.", text)
        self.assertIn("Invalidation : acceptation prix opposée ou suivi échoué.", text)
        self.assertNotIn("price_acceptance_or_rejection_follow_through", text)
        self.assertNotIn("opposite_price_acceptance_or_failed_follow_through", text)

    def test_unknown_watch_condition_has_clean_fallback(self):
        rendered = label_condition(
            "WATCH_FOR_PULLBACK_CONFIRMATION",
            self.labels,
            kind="watch",
        )

        self.assertEqual(
            rendered,
            "condition à surveiller non traduite : pullback confirmation.",
        )
        self.assertNotIn("WATCH_FOR_PULLBACK_CONFIRMATION", rendered)
        self.assertNotIn("_", rendered)

    def test_unknown_invalidation_condition_has_clean_fallback(self):
        rendered = label_condition(
            "INVALIDATION_PRICE_REENTERS_OLD_ZONE",
            self.labels,
            kind="invalidation",
        )

        self.assertEqual(
            rendered,
            "condition d'invalidation non traduite : price reenters old zone.",
        )
        self.assertNotIn("INVALIDATION_PRICE_REENTERS_OLD_ZONE", rendered)
        self.assertNotIn("_", rendered)

    def test_condition_list_is_supported(self):
        rendered = label_condition(
            [
                "WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION",
                "WATCH_FOR_COUNTER_BREATH_REJECTION",
            ],
            self.labels,
            kind="watch",
        )

        self.assertEqual(
            rendered,
            "vraie acceptation prix, pas extension tardive ; rejet du contre-souffle.",
        )


if __name__ == "__main__":
    unittest.main()

