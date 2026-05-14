import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_terrain_context_once import build_terrain_context
from pf_packet_requalification_once import requalify_packet


class LegacyEvidenceAdapterV76Test(unittest.TestCase):
    def test_legacy_behavioral_state_enriches_terrain_context(self):
        evidence = {
            "symbol": "GBPUSD",
            "state": "ELASTIC_RELEASE_WITH_TEMPORAL_BREAK",
            "status": "ACTIVE",
            "bias": "PAIR_DOWN",
            "generated_at": "2026-05-14T15:12:01.795464+00:00",
            "latest_event": {
                "symbol": "GBPUSD",
                "event": "COMPRESSION",
                "event_role": "ELASTIC_LOADING_LEGACY",
                "bias": "PAIR_DOWN",
                "price": "1.34838",
                "timeframe": "1",
                "detected_at": "2026-05-14T15:07:13.297392+00:00",
                "event_at": "2026-05-14T18:07:05+00:00",
            },
            "recent_events": [
                {
                    "symbol": "GBPUSD",
                    "event": "EXTREME_HIGH",
                    "event_role": "ZONE_PRESSURE_HIGH",
                    "bias": "PAIR_DOWN",
                    "price": "1.34977",
                    "timeframe": "1",
                    "detected_at": "2026-05-14T14:53:07.283850+00:00",
                    "event_at": "2026-05-14T17:53:01+00:00",
                },
                {
                    "symbol": "GBPUSD",
                    "event": "KISS_REJECT",
                    "event_role": "ZONE_REPULSION",
                    "bias": "PAIR_DOWN",
                    "price": "1.3484",
                    "timeframe": "5",
                    "detected_at": "2026-05-14T15:00:09.125539+00:00",
                    "event_at": "2026-05-14T18:00:03+00:00",
                },
                {
                    "symbol": "GBPUSD",
                    "event": "EXTREME_HIGH",
                    "event_role": "ZONE_PRESSURE_HIGH",
                    "bias": "PAIR_DOWN",
                    "price": "1.3484",
                    "timeframe": "15",
                    "detected_at": "2026-05-14T15:00:09.219728+00:00",
                    "event_at": "2026-05-14T18:00:03+00:00",
                },
            ],
        }

        context = build_terrain_context(evidence)
        self.assertEqual(context["symbol"], "GBPUSD")
        self.assertEqual(context["raw_bias"], "PAIR_DOWN")
        self.assertEqual(context["last_structural_event"], "COUNTER_BREATH_REJECTED")
        self.assertEqual(context["film_state"], "LOWER_ZONE_ACTIVE")
        self.assertEqual(context["current_zone_status"], "REJECTION_HIGH")
        self.assertEqual(context["price_confirmation"], "PRICE_REJECTED_HIGH")
        self.assertEqual(context["propagation_state"], "LTF_MTF_RELAY")
        self.assertEqual(context["detachment_texture"], "REJECTION_DETACHMENT")
        self.assertEqual(context["data_visibility"], "READING_PARTIAL")
        self.assertIn("EVENT_TIME_OFFSET", context["technical_risks"])

        packet = requalify_packet(context)
        self.assertIn(
            packet["qualified_bias"],
            {"SECOND_LEG_DOWN", "POST_HIGH_UNWIND"},
        )
        self.assertNotEqual(packet["packet_quality"], "HONEST_UNKNOWN")


if __name__ == "__main__":
    unittest.main()

