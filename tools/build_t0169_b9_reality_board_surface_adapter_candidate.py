from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_reality_board_surface_adapter_candidate import run


def existing_or_none(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    p = Path(path)
    return str(p) if p.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build B9 Reality Board Surface Adapter Candidate V0")
    parser.add_argument("--read-model-json", default="outputs/b9_reality_board_read_model_v01/B9_REALITY_BOARD_READ_MODEL_V01.json")
    parser.add_argument("--panel-json", default="outputs/b9_reality_board_scene_panel_candidate_v01/B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json")
    parser.add_argument("--payload-json", default="outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json")
    parser.add_argument("--display-contract-json", default="outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json")
    parser.add_argument("--output-dir", default="outputs/b9_reality_board_surface_adapter_candidate_v0")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    summary = run(
        read_model_json=existing_or_none(args.read_model_json),
        panel_json=existing_or_none(args.panel_json),
        payload_json=existing_or_none(args.payload_json),
        display_contract_json=existing_or_none(args.display_contract_json),
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary.get("surface_state") == "BLOCKED_FORBIDDEN_LANGUAGE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
