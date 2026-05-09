from pathlib import Path

p = Path("pf_relational_gravity_bridge.py")
text = p.read_text(encoding="utf-8")

marker = "def relational_gravity_block_to_dict("
idx = text.find(marker)
if idx < 0:
    raise SystemExit("ERROR: serializer function not found")

prefix = text[:idx].rstrip()

new_block = r'''
# ---------------------------------------------------------------------------
# P1.2 - Relational Gravity Bridge Guard
# ---------------------------------------------------------------------------

def _split_actor_field(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).replace(",", "/").split("/") if v.strip()]


def _join_actor_field(values):
    clean = []
    for v in values:
        s = str(v).strip()
        if s and s not in clean:
            clean.append(s)
    return "/".join(clean)


def _apply_relational_gravity_bridge_guard(state: dict) -> dict:
    """
    P1.2 Bridge Guard.
    Ne modifie pas tf_details.
    Securise la synthese top-level.
    """
    if not isinstance(state, dict):
        return state

    tf_details = state.get("tf_details", {}) or {}

    directions = []
    leaders = []
    antagonists = []

    for _, tf_state in tf_details.items():
        if not isinstance(tf_state, dict):
            continue
        if not tf_state.get("loaded", False):
            continue

        direction = tf_state.get("direction")
        if direction:
            directions.append(str(direction))

        leader = tf_state.get("leader")
        if leader:
            leaders.append(str(leader))

        for antagonist in _split_actor_field(tf_state.get("antagonist")):
            antagonists.append(antagonist)

    unique_directions = sorted(set(directions))
    unique_leaders = sorted(set(leaders))
    unique_antagonists = sorted(set(antagonists))

    state["direction_consistency"] = (
        "ALIGNED" if len(unique_directions) == 1
        else "CONFLICT" if len(unique_directions) > 1
        else "UNKNOWN"
    )

    state["leader_consistency"] = (
        "ALIGNED" if len(unique_leaders) == 1
        else "CONFLICT" if len(unique_leaders) > 1
        else "UNKNOWN"
    )

    state["antagonist_consistency"] = (
        "ALIGNED" if len(unique_antagonists) <= 2
        else "MIXED" if unique_antagonists
        else "UNKNOWN"
    )

    cross_tf_state = state.get("cross_tf_state")
    original_leader = state.get("dominant_leader")

    # Critical guard: MIXED field must not expose a clear top-level leader.
    if cross_tf_state == "RELATIONAL_GRAVITY_MIXED":
        state["dominant_leader_original"] = original_leader
        state["dominant_leader"] = "MIXED"
        state["leader_consistency"] = "CONFLICT"
        state["topline_reliable"] = False

        antagonist_list = _split_actor_field(state.get("dominant_antagonist"))
        if original_leader:
            antagonist_list = [
                a for a in antagonist_list
                if a != str(original_leader)
            ]

        state["dominant_antagonist"] = _join_actor_field(antagonist_list)

        state["summary"] = (
            "RELATIONAL_GRAVITY_MIXED - leader conflict / mixed field. "
            "Topline not reliable; use tf_details only."
        )
        return state

    # Non-mixed case: still remove leader from antagonist if present.
    leader = state.get("dominant_leader")
    antagonist_list = _split_actor_field(state.get("dominant_antagonist"))

    if leader and leader != "MIXED" and leader in antagonist_list:
        antagonist_list = [a for a in antagonist_list if a != leader]
        state["dominant_antagonist"] = _join_actor_field(antagonist_list)

    state["topline_reliable"] = (
        state.get("direction_consistency") == "ALIGNED"
        and state.get("leader_consistency") == "ALIGNED"
    )

    if state["topline_reliable"]:
        state["summary"] = "Relational Gravity topline reliable."
    else:
        state["summary"] = "Relational Gravity topline partial; inspect tf_details."

    return state


def relational_gravity_block_to_dict(block: RelationalGravityCockpitBlock) -> dict:
    """Serialize block to plain dict for JSON cockpit state."""
    out = {
        "bridge_version": block.bridge_version,
        "cross_tf_state": block.cross_tf_state,
        "dominant_direction": block.dominant_direction,
        "dominant_leader": block.dominant_leader,
        "dominant_antagonist": block.dominant_antagonist,
        "aligned_tfs": block.aligned_tfs,
        "counter_tf": block.counter_tf,
        "max_score": block.max_score,
        "notes": block.notes,
        "tf_details": {
            str(tf): {
                "loaded": s.loaded,
                "source_file": s.source_file,
                "status": s.status,
                "primary_state": s.primary_state,
                "group": s.group,
                "direction": s.direction,
                "gap_mode": s.gap_mode,
                "leader": s.leader,
                "antagonist": s.antagonist,
                "score": s.score,
                "confidence": s.confidence,
                "lab_signatures": s.lab_signatures,
                "interpretation": s.interpretation,
            }
            for tf, s in block.slots.items()
        },
    }

    return _apply_relational_gravity_bridge_guard(out)
'''

p.write_text(prefix + "\n\n" + new_block + "\n", encoding="utf-8")
print("PATCH_OK pf_relational_gravity_bridge.py P1.2 guard injected")
