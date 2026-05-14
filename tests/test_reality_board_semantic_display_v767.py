from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patch"))

from pf_reality_board_state_once import build_state

def test_time_profiles_are_compact_not_raw_dict_dump():
    state = build_state(ROOT, "GBPUSD")
    roles = state["time_profile_roles"]
    for key in ("htf", "mtf", "ltf"):
        summary = roles[key]["summary_fr"]
        assert isinstance(summary, str)
        assert "{" not in summary
        assert "events_total" not in summary
        assert len(summary) < 220

def test_telegram_candidate_uses_clean_ascii_separator_and_no_duplicate_alternative():
    state = build_state(ROOT, "GBPUSD")
    text = state["telegram_candidate"]["text_fr"]
    assert "GBPUSD - Reality Board" in text
    assert "GBPUSD â€” Reality Board" not in text
    assert "Alternative : Alternative :" not in text
