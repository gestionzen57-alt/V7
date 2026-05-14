from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"patch"))
from pf_reality_board_state_once import build_state
def test_no_forbidden_terms_in_fixture_state():
    st=build_state(ROOT,"GBPUSD")
    blob=json.dumps(st,ensure_ascii=False).upper()
    for term in ["BUY","SELL","ENTRY","EXIT","STOP","TARGET"]:
        assert term not in blob
