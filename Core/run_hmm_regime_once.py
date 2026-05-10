"""Runner PowerFlow V7.2 — B1+ HMM Gaussian regime."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

from pf_hmm_regime import (
    HMMRegimeGaussian,
    fallback_result,
    predict_from_db,
    train_from_db,
    write_json,
)

DEFAULT_DB = "Core/powerflow.db"
DEFAULT_MODEL = "output/hmm_regime_model.pkl"
DEFAULT_OUTPUT = "output/hmm_regime_result.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow B1+ HMM Gaussian regime runner")
    p.add_argument("--db", default=DEFAULT_DB, help="Path to powerflow.db")
    p.add_argument("--symbol", default="GBPUSD", help="Symbol, default GBPUSD")
    p.add_argument("--tf", type=int, default=240, help="Primary timeframe, default 240")
    p.add_argument("--fallback-tf", type=int, default=60, help="Fallback timeframe, default 60")
    p.add_argument("--lookback", type=int, default=500, help="Historical rows for train")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Model pickle path")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path")
    p.add_argument("--train", action="store_true", help="Train model from DB")
    p.add_argument("--predict", action="store_true", help="Predict current regime")
    p.add_argument("--pretty", action="store_true", help="Print JSON")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    do_train = args.train or not args.predict
    do_predict = args.predict or not args.train

    model = None
    train_meta: Dict[str, Any] = {}

    if do_train:
        model, train_meta = train_from_db(
            db_path=args.db,
            symbol=args.symbol,
            primary_tf=args.tf,
            fallback_tf=args.fallback_tf,
            lookback=args.lookback,
        )
        if model is not None:
            model.save(args.model)

    if do_predict:
        if model is None:
            if Path(args.model).exists():
                model = HMMRegimeGaussian.load(args.model)
            else:
                model, train_meta = train_from_db(
                    db_path=args.db,
                    symbol=args.symbol,
                    primary_tf=args.tf,
                    fallback_tf=args.fallback_tf,
                    lookback=args.lookback,
                )
                if model is not None:
                    model.save(args.model)

        if model is None:
            payload = fallback_result("HMM_MODEL_MISSING_OR_TRAIN_FAILED", train_meta)
        else:
            payload = predict_from_db(
                model=model,
                db_path=args.db,
                symbol=args.symbol,
                timeframe=args.tf,
                fallback_tf=args.fallback_tf,
                lookback=min(args.lookback, 240),
            )
            payload["model_path"] = args.model
            if train_meta:
                payload["train_meta"] = train_meta
    else:
        payload = {
            "valid": True,
            "method": "hmm_gaussian_standalone",
            "version": "HMMRegimeV1.2StandaloneSchema",
            "model_path": args.model,
            "train_meta": train_meta,
        }

    write_json(args.output, payload)
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
