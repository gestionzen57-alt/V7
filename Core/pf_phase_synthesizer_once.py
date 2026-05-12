from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: str | Path, data: dict[str, Any], pretty: bool = False) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, indent=2 if pretty else None, ensure_ascii=False),
        encoding="utf-8",
    )


def write_txt(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"PHASE SYNTHESIS | {data.get('symbol')} | {data.get('attention')} | {data.get('phase_state')}",
        f"bias={data.get('dominant_bias')}",
        f"confidence={data.get('confidence')}",
        "",
        f"READING={data.get('reading')}",
        "",
        "EVIDENCE",
    ]

    for e in data.get("evidence") or []:
        lines.append(f"- {e}")

    lines += ["", "TECHNICAL RISKS"]
    for r in data.get("technical_risks") or []:
        lines.append(f"- {r}")

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def first_profile(profiles: dict[str, Any], name: str) -> dict[str, Any]:
    for item in profiles.get("profiles") or []:
        if str(item.get("profile", "")).upper() == name.upper():
            return item
    return {}


def get_b8_state(b8: dict[str, Any]) -> tuple[str, str]:
    status = str(b8.get("status") or "UNKNOWN").upper()
    coverage = str(b8.get("coverage_state") or "UNKNOWN").upper()

    if status == "OK":
        return "B8_AVAILABLE", "cross-symbol coverage available"
    if coverage == "INSUFFICIENT_CROSS_COVERAGE":
        return "B8_DEGRADED", "cross-symbol coverage insufficient"
    return "B8_UNKNOWN", "cross-symbol state unknown"


def classify_phase(
    ltf: dict[str, Any],
    mtf: dict[str, Any],
    htf: dict[str, Any],
    cockpit: dict[str, Any],
    b8: dict[str, Any],
) -> dict[str, Any]:
    evidence: list[str] = []
    risks: list[str] = []

    ltf_state = str(ltf.get("main_state") or "").upper()
    mtf_state = str(mtf.get("main_state") or "").upper()
    htf_state = str(htf.get("main_state") or "").upper()

    ltf_bias = str(ltf.get("dominant_bias") or "UNKNOWN").upper()
    mtf_bias = str(mtf.get("dominant_bias") or "UNKNOWN").upper()
    htf_bias = str(htf.get("dominant_bias") or "UNKNOWN").upper()

    ltf_fake = str(ltf.get("fake_risk") or "UNKNOWN").upper()
    mtf_fake = str(mtf.get("fake_risk") or "UNKNOWN").upper()
    htf_fake = str(htf.get("fake_risk") or "UNKNOWN").upper()

    cockpit_action = str(cockpit.get("action") or cockpit.get("attention") or "").upper()
    cockpit_state = str(cockpit.get("state") or cockpit.get("synthesis") or "").upper()

    b8_state, b8_phrase = get_b8_state(b8)
    evidence.append(f"LTF={ltf_state} bias={ltf_bias} fake={ltf_fake}")
    evidence.append(f"MTF={mtf_state} bias={mtf_bias} fake={mtf_fake}")
    evidence.append(f"HTF={htf_state} bias={htf_bias} fake={htf_fake}")
    evidence.append(f"Cockpit={_cockpit_evidence(cockpit)}")
    evidence.append(f"B8={b8_state} ({b8_phrase})")

    directional_votes = [b for b in [ltf_bias, mtf_bias, htf_bias] if b in {"PAIR_UP", "PAIR_DOWN"}]
    dominant_bias = "UNKNOWN"
    if directional_votes:
        up = directional_votes.count("PAIR_UP")
        down = directional_votes.count("PAIR_DOWN")
        if up > down:
            dominant_bias = "PAIR_UP"
        elif down > up:
            dominant_bias = "PAIR_DOWN"
        else:
            dominant_bias = "CONFLICT"

    release_count = sum("RELEASE" in s for s in [ltf_state, mtf_state, htf_state])
    compression_count = sum("COMPRESSION" in s or "COMPRESS" in s for s in [ltf_state, mtf_state, htf_state])
    reaction_count = sum("REACTION" in s or "ABSORPTION" in s or "REJECTION" in s for s in [ltf_state, mtf_state, htf_state])

    fake_high = any(x in {"HIGH", "VERY_HIGH"} for x in [ltf_fake, mtf_fake, htf_fake])
    fake_medium = any(x == "MEDIUM" for x in [ltf_fake, mtf_fake, htf_fake])

    aligned = dominant_bias in {"PAIR_UP", "PAIR_DOWN"} and len(set(directional_votes)) == 1
    live_conflict = "CONFLICT" in cockpit_state or dominant_bias == "CONFLICT"

    if release_count >= 2 and aligned and not fake_high:
        phase_state = "RELEASE_VALIDATED"
        attention = "WAKE_TRADER"
        confidence = 0.82 if b8_state == "B8_AVAILABLE" else 0.72
        reading = f"Release multi-TF actif en {dominant_bias}. Flux exploitable, B8={b8_state}."
    elif release_count >= 1 and live_conflict:
        phase_state = "CONFLICT_RELEASE_TEST"
        attention = "WAKE_TRADER"
        confidence = 0.68
        reading = f"Release détecté mais conflit live/structure. Surveiller résolution, absorption ou second leg."
    elif compression_count >= 2 and not fake_high:
        phase_state = "COMPRESSION_REAL_CANDIDATE"
        attention = "WATCH"
        confidence = 0.70 if b8_state == "B8_AVAILABLE" else 0.62
        reading = "Compression multi-TF candidate réelle. Attendre EIE/release ou rupture de densité."
    elif compression_count >= 1 and (fake_high or fake_medium) and b8_state != "B8_AVAILABLE":
        phase_state = "COMPRESSION_FAKE_RISK"
        attention = "WATCH_CONTEXT"
        confidence = 0.58
        reading = "Compression visible mais risque de fake élevé ou couverture B8 insuffisante."
    elif reaction_count >= 1:
        phase_state = "REACTION_ZONE_TEST"
        attention = "WATCH"
        confidence = 0.62
        reading = f"Zone de réaction active. Chercher rejet, absorption, réintégration ou bascule."
    else:
        phase_state = "NO_CLEAR_PHASE"
        attention = "INFO"
        confidence = 0.40
        reading = "Pas de phase dominante nette. Lecture contextuelle seulement."

    if b8_state == "B8_DEGRADED":
        risks.append("B8_INSUFFICIENT_CROSS_PAIR_COVERAGE")
    if fake_high:
        risks.append("HIGH_FAKE_RISK")
    if live_conflict:
        risks.append("LIVE_STRUCTURE_CONFLICT")

    return {
        "phase_state": phase_state,
        "attention": attention,
        "dominant_bias": dominant_bias,
        "confidence": round(confidence, 2),
        "reading": reading,
        "evidence": evidence,
        "technical_risks": risks,
    }


def _cockpit_evidence(cockpit: dict) -> str:
    if not isinstance(cockpit, dict):
        return "UNKNOWN"

    action = (
        cockpit.get("action")
        or cockpit.get("attention")
        or cockpit.get("status")
        or cockpit.get("decision")
        or "UNKNOWN"
    )

    state = (
        cockpit.get("state")
        or cockpit.get("etat")
        or cockpit.get("main_state")
        or cockpit.get("market_state")
        or "UNKNOWN"
    )

    synthesis = (
        cockpit.get("synthesis")
        or cockpit.get("live_synthesis")
        or cockpit.get("multiread_synthesis")
        or cockpit.get("reading_type")
        or "UNKNOWN"
    )

    return f"{action} | {state} | synthesis={synthesis}"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--time-profiles", default="output/dashboard_surface/time_profiles_dashboard.json")
    parser.add_argument("--cockpit", default="output/dashboard_surface/trader_cockpit.json")
    parser.add_argument("--b8", default="output/dashboard_surface/b8_cross_surface.json")
    parser.add_argument("--output", default="output/dashboard_surface/phase_synthesis.json")
    parser.add_argument("--txt", default="output/dashboard_surface/phase_synthesis.txt")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    profiles = load_json(args.time_profiles)
    cockpit = load_json(args.cockpit)
    b8 = load_json(args.b8)

    ltf = first_profile(profiles, "LTF")
    mtf = first_profile(profiles, "MTF")
    htf = first_profile(profiles, "HTF")

    synthesis = classify_phase(ltf, mtf, htf, cockpit, b8)

    data = {
        "method": "PHASE_SYNTHESIS_V738C",
        "timestamp_utc": utc_now(),
        "symbol": args.symbol.upper(),
        **synthesis,
        "inputs": {
            "time_profiles": args.time_profiles,
            "cockpit": args.cockpit,
            "b8": args.b8,
        },
    }

    write_json(args.output, data, pretty=args.pretty)
    write_txt(args.txt, data)

    print(
        f"PHASE_SYNTHESIS_OK | symbol={data['symbol']} | "
        f"attention={data['attention']} | phase={data['phase_state']} | "
        f"bias={data['dominant_bias']} | conf={data['confidence']} | out={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
