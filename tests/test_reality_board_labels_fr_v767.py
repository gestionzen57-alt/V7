from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_labels():
    labels=json.loads((ROOT/"schema/reality_board_labels_fr_v767.json").read_text(encoding="utf-8"))
    assert labels["footer"]=="PowerFlow Ã©claire le terrain. Le trader arbitre."
    assert labels["film_state"]["HIGH_ZONE_REJECTION"]=="Rejet de zone haute"
    assert "Ã©puisement" in labels["qualified_bias"]["HIGH_ZONE_EXHAUSTION_RISK"]
