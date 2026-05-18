from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_terrain_node_builder import build_nodes, summarize_nodes, REQUIRED_NODE_FIELDS
from tools.build_t0142_b9_terrain_node_builder import load_json, run


def test_t0142_builds_required_nodes(tmp_path):
    sample = ROOT / "samples" / "b9_terrain_node_builder_v0" / "sample_t009_sequence_summary_terrain_nodes.json"
    manifest = run(sample, tmp_path)
    assert manifest["node_count"] == 6
    assert manifest["missing_required_field_counts"] == {}
    assert manifest["forbidden_language_hit_count"] == 0
    assert (tmp_path / "B9_TERRAIN_NODE_BUILDER_V0.zip").exists()


def test_t0142_infers_core_node_roles():
    sample = ROOT / "samples" / "b9_terrain_node_builder_v0" / "sample_t009_sequence_summary_terrain_nodes.json"
    summary = load_json(sample)
    nodes = build_nodes(summary)
    roles = {node["node_role"] for node in nodes}
    assert "RETEST_FAILED_NODE" in roles
    assert "FAILED_REINTEGRATION_NODE" in roles
    assert "LOWER_ZONE_DEFENDED_NODE" in roles
    assert "RAW_UNAVAILABLE_NODE_REJECTED" in roles
    result = summarize_nodes(nodes)
    assert result["forbidden_language_hits"] == []
    for node in nodes:
        for field in REQUIRED_NODE_FIELDS:
            assert node.get(field) not in (None, "")
