import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_v76_telegram_cycle_once import build_packet_from_evidence


class V76TelegramCycleOnceTest(unittest.TestCase):
    def test_build_packet_from_legacy_evidence(self):
        evidence = {
            "symbol": "GBPUSD",
            "state": "ELASTIC_RELEASE_WITH_TEMPORAL_BREAK",
            "status": "ACTIVE",
            "bias": "PAIR_DOWN",
            "generated_at": "2026-05-14T15:12:01.795464+00:00",
            "recent_events": [
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
        context, packet, memory = build_packet_from_evidence(evidence, symbol="GBPUSD", memory_cards=[])
        self.assertEqual(context["symbol"], "GBPUSD")
        self.assertEqual(packet["raw_bias"], "PAIR_DOWN")
        self.assertNotEqual(packet["qualified_bias"], "HONEST_UNKNOWN")
        self.assertIn(packet["price_confirmation"], {"PRICE_REJECTED_HIGH", "PRICE_PENDING"})


if __name__ == "__main__":
    unittest.main()

