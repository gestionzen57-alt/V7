from pathlib import Path
import json,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"patch"))
from pf_reality_board_state_once import build_state
def wj(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,ensure_ascii=False),encoding="utf-8")
def test_state_and_time_roles():
    fx=json.loads((ROOT/"tests/fixtures/reality_board_v767/gbpusd_20260514_reading_partial.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        t=Path(tmp); shutil.copytree(ROOT/"schema",t/"schema")
        wj(t/"output/dashboard_surface/GBPUSD/terrain_packet.json",fx["terrain_packet"]); wj(t/"output/dashboard_surface/GBPUSD/film_memory_match.json",fx["film_memory_match"])
        wj(t/"Core/output/dashboard_surface/GBPUSD/ltf_session_memory.json",fx["ltf_session_memory"]); wj(t/"Core/output/dashboard_surface/GBPUSD/mtf_session_memory.json",fx["mtf_session_memory"]); wj(t/"Core/output/dashboard_surface/GBPUSD/htf_session_memory.json",fx["htf_session_memory"])
        st=build_state(t,"GBPUSD")
        assert st["reading_status"]=="READING_PARTIAL"
        assert st["time_profile_roles"]["htf"]["role"]=="ANALYSE"
        assert st["time_profile_roles"]["mtf"]["role"]=="PLAN"
        assert st["time_profile_roles"]["ltf"]["role"]=="ACTION"
        assert st["telegram_candidate"]["send_enabled"] is False
