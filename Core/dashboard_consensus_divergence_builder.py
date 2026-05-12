#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — CONSENSUS_DIVERGENCE_UI builder.

Purpose:
- Respect duality: Legacy/HMM and Rolling/Wavelet.
- Default display = consensus, one synthetic block.
- Significant divergence = two blocks side by side.
- No forced merge.

Read-only file builder. No DB write.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


REGIME_CONFIDENCE_DIVERGENCE_THRESHOLD = 0.15
DENSITY_CONSENSUS_RATIO = 0.75

REGIME_ALIASES = {
    "TREND": "TENDANCE",
    "REGIME_TENDANCE": "TENDANCE",
    "REGIME_COMPRESSION": "COMPRESSION",
    "REGIME_TRANSITION": "TRANSITION",
    "REGIME_RANGE": "RANGE",
    "UNKNOWN": "UNKNOWN",
    "NONE": "UNKNOWN",
    "": "UNKNOWN",
}

DENSITY_ALIASES = {
    "COMPRESSING": "CYCLE_COMPRESSING",
    "CYCLE_COMPRESSING": "CYCLE_COMPRESSING",
    "COMPRESSION": "CYCLE_COMPRESSING",
    "COMPRESSED": "CYCLE_COMPRESSING",
    "EXPANDING": "CYCLE_EXPANDING",
    "CYCLE_EXPANDING": "CYCLE_EXPANDING",
    "EXPANSION": "CYCLE_EXPANDING",
    "STABLE": "CYCLE_STABLE",
    "CYCLE_STABLE": "CYCLE_STABLE",
    "NEUTRAL": "CYCLE_STABLE",
    "UNKNOWN": "CYCLE_UNKNOWN",
    "": "CYCLE_UNKNOWN",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def first_existing(paths: Iterable[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    return list(paths)[0]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def normalize_regime(value: Any) -> str:
    raw = normalize_text(value)
    return REGIME_ALIASES.get(raw, raw or "UNKNOWN")


def normalize_density_state(value: Any) -> str:
    raw = normalize_text(value)
    return DENSITY_ALIASES.get(raw, raw or "CYCLE_UNKNOWN")


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        x = float(value)
        if math.isnan(x):
            return default
        return x
    except Exception:
        return default


def find_first_key(obj: Any, keys: Iterable[str]) -> Any:
    targets = {k.lower() for k in keys}
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if str(k).lower() in targets:
                return v
        for v in obj.values():
            found = find_first_key(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first_key(item, keys)
            if found is not None:
                return found
    return None


def extract_regime_payload(data: Mapping[str, Any], source: str) -> Dict[str, Any]:
    """Schema-flex regime extraction."""
    regime = (
        data.get("regime")
        or data.get("regime_state")
        or data.get("state")
        or data.get("dominant_regime")
        or find_first_key(data, ("regime", "regime_state", "dominant_regime", "state"))
    )
    confidence = (
        data.get("confidence")
        or data.get("regime_confidence")
        or data.get("probability")
        or data.get("score")
        or find_first_key(data, ("confidence", "regime_confidence", "probability", "score"))
    )

    return {
        "source": source,
        "regime": normalize_regime(regime),
        "confidence": round(as_float(confidence, 0.0), 6),
        "raw_regime": regime,
    }


def build_regime_consensus(legacy: Mapping[str, Any], hmm: Mapping[str, Any]) -> Dict[str, Any]:
    legacy_payload = extract_regime_payload(legacy, "LEGACY")
    hmm_payload = extract_regime_payload(hmm, "HMM")

    same_regime = legacy_payload["regime"] == hmm_payload["regime"]
    conf_gap = abs(legacy_payload["confidence"] - hmm_payload["confidence"])
    consensus = same_regime and conf_gap < REGIME_CONFIDENCE_DIVERGENCE_THRESHOLD

    if consensus:
        confidence = round((legacy_payload["confidence"] + hmm_payload["confidence"]) / 2.0, 6)
        return {
            "regime_display_mode": "CONSENSUS",
            "regime_block": {
                "regime": legacy_payload["regime"],
                "confidence": confidence,
                "source": "LEGACY_HMM_ALIGNED",
                "confidence_gap": round(conf_gap, 6),
            },
            "regime_sources": [legacy_payload, hmm_payload],
        }

    return {
        "regime_display_mode": "DIVERGENCE",
        "regime_blocks": [
            {
                "source": "LEGACY",
                "regime": legacy_payload["regime"],
                "confidence": legacy_payload["confidence"],
            },
            {
                "source": "HMM",
                "regime": hmm_payload["regime"],
                "confidence": hmm_payload["confidence"],
            },
        ],
        "regime_divergence": {
            "same_regime": same_regime,
            "confidence_gap": round(conf_gap, 6),
            "threshold": REGIME_CONFIDENCE_DIVERGENCE_THRESHOLD,
        },
    }


def iter_currency_items(obj: Any) -> Iterable[Tuple[str, Mapping[str, Any]]]:
    if isinstance(obj, Mapping):
        currencies = obj.get("currencies") or obj.get("currency_states") or obj.get("states")
        if isinstance(currencies, Mapping):
            for cur, payload in currencies.items():
                if isinstance(payload, Mapping):
                    yield normalize_text(cur), payload
                else:
                    yield normalize_text(cur), {"cycle_state": payload}
        elif isinstance(currencies, list):
            for item in currencies:
                if isinstance(item, Mapping):
                    cur = item.get("currency") or item.get("ccy") or item.get("symbol")
                    if cur:
                        yield normalize_text(cur), item

        # Fallback: top-level currency keys.
        for cur in ("GBP", "EUR", "USD", "JPY", "CAD", "CHF", "AUD", "NZD", "XAU"):
            payload = obj.get(cur) or obj.get(cur.lower())
            if isinstance(payload, Mapping):
                yield cur, payload
            elif payload is not None and not isinstance(payload, (dict, list)):
                yield cur, {"cycle_state": payload}


def extract_cycle_state(payload: Mapping[str, Any]) -> str:
    value = (
        payload.get("cycle_state")
        or payload.get("cycleState")
        or payload.get("state")
        or payload.get("density_state")
        or payload.get("temporal_density_state")
        or payload.get("wavelet_state")
        or payload.get("dominant_state")
        or find_first_key(payload, ("cycle_state", "state", "density_state", "wavelet_state", "dominant_state"))
    )
    return normalize_density_state(value)


def extract_density_map(data: Mapping[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for cur, payload in iter_currency_items(data):
        if cur and isinstance(payload, Mapping):
            result[cur] = extract_cycle_state(payload)

    # If the file only exposes grouped lists, support that too.
    for group_key, state in [
        ("compressing", "CYCLE_COMPRESSING"),
        ("compression", "CYCLE_COMPRESSING"),
        ("expanding", "CYCLE_EXPANDING"),
        ("expansion", "CYCLE_EXPANDING"),
        ("stable", "CYCLE_STABLE"),
    ]:
        group = data.get(group_key)
        if isinstance(group, list):
            for cur in group:
                result[normalize_text(cur)] = state

    return result


def grouped_density(density_map: Mapping[str, str]) -> Dict[str, List[str]]:
    groups = {"compressing": [], "expanding": [], "stable": [], "unknown": []}
    for cur, state in density_map.items():
        if state == "CYCLE_COMPRESSING":
            groups["compressing"].append(cur)
        elif state == "CYCLE_EXPANDING":
            groups["expanding"].append(cur)
        elif state == "CYCLE_STABLE":
            groups["stable"].append(cur)
        else:
            groups["unknown"].append(cur)
    for values in groups.values():
        values.sort()
    return groups


def build_density_consensus(rolling: Mapping[str, Any], wavelet: Mapping[str, Any]) -> Dict[str, Any]:
    rolling_map = extract_density_map(rolling)
    wavelet_map = extract_density_map(wavelet)

    currencies = sorted(set(rolling_map) | set(wavelet_map))
    compared = []
    aligned = []

    for cur in currencies:
        r = rolling_map.get(cur, "CYCLE_UNKNOWN")
        w = wavelet_map.get(cur, "CYCLE_UNKNOWN")
        if r == "CYCLE_UNKNOWN" or w == "CYCLE_UNKNOWN":
            continue
        compared.append(cur)
        if r == w:
            aligned.append(cur)

    ratio = (len(aligned) / len(compared)) if compared else 0.0

    if compared and ratio >= DENSITY_CONSENSUS_RATIO:
        counts: Dict[str, int] = {}
        for cur in aligned:
            state = rolling_map[cur]
            counts[state] = counts.get(state, 0) + 1
        dominant_state = max(counts.items(), key=lambda kv: kv[1])[0] if counts else "CYCLE_UNKNOWN"

        return {
            "density_display_mode": "CONSENSUS",
            "density_block": {
                "dominant_state": dominant_state,
                "currencies_count": len(aligned),
                "source": "ROLLING_WAVELET_ALIGNED",
                "alignment_ratio": round(ratio, 6),
                "compared_count": len(compared),
            },
            "density_sources": {
                "rolling": grouped_density(rolling_map),
                "wavelet": grouped_density(wavelet_map),
            },
        }

    return {
        "density_display_mode": "DIVERGENCE",
        "density_blocks": [
            {"source": "ROLLING", **grouped_density(rolling_map)},
            {"source": "WAVELET", **grouped_density(wavelet_map)},
        ],
        "density_divergence": {
            "alignment_ratio": round(ratio, 6),
            "threshold": DENSITY_CONSENSUS_RATIO,
            "compared_count": len(compared),
            "aligned_count": len(aligned),
        },
    }


def build_consensus_divergence(
    legacy_path: Path,
    hmm_path: Path,
    rolling_path: Path,
    wavelet_path: Path,
) -> Dict[str, Any]:
    legacy = read_json(legacy_path)
    hmm = read_json(hmm_path)
    rolling = read_json(rolling_path)
    wavelet = read_json(wavelet_path)

    technical_risks: List[str] = []
    for label, path, data in [
        ("REGIME_LEGACY_MISSING", legacy_path, legacy),
        ("REGIME_HMM_MISSING", hmm_path, hmm),
        ("TEMPORAL_DENSITY_ROLLING_MISSING", rolling_path, rolling),
        ("WAVELET_MISSING", wavelet_path, wavelet),
    ]:
        if not data:
            technical_risks.append(f"{label}:{path}")

    output = {
        "timestamp_utc": utc_now_iso(),
        "method": "CONSENSUS_DIVERGENCE_UI",
        "rules": {
            "default": "CONSENSUS_ONE_BLOCK",
            "regime_confidence_divergence_threshold": REGIME_CONFIDENCE_DIVERGENCE_THRESHOLD,
            "density_consensus_ratio": DENSITY_CONSENSUS_RATIO,
        },
        "input_paths": {
            "regime_legacy": str(legacy_path),
            "regime_hmm": str(hmm_path),
            "temporal_density_rolling": str(rolling_path),
            "wavelet": str(wavelet_path),
        },
        "technical_risks": technical_risks,
    }

    output.update(build_regime_consensus(legacy, hmm))
    output.update(build_density_consensus(rolling, wavelet))
    return output


def choose_paths(surface_dir: Path, symbol: str) -> Dict[str, Path]:
    """Use exact requested paths, with symbol fallback if project is namespaced."""
    symbol_surface = surface_dir / symbol.upper()

    legacy = first_existing([surface_dir / "regime_legacy.json", symbol_surface / "regime_legacy.json"])
    hmm = first_existing([surface_dir / "regime_hmm.json", symbol_surface / "regime_hmm.json"])
    wavelet = first_existing([surface_dir / "wavelet.json", symbol_surface / "wavelet.json"])
    rolling = first_existing([
        Path("output") / "temporal_density_state.json",
        Path("output") / f"temporal_density_state_{symbol.upper()}.json",
    ])

    return {"legacy": legacy, "hmm": hmm, "rolling": rolling, "wavelet": wavelet}


def write_json(data: Mapping[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build dashboard consensus/divergence state.")
    parser.add_argument("--symbol", default="GBPUSD", help="Fallback symbol if dashboard_surface is namespaced.")
    parser.add_argument("--surface-dir", default="output/dashboard_surface")
    parser.add_argument("--legacy", default=None)
    parser.add_argument("--hmm", default=None)
    parser.add_argument("--rolling", default=None)
    parser.add_argument("--wavelet", default=None)
    parser.add_argument("--output", "--out", dest="output", default="output/dashboard_surface/consensus_divergence.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    paths = choose_paths(Path(args.surface_dir), args.symbol)
    legacy_path = Path(args.legacy) if args.legacy else paths["legacy"]
    hmm_path = Path(args.hmm) if args.hmm else paths["hmm"]
    rolling_path = Path(args.rolling) if args.rolling else paths["rolling"]
    wavelet_path = Path(args.wavelet) if args.wavelet else paths["wavelet"]

    result = build_consensus_divergence(legacy_path, hmm_path, rolling_path, wavelet_path)
    write_json(result, Path(args.output))

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            "CONSENSUS_DIVERGENCE_OK | "
            f"regime={result.get('regime_display_mode')} | "
            f"density={result.get('density_display_mode')} | "
            f"out={args.output}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
