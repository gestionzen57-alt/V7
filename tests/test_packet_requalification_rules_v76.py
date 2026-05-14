import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_packet_requalification_once import requalify_packet
from pf_terrain_context_once import build_terrain_context
from pf_film_memory_reader_once import match_film_context


class PacketRequalificationRulesV76Test(unittest.TestCase):
    def test_b3_b2_not_release(self):
        packet = requalify_packet({"symbol": "GBPUSD", "b3_active": True, "b2_active": True, "raw_bias": "B3_B2"})
        self.assertEqual(packet["qualified_bias"], "EVENT_STACK")
        self.assertEqual(packet["packet_quality"], "EVENT_STACK_NOT_RELEASE")
        self.assertNotEqual(packet["qualified_bias"], "RELEASE_VALIDATED")

    def test_b3_b4_p1_candidate(self):
        packet = requalify_packet({"symbol": "GBPUSD", "raw_bias": "B3_B4_P1", "b3_active": True, "b4_active": True, "p1_active": True, "price_confirmation": "PRICE_PENDING"})
        self.assertEqual(packet["qualified_bias"], "RELEASE_CANDIDATE")
        self.assertEqual(packet["packet_quality"], "CANDIDATE_NOT_VALIDATED")

    def test_release_candidate_price_accepted_validated(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "B3_B4_P1",
            "b3_active": True,
            "b4_active": True,
            "p1_active": True,
            "price_confirmation": "PRICE_ACCEPTED_ABOVE_ZONE",
            "propagation_state": "LTF_MTF_RELAY",
            "data_visibility": "FULL_READING",
        })
        self.assertEqual(packet["qualified_bias"], "RELEASE_VALIDATED")
        self.assertEqual(packet["price_confirmation"], "PRICE_CONFIRMED")

    def test_pair_up_after_release_down_counter_breath(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "PAIR_UP",
            "last_structural_event": "RELEASE_DOWN_VALIDATED",
            "current_zone_status": "LOWER_ZONE_ACTIVE",
            "price_confirmation": "PRICE_PENDING",
        })
        self.assertEqual(packet["qualified_bias"], "POST_RELEASE_COUNTER_BREATH")
        self.assertEqual(packet["packet_quality"], "REACTION_NOT_RELEASE")

    def test_pair_down_after_high_rejection_post_high_unwind(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "PAIR_DOWN",
            "last_structural_event": "HIGH_ZONE_REJECTION",
            "price_confirmation": "PRICE_REJECTED_HIGH",
        })
        self.assertEqual(packet["qualified_bias"], "POST_HIGH_UNWIND")
        self.assertEqual(packet["packet_quality"], "STRUCTURAL_REACTION")

    def test_hot_without_price_pressure_pending(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "HOT",
            "no_price_displacement": True,
        })
        self.assertEqual(packet["qualified_bias"], "PRESSURE_PENDING")
        self.assertEqual(packet["price_confirmation"], "PRICE_PENDING")

    def test_stale_packets_reading_partial(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "WATCH",
            "packets_stale": True,
        })
        self.assertEqual(packet["data_visibility"], "PACKETS_STALE")
        self.assertEqual(packet["qualified_bias"], "READING_PARTIAL")
        self.assertIn("PACKETS_STALE", packet["technical_risks"])

    def test_b8_degraded_honest_unknown(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "WATCH",
            "b8_degraded": True,
        })
        self.assertEqual(packet["data_visibility"], "B8_DEGRADED")
        self.assertEqual(packet["qualified_bias"], "HONEST_UNKNOWN")
        self.assertIn("B8_DEGRADED", packet["technical_risks"])

    def test_2026_05_14_example(self):
        example_path = ROOT / "schema" / "terrain_packet_examples" / "gbpusd_20260514_lower_zone_partial.json"
        with open(example_path, "r", encoding="utf-8") as handle:
            example = json.load(handle)
        self.assertEqual(example["symbol"], "GBPUSD")
        self.assertEqual(example["film_state"], "LOWER_ZONE_ACTIVE")
        self.assertEqual(example["last_structural_event"], "COUNTER_BREATH_REJECTED")
        self.assertEqual(example["current_zone_low"], 1.3504)
        self.assertEqual(example["current_zone_high"], 1.3532)
        self.assertEqual(example["raw_bias"], "PAIR_UP")
        self.assertEqual(example["qualified_bias"], "POST_LOW_COUNTER_BREATH")
        self.assertEqual(example["packet_quality"], "REACTION_NOT_RELEASE")
        self.assertEqual(example["price_confirmation"], "PRICE_PENDING")
        self.assertEqual(example["propagation_state"], "LTF_ONLY")
        self.assertEqual(example["detachment_texture"], "COUNTER_BREATH_DETACHMENT")
        self.assertIn(example["data_visibility"], {"M1_MISSING_PACKETS_STALE", "READING_PARTIAL"})

    def test_context_builder_fallback(self):
        context = build_terrain_context({"symbol": "GBPUSD", "bias": "PAIR_UP", "m1_available": False})
        self.assertEqual(context["raw_bias"], "PAIR_UP")
        self.assertEqual(context["data_visibility"], "M1_MISSING")

    def test_film_memory_reader_does_not_decide(self):
        context = {"film_state": "LOWER_ZONE_ACTIVE", "last_structural_event": "COUNTER_BREATH_REJECTED", "raw_bias": "PAIR_UP"}
        memory = [{
            "name": "LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL",
            "film_state": "LOWER_ZONE_ACTIVE",
            "last_structural_event": "COUNTER_BREATH_REJECTED",
            "raw_bias": "PAIR_UP",
            "expected_next_behavior": "LOW_RETEST_OR_POST_LOW_REACTION",
            "false_positive_risk": "READING_PARTIAL_CAN_OVERSTATE_COUNTER_BREATH",
        }]
        match = match_film_context(context, memory)
        self.assertGreater(match["memory_confidence"], 0.0)
        self.assertEqual(match["memory_effect"], "LIMIT_WITH_FALSE_POSITIVE_RISK")
        self.assertNotIn("qualified_bias", match)


class TestV76CanonicalAliases(unittest.TestCase):
    def test_zone_status_alias_is_canonicalized(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "PAIR_UP",
            "current_zone_status": "LOWER_ZONE_ACTIVE",
            "film_state": "LOWER_ZONE_RANGE_ACTIVE",
            "last_structural_event": "COUNTER_BREATH_REJECTED",
        })
        self.assertEqual(packet["current_zone_status"], "LOWER_RANGE_ACTIVE")

    def test_legacy_data_visibility_alias_is_canonicalized(self):
        packet = requalify_packet({
            "symbol": "GBPUSD",
            "raw_bias": "WATCH",
            "data_visibility": "DATA_PARTIAL",
        })
        self.assertEqual(packet["data_visibility"], "READING_PARTIAL")
        self.assertEqual(packet["qualified_bias"], "READING_PARTIAL")

if __name__ == "__main__":
    unittest.main()
