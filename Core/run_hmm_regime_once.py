"""
run_hmm_regime_once.py
PowerFlow B1 — one-shot HMM regime runner V1.2 Standalone Schema-Aware

Usage from project root:
    python Core/run_hmm_regime_once.py --db Core/powerflow.db --train --predict --pretty

Usage from Core:
    python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from pf_hmm_regime import HMMRegimeEngine, METHOD, MODEL_VERSION


RUNNER_VERSION = "HMMRegimeRunnerV1.2StandaloneSchema"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_root() -> Path:
    # This runner lives in Core/. The repo root is the parent of Core.
    return Path(__file__).resolve().parent.parent


def resolve_path(path_text: str | None, default: Path) -> Path:
    if not path_text:
        return default.resolve()
    p = Path(path_text)
    if p.is_absolute():
        return p.resolve()
    return (Path.cwd() / p).resolve()


def parse_tfs(value: str) -> List[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def write_json(path: Path, payload: Dict[str, Any], pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2 if pretty else None, ensure_ascii=False)


def build_base_payload(args: argparse.Namespace, db_path: Path, model_path: Path, output_path: Path) -> Dict[str, Any]:
    return {
        "timestamp": utc_now(),
        "runner_version": RUNNER_VERSION,
        "model_version": MODEL_VERSION,
        "method": METHOD,
        "db_path": str(db_path),
        "model_path": str(model_path),
        "output_path": str(output_path),
        "train_requested": bool(args.train),
        "predict_requested": bool(args.predict),
        "valid": False,
        "technical_risks": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow B1 HMM regime runner")
    parser.add_argument("--db", default=None, help="Path to powerflow.db")
    parser.add_argument("--model", default=None, help="Path to HMM model pickle")
    parser.add_argument("--output", default=None, help="Path to output JSON")
    parser.add_argument("--tfs", default="240,60", help="Comma-separated TF priority list")
    parser.add_argument("--train", action="store_true", help="Train model on historical DB data")
    parser.add_argument("--predict", action="store_true", help="Predict current regime")
    parser.add_argument("--pretty", action="store_true", help="Pretty JSON output")
    parser.add_argument("--lookback", type=int, default=50, help="Prediction lookback observations")
    args = parser.parse_args()

    root = project_root()
    db_default = root / "Core" / "powerflow.db"
    output_default = root / "output" / "hmm_regime_result.json"
    model_default = root / "output" / "hmm_regime_model.pkl"

    db_path = resolve_path(args.db, db_default)
    output_path = resolve_path(args.output, output_default)
    model_path = resolve_path(args.model, model_default)
    tfs = parse_tfs(args.tfs)

    # If neither flag is passed, behave as a snapshot prediction.
    if not args.train and not args.predict:
        args.predict = True

    payload = build_base_payload(args, db_path, model_path, output_path)

    try:
        engine = HMMRegimeEngine(model_path=model_path if model_path.exists() else None)

        if args.train:
            training = engine.train_on_historical_data(db_path=db_path, tfs=tfs, model_path=model_path)
            payload["training"] = training
            if not training.get("valid"):
                payload["valid"] = False
                payload["technical_risks"] = training.get("technical_risks", [])
                payload["error"] = training.get("error")
                write_json(output_path, payload, pretty=args.pretty)
                print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
                return 2

        if args.predict:
            # Reload from disk if training was not requested but a model exists.
            if not args.train and model_path.exists():
                engine = HMMRegimeEngine(model_path=model_path)
            prediction = engine.predict_from_db(db_path=db_path, tfs=tfs, lookback=args.lookback)
            payload["prediction"] = prediction
            payload["valid"] = bool(prediction.get("valid"))
            payload["technical_risks"] = prediction.get("technical_risks", [])
            payload["regime"] = prediction.get("regime")
            payload["confidence"] = prediction.get("confidence")
            payload["probabilities"] = prediction.get("probabilities")
            payload["probability_map"] = prediction.get("probability_map")
            payload["raw_state"] = prediction.get("raw_state")
            payload["error"] = prediction.get("error")
        else:
            payload["valid"] = bool(payload.get("training", {}).get("valid"))
            payload["error"] = payload.get("training", {}).get("error")

        write_json(output_path, payload, pretty=args.pretty)
        print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0 if payload.get("valid") else 2

    except Exception as exc:
        payload["valid"] = False
        payload["technical_risks"] = ["HMM_RUNTIME_ERROR"]
        payload["error"] = str(exc)
        write_json(output_path, payload, pretty=args.pretty)
        print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
