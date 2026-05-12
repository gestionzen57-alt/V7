from pathlib import Path

path = Path("pf_evidence_bus_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_visual_neutralize_v739d")
backup.write_text(text, encoding="utf-8")

old = '''def write_txt(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"EVIDENCE BUS | {data.get('symbol')} | {data.get('global_attention')} | {data.get('dominant_phase')}",
        f"bias={data.get('dominant_bias')}",
        f"confidence={data.get('confidence')}",
        "",
        "EVIDENCE",
    ]

    for e in data.get("evidence", []):
        details = e.get("details") or {}
        extra = ""
        if details.get("fake_risk"):
            extra += f" fake={details.get('fake_risk')}"
        if details.get("coverage"):
            extra += f" coverage={details.get('coverage')}"
        if details.get("last_event"):
            le = details.get("last_event") or {}
            extra += f" last={le.get('timeframe')}/{le.get('event_type')}/price={le.get('price')}"
        lines.append(
            f"- {e.get('layer')}: {e.get('attention')} | {e.get('state')} | "
            f"{e.get('bias')} | w={e.get('weight')}{extra}"
        )
        msg = str(e.get("message") or "").strip()
        if msg:
            lines.append(f"  message={msg}")

    risks = data.get("technical_risks") or []
    if risks:
        lines += ["", "TECHNICAL RISKS"]
        for r in risks:
            lines.append(f"- {r}")

    p.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
'''

new = '''def visual_weight(e: dict[str, Any]) -> tuple[float, str]:
    layer = str(e.get("layer") or "").upper()
    state = str(e.get("state") or "").upper()
    weight = as_float(e.get("weight"), 0.0)

    if layer == "PHASE_SYNTHESIS" and state in {"NO_CLEAR_PHASE", "MIXED_PHASE", "UNKNOWN"}:
        return 0.0, "neutralized=derived_phase_unclear"

    if layer == "B8_CROSS_SYMBOL" and state in {"DEGRADED", "MISSING", "UNKNOWN"}:
        return 0.0, "neutralized=cross_coverage_degraded"

    return weight, ""


def write_txt(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"EVIDENCE BUS | {data.get('symbol')} | {data.get('global_attention')} | {data.get('dominant_phase')}",
        f"bias={data.get('dominant_bias')}",
        f"confidence={data.get('confidence')}",
        "",
        "EVIDENCE",
    ]

    for e in data.get("evidence", []):
        details = e.get("details") or {}
        vw, neutralized = visual_weight(e)

        extra = ""
        if neutralized:
            extra += f" {neutralized}"
        if details.get("fake_risk"):
            extra += f" fake={details.get('fake_risk')}"
        if details.get("coverage"):
            extra += f" coverage={details.get('coverage')}"
        if details.get("last_event"):
            le = details.get("last_event") or {}
            extra += f" last={le.get('timeframe')}/{le.get('event_type')}/price={le.get('price')}"

        lines.append(
            f"- {e.get('layer')}: {e.get('attention')} | {e.get('state')} | "
            f"{e.get('bias')} | w={vw}{extra}"
        )

        msg = str(e.get("message") or "").strip()
        if msg:
            lines.append(f"  message={msg}")

    risks = data.get("technical_risks") or []
    if risks:
        lines += ["", "TECHNICAL RISKS"]
        for r in risks:
            lines.append(f"- {r}")

    p.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | write_txt block not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | visual neutralization installed | backup={backup.name}")
