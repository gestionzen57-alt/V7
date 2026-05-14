from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"patch"))
from pf_reality_board_state_once import requali
def test_pair_up_after_high(): assert requali({"raw_bias":"PAIR_UP","film_state":"HIGH_ZONE_REJECTION","last_structural_event":"HIGH_ZONE_REJECTION"})[0]=="HIGH_ZONE_EXHAUSTION_RISK"
def test_pair_down_after_high(): assert requali({"raw_bias":"PAIR_DOWN","film_state":"HIGH_ZONE_REJECTION","last_structural_event":"HIGH_ZONE_REJECTION"})[0]=="POST_HIGH_UNWIND"
def test_pair_down_after_counter_breath(): assert requali({"raw_bias":"PAIR_DOWN","last_structural_event":"COUNTER_BREATH_REJECTED"})[0]=="SECOND_LEG_DOWN"
def test_pair_up_lower_lock(): assert requali({"raw_bias":"PAIR_UP","last_structural_event":"LOWER_LOCK"})[0]=="COUNTER_BREATH_UP"
def test_hot_pending(): assert requali({"raw_bias":"HOT","price_confirmation":"PENDING"})[0]=="PRESSURE_PENDING"
