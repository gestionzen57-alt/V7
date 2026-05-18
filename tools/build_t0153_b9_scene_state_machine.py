
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pf_t009_scene_state_machine import enrich_sequence_summary_with_scene_state_machine, write_outputs


def run(args):
    input_path = Path(args.sequence_summary_json)
    output_dir = Path(args.output_dir)
    summary = json.loads(input_path.read_text(encoding="utf-8"))
    enriched = enrich_sequence_summary_with_scene_state_machine(summary)
    return write_outputs(enriched, output_dir)


def main():
    parser = argparse.ArgumentParser(description="T0153 B9 Scene State Machine V0")
    parser.add_argument("--sequence-summary-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
