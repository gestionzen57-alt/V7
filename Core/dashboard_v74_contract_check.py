from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SURFACE_DIR = Path("output/dashboard_surface")

DEFAULT_FILES = {
    "cockpit": SURFACE_DIR / "trader_cockpit.json",
    "evidence_bus": SURFACE_DIR / "evidence_bus.json",
    "evidence_reading": SURFACE_DIR / "evidence_reading.json",
    "time_profiles": SURFACE_DIR / "time_profiles_dashboard.json",
    "phase_synthesis": SURFACE_DIR / "phase_synthesis.json",
    "b8": SURFACE_DIR / "b8_cross_surface.json",
    "data_health": SURFACE_DIR / "data_health.json",
}


BAD_VALUES = {
    "",
    "UNKNOWN",
    "NONE",
    "NULL",
    "N/A",
}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []

    if not path.exists():
        return {}, [f"MISSING_SOURCE:{path.as_posix()}"]

    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return {}, [f"READ_ERROR:{path.as_posix()}:{type(exc).__name__}:{exc}"]

    if not raw.strip():
        return {}, [f"EMPTY_SOURCE:{path.as_posix()}"]

    try:
        data = json.loads(raw)
    except Exception as exc:
        return {}, [f"INVALID_JSON:{path.as_posix()}:{type(exc).__name__}:{exc}"]

    if not isinstance(data, dict):
        return {}, [f"ROOT_NOT_OBJECT:{path.as_posix()}"]

    return data, issues


def upper(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip().upper()


def is_bad(v: Any) -> bool:
    return upper(v) in BAD_VALUES


def add_if_bad(issues: list[str], label: str, value: Any) -> None:
    if is_bad(value):
        issues.append(f"MISSING_OR_WEAK_FIELD:{label}={value!r}")


def first_existing(data: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in data and data.get(k) not in (None, ""):
            return data.get(k)
    return None


def extract_nested(data: Any, keys: list[str]) -> Any:
    """Recursive shallow finder for unstable cockpit schemas."""
    if isinstance(data, dict):
        for k in keys:
            if k in data and data.get(k) not in (None, ""):
                return data.get(k)
        for v in data.values():
            found = extract_nested(v, keys)
            if found not in (None, ""):
                return found
    elif isinstance(data, list):
        for item in data:
            found = extract_nested(item, keys)
            if found not in (None, ""):
                return found
    return None


def check_evidence_reading(data: dict[str, Any], issues: list[str]) -> None:
    add_if_bad(issues, "evidence_reading.attention", data.get("attention"))
    add_if_bad(issues, "evidence_reading.phase", data.get("phase"))
    add_if_bad(issues, "evidence_reading.bias", data.get("bias"))
    add_if_bad(issues, "evidence_reading.phrase", data.get("phrase"))

    phrase = str(data.get("phrase") or "")
    if "Aucune phrase Evidence Reading" in phrase:
        issues.append("PLACEHOLDER_TEXT:evidence_reading.phrase")

    warning = data.get("semantic_warning")
    if data.get("phase") in {
        "STRUCTURAL_BEARISH_WITH_LTF_MTF_COUNTERFLOW",
        "STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW",
    }:
        add_if_bad(issues, "evidence_reading.structural_bias", data.get("structural_bias"))
        add_if_bad(issues, "evidence_reading.counterflow_bias", data.get("counterflow_bias"))
        if upper(warning) != "LTF_MTF_COUNTERFLOW_ACTIVE":
            issues.append(f"SEMANTIC_WARNING_MISMATCH:{warning!r}")

    watch = data.get("watch")
    if not isinstance(watch, list) or not watch:
        issues.append("MISSING_OR_EMPTY_LIST:evidence_reading.watch")


def check_evidence_bus(data: dict[str, Any], issues: list[str]) -> None:
    add_if_bad(issues, "evidence_bus.global_attention", data.get("global_attention"))
    add_if_bad(issues, "evidence_bus.dominant_phase", data.get("dominant_phase"))
    add_if_bad(issues, "evidence_bus.dominant_bias", data.get("dominant_bias"))
    add_if_bad(issues, "evidence_bus.dashboard_bias", data.get("dashboard_bias"))

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append("MISSING_OR_EMPTY_LIST:evidence_bus.evidence")
        return

    required_layers = {
        "LTF",
        "MTF",
        "HTF",
        "COCKPIT",
        "B8_CROSS_SYMBOL",
        "LIVE_BRIEF",
        "MULTIREAD",
    }
    found_layers = {upper(x.get("layer")) for x in evidence if isinstance(x, dict)}
    missing = sorted(required_layers - found_layers)
    for layer in missing:
        issues.append(f"MISSING_EVIDENCE_LAYER:{layer}")

    for i, ev in enumerate(evidence):
        if not isinstance(ev, dict):
            issues.append(f"BAD_EVIDENCE_ROW:evidence[{i}]")
            continue
        add_if_bad(issues, f"evidence[{i}].layer", ev.get("layer"))
        add_if_bad(issues, f"evidence[{i}].state", ev.get("state"))
        if ev.get("weight") is None:
            issues.append(f"MISSING_WEIGHT:evidence[{i}].weight")


def check_time_profiles(data: dict[str, Any], issues: list[str]) -> None:
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        issues.append("MISSING_OR_EMPTY_LIST:time_profiles.profiles")
        return

    required = {"LTF", "MTF", "HTF"}
    found = {upper(p.get("profile")) for p in profiles if isinstance(p, dict)}
    for p in sorted(required - found):
        issues.append(f"MISSING_TIME_PROFILE:{p}")

    for p in profiles:
        if not isinstance(p, dict):
            continue

        name = upper(p.get("profile"))
        add_if_bad(issues, f"time_profiles.{name}.attention", p.get("attention"))
        add_if_bad(issues, f"time_profiles.{name}.main_state", p.get("main_state"))
        add_if_bad(issues, f"time_profiles.{name}.dominant_bias", p.get("dominant_bias"))

        tfs = p.get("timeframes")
        if not isinstance(tfs, dict) or not tfs:
            issues.append(f"MISSING_TIMEFRAMES:{name}")
            continue

        for tf, row in tfs.items():
            if not isinstance(row, dict):
                issues.append(f"BAD_TIMEFRAME_ROW:{name}.{tf}")
                continue
            phase = upper(row.get("phase"))
            bias = upper(row.get("bias"))
            risks = row.get("technical_risks") or []

            add_if_bad(issues, f"time_profiles.{name}.{tf}.phase", row.get("phase"))
            add_if_bad(issues, f"time_profiles.{name}.{tf}.important_event", row.get("important_event"))

            # Thin higher-timeframe data is an explicit data-health state, not a silent dashboard failure.
            # D1 can legitimately have UNKNOWN bias when phase=THIN_DATA and D1_THIN_ROWS is present.
            if upper(tf) == "D1" and phase == "THIN_DATA":
                if "D1_THIN_ROWS" not in risks:
                    issues.append("D1_THIN_DATA_WITHOUT_RISK:D1_THIN_ROWS")
            else:
                add_if_bad(issues, f"time_profiles.{name}.{tf}.bias", row.get("bias"))


def check_cockpit(data: dict[str, Any], issues: list[str]) -> None:
    action = extract_nested(data, ["action", "attention", "status"])
    state = extract_nested(data, ["state", "etat", "main_state", "market_state"])
    reading = extract_nested(data, ["reading", "synthesis", "multiread_synthesis"])

    add_if_bad(issues, "cockpit.action", action)
    add_if_bad(issues, "cockpit.state", state)
    add_if_bad(issues, "cockpit.reading", reading)

    scenarios = extract_nested(data, ["scenarios", "watch_scenarios"])
    if scenarios is None:
        issues.append("MISSING_FIELD:cockpit.scenarios")


def check_b8(data: dict[str, Any], issues: list[str]) -> None:
    status = data.get("status")
    coverage = data.get("coverage")

    add_if_bad(issues, "b8.status", status)

    if upper(status) == "DEGRADED":
        risks = data.get("technical_risks") or data.get("risks") or []
        msg = str(data.get("message") or "")
        if "B8_INSUFFICIENT_CROSS_PAIR_COVERAGE" not in risks and "INSUFFICIENT" not in msg.upper():
            issues.append("B8_DEGRADED_WITHOUT_EXPLANATION")

    if coverage is not None and is_bad(coverage) and upper(status) != "DEGRADED":
        issues.append(f"B8_BAD_COVERAGE_WITHOUT_DEGRADED:{coverage!r}")


def check_phase(data: dict[str, Any], issues: list[str]) -> None:
    add_if_bad(issues, "phase_synthesis.attention", data.get("attention"))
    add_if_bad(issues, "phase_synthesis.phase_state", data.get("phase_state"))
    add_if_bad(issues, "phase_synthesis.dominant_bias", data.get("dominant_bias"))

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append("MISSING_OR_EMPTY_LIST:phase_synthesis.evidence")


def scan_visual_leaks(label: str, data: Any, issues: list[str]) -> None:
    """Detect values that would leak badly into the dashboard."""
    bad_fragments = [
        "[object Object]",
        "undefined",
        "NaN",
        "Aucune phrase Evidence Reading disponible",
    ]

    def walk(prefix: str, v: Any) -> None:
        if isinstance(v, dict):
            for k, val in v.items():
                walk(f"{prefix}.{k}" if prefix else str(k), val)
        elif isinstance(v, list):
            for i, val in enumerate(v):
                walk(f"{prefix}[{i}]", val)
        else:
            s = str(v)
            for frag in bad_fragments:
                if frag in s:
                    issues.append(f"VISUAL_LEAK:{label}:{prefix}:{frag}")

    walk("", data)


def check_dashboard_html(path: Path, issues: list[str]) -> None:
    if not path.exists():
        issues.append(f"MISSING_DASHBOARD_HTML:{path.as_posix()}")
        return

    text = path.read_text(encoding="utf-8-sig", errors="replace")

    required_tokens = [
        "evidence_reading.json",
        "evidence_bus.json",
        "time_profiles_dashboard.json",
        "trader_cockpit.json",
        "dashboard_bias",
        "structural_bias",
        "counterflow_bias",
        "semantic_warning",
        "recursiveFind",
        "repairMojibake",
        "MISSING_FIELD",
    ]

    for token in required_tokens:
        if token not in text:
            issues.append(f"DASHBOARD_HTML_MISSING_TOKEN:{token}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", default="dashboard_powerflow_v74.html")
    parser.add_argument("--surface-dir", default="output/dashboard_surface")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    global SURFACE_DIR
    SURFACE_DIR = Path(args.surface_dir)

    files = {
        "cockpit": SURFACE_DIR / "trader_cockpit.json",
        "evidence_bus": SURFACE_DIR / "evidence_bus.json",
        "evidence_reading": SURFACE_DIR / "evidence_reading.json",
        "time_profiles": SURFACE_DIR / "time_profiles_dashboard.json",
        "phase_synthesis": SURFACE_DIR / "phase_synthesis.json",
        "b8": SURFACE_DIR / "b8_cross_surface.json",
        "data_health": SURFACE_DIR / "data_health.json",
    }

    issues: list[str] = []
    data: dict[str, dict[str, Any]] = {}

    for name, path in files.items():
        obj, load_issues = load_json(path)
        issues.extend(load_issues)
        data[name] = obj

    check_dashboard_html(Path(args.html), issues)

    if data.get("evidence_reading"):
        check_evidence_reading(data["evidence_reading"], issues)

    if data.get("evidence_bus"):
        check_evidence_bus(data["evidence_bus"], issues)

    if data.get("time_profiles"):
        check_time_profiles(data["time_profiles"], issues)

    if data.get("cockpit"):
        check_cockpit(data["cockpit"], issues)

    if data.get("b8"):
        check_b8(data["b8"], issues)

    if data.get("phase_synthesis"):
        check_phase(data["phase_synthesis"], issues)

    for name, obj in data.items():
        if obj:
            scan_visual_leaks(name, obj, issues)

    result = {
        "method": "DASHBOARD_V74_CONTRACT_CHECK",
        "status": "OK" if not issues else "FAIL",
        "issues_count": len(issues),
        "issues": issues,
        "checked_files": {k: v.as_posix() for k, v in files.items()},
        "html": args.html,
    }

    out = SURFACE_DIR / "dashboard_v74_contract_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")

    if issues:
        print(f"DASHBOARD_V74_CONTRACT_FAIL | issues={len(issues)} | out={out.as_posix()}")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"DASHBOARD_V74_CONTRACT_OK | out={out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
