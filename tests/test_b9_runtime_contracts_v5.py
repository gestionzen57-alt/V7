# -*- coding: utf-8 -*-
from pathlib import Path


def test_contract_facades_importable():
    from pf_terrain_node_snapshot import create_terrain_node_snapshot
    from pf_packet_requalifier_v767 import requalify_packet, requalify_terrain_packet
    from pf_b6_field_memory_reader import read_b6_field_memory
    from telegram_alert_sender_b9 import send_b9_alert
    assert callable(create_terrain_node_snapshot)
    assert callable(requalify_packet)
    assert callable(requalify_terrain_packet)
    assert callable(read_b6_field_memory)
    assert callable(send_b9_alert)


def test_create_terrain_node_snapshot_accepts_engine_keywords():
    from pf_terrain_node_snapshot import create_terrain_node_snapshot
    node = create_terrain_node_snapshot(
        symbol="GBPUSD",
        zone_low=1.27,
        zone_high=1.275,
        current_price=1.272,
        data_visibility="TACTICAL_OK",
        price_verdict_candidate="PENDING",
    )
    assert isinstance(node, dict)
    assert node["symbol"] == "GBPUSD"
    assert "zone_bounds" in node
    assert "data_visibility" in node


def test_requalifier_and_memory_facades_return_packets():
    from pf_packet_requalifier_v767 import requalify_packet
    from pf_b6_field_memory_reader import read_b6_field_memory
    packet = requalify_packet(packet={"symbol": "GBPUSD"})
    memory = read_b6_field_memory(symbol="GBPUSD")
    assert isinstance(packet, dict)
    assert isinstance(memory, dict)
    assert "limits" in packet
    assert "limits" in memory


def test_telegram_facade_dry_run_default():
    from telegram_alert_sender_b9 import send_b9_alert
    result = send_b9_alert({"symbol": "GBPUSD"})
    assert result.get("alert_sent") is False


def test_pf_engine_b9_imports_after_contract_facades():
    from pf_engine_b9 import PowerFlowEngineB9
    assert PowerFlowEngineB9 is not None


def test_injected_facades_have_no_forbidden_runtime_words():
    files = [
        Path("pf_terrain_node_snapshot.py"),
        Path("pf_packet_requalifier_v767.py"),
        Path("pf_b6_field_memory_reader.py"),
        Path("telegram_alert_sender_b9.py"),
    ]
    forbidden = ["buy", "sell", "achat", "vente", "entry", "target", "stop loss"]
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        idx = text.find("b9_runtime_contract_compat_v5")
        if idx >= 0:
            injected = text[idx:]
            assert not any(word in injected for word in forbidden)
