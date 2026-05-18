from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0168_B9_GOLDEN_TERRAIN_FIXTURE_BUILDER_V0"

READY_STATES = {"READY_T009_PRECISE", "READY", "READY_FIXTURE", "READY_FOR_FIXTURE"}
REVIEW_STATES = {"REVIEW", "NEEDS_REPLAY_REMAP", "NEEDS_PRECISE_TIME", "FAMILY_ONLY"}

FORBIDDEN_OUTPUT_PATTERNS = [
    re.compile(r"\bprobabilit[eé]\s+de\s+r[eé]ussite\b", re.IGNORECASE),
    re.compile(r"\btaux\s+de\s+r[eé]ussite\b", re.IGNORECASE),
    re.compile(r"\border\s+directionnel\b", re.IGNORECASE),
]

REQUIRED_FIXTURE_FIELDS = [
    "fixture_id",
    "source_case_id",
    "fixture_state",
    "date",
    "time_start",
    "time_end",
    "expected_scene_family",
    "expected_scene_role",
    "expected_price_verdict",
    "expected_retest_state",
    "expected_memory_family",
    "expected_source_limits",
    "acceptance_checks",
    "technical_limits",
]


def _norm_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (key or "").strip().lower()).strip("_")


def _first(row: Dict[str, Any], *names: str, default: str = "") -> str:
    norm = {_norm_key(k): v for k, v in row.items()}
    for name in names:
        val = norm.get(_norm_key(name))
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return default


def _slug(text: str, limit: int = 32) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", text or "CASE").strip("_").upper()
    return value[:limit] or "CASE"


def _stable_id(prefix: str, parts: Iterable[str]) -> str:
    seed = "|".join(str(p or "") for p in parts)
    return f"{prefix}_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10].upper()}"


def _parse_time(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    # Keep exact ISO-like values; they are more useful than over-normalization.
    return text


def _derive_family(label: str, expected: str = "") -> Tuple[str, str, str, str, str]:
    hay = f"{label} {expected}".lower()
    if "raw" in hay and "unavailable" in hay:
        return ("RAW_UNAVAILABLE_REJECTED", "SCENE_BLOCKED_RAW_UNAVAILABLE", "RAW_UNAVAILABLE_REJECTED", "RETEST_NOT_VISIBLE", "MEMORY_REJECTED_RAW_UNAVAILABLE")
    if "effort" in hay and ("sans" in hay or "without" in hay):
        return ("EFFORT_WITHOUT_RESULT_FRICTION_MEMORY", "EFFORT_WITHOUT_RESULT_FRICTION", "PENDING", "RETEST_PENDING", "FRICTION_ABSORPTION_MEMORY")
    if "centre descendant" in hay or "center descending" in hay or "center_migration_down" in hay:
        return ("CENTER_MIGRATION_DOWN_AFTER_RETEST", "CENTER_MIGRATION_DOWN_MEMORY_SHIFT", "ACCEPTED", "RETEST_ACCEPTED", "DIRECTIONAL_PROGRESS_MEMORY")
    if "centre montant" in hay or "center ascending" in hay or "center_migration_up" in hay:
        return ("PROGRESSIVE_WAVE_MEMORY_SHIFT", "CENTER_MIGRATION_UP_MEMORY_SHIFT", "ACCEPTED", "RETEST_ACCEPTED", "DIRECTIONAL_PROGRESS_MEMORY")
    if "vague progressive" in hay or "progressive" in hay:
        return ("PROGRESSIVE_WAVE_MEMORY_SHIFT", "PROGRESSIVE_FIRST_LEG", "ACCEPTED", "RETEST_ACCEPTED", "DIRECTIONAL_PROGRESS_MEMORY")
    if "failed reintegration" in hay or "réintégration échouée" in hay or "reintegration" in hay:
        return ("HIGH_REJECTION_FAILED_REINTEGRATION_SECOND_LEG", "FAILED_REINTEGRATION_NODE", "FAILED_REINTEGRATION", "RETEST_FAILED", "ROTATION_BREATH_MEMORY")
    if "pullback" in hay and ("absor" in hay):
        return ("RELEASE_UP_PULLBACK_ABSORBED", "PULLBACK_ABSORBED_RECONSTRUCTION", "PULLBACK_ABSORBED", "RETEST_ACCEPTED", "FRICTION_ABSORPTION_MEMORY")
    if "zone basse" in hay or "low zone" in hay:
        return ("RELEASE_DOWN_LOW_DEFENDED_REACTION", "LOW_ZONE_DEFENDED_REACTION", "LOWER_ZONE_DEFENDED", "RETEST_ACCEPTED", "ROTATION_BREATH_MEMORY")
    if "rejet haut" in hay or "high rejection" in hay:
        return ("HIGH_REJECTION_FAILED_REINTEGRATION_SECOND_LEG", "HIGH_REJECTION_NODE", "REJECTED", "RETEST_FAILED", "ROTATION_BREATH_MEMORY")
    if "rebond correctif" in hay or "corrective" in hay:
        return ("CORRECTIVE_BREATH_NO_PROGRESS", "CORRECTIVE_BREATH_NO_PROGRESS", "PENDING", "RETEST_PENDING", "ROTATION_BREATH_MEMORY")
    if "release" in hay:
        return ("PROGRESSIVE_WAVE_MEMORY_SHIFT", "PROGRESSIVE_FIRST_LEG", "ACCEPTED", "RETEST_ACCEPTED", "DIRECTIONAL_PROGRESS_MEMORY")
    return ("GOLDEN_TERRAIN_REVIEW_REQUIRED", "SCENE_ROLE_REVIEW_REQUIRED", "PENDING", "RETEST_PENDING", "MEMORY_REVIEW_REQUIRED")


def _fixture_state(status: str, time_start: str, time_end: str, source_limits: str) -> str:
    status_u = (status or "").strip().upper()
    if status_u in READY_STATES and time_start and time_end:
        return "FIXTURE_READY"
    if "RAW_UNAVAILABLE" in (source_limits or "").upper():
        return "FIXTURE_REJECT_RAW_UNAVAILABLE"
    if status_u in REVIEW_STATES or not (time_start and time_end):
        return "FIXTURE_REVIEW_NEEDS_REPLAY_REMAP"
    return "FIXTURE_REVIEW_REQUIRED"


def _make_acceptance_checks(fixture_state: str, scene_role: str, price_verdict: str, retest_state: str, memory_family: str) -> List[str]:
    checks = [
        "moment_count_preserved",
        "forbidden_language_absent",
        "no_execution_decision_fields",
        f"expected_scene_role:{scene_role}",
        f"expected_price_verdict:{price_verdict}",
        f"expected_retest_state:{retest_state}",
        f"expected_memory_family:{memory_family}",
    ]
    if fixture_state == "FIXTURE_READY":
        checks.append("fixture_can_run_as_replay_contract")
    else:
        checks.append("fixture_requires_human_or_replay_alignment_before_strict_test")
    return checks


def load_golden_cases(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Golden cases CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def build_fixtures(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    fixtures: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    review: List[Dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        case_id = _first(row, "case_id", "golden_case_id", "id", default=f"GTC_B9_{index:03d}")
        date = _first(row, "date", "day", default="")
        time_start_raw = _parse_time(_first(row, "time_start", "start", "start_time", "heure_debut", default=""))
        time_end_raw = _parse_time(_first(row, "time_end", "end", "end_time", "heure_fin", default=""))
        time_start = time_start_raw or "TIME_REMAP_REQUIRED"
        time_end = time_end_raw or "TIME_REMAP_REQUIRED"
        status = _first(row, "status", "fixture_state", "readiness", "etat", default="REVIEW")
        label_fr = _first(row, "label_fr", "film_fr", "terrain_case", "description", "case_label", default=case_id)
        expected = _first(row, "expected_label", "expected_scene", "expected_reading", "preuve_b9_attendue", default="")
        source_limits = _first(row, "source_limits", "limits", "limites", "technical_limits", default="Source limits not specified.")
        session = _first(row, "session", "session_phase", default="SESSION_UNKNOWN")
        source_family = _first(row, "source_family", "summary_recovery_type", default="GOLDEN_TERRAIN_CASE")
        source_mode = _first(row, "source_mode", default="REPLAY_GOLDEN_CASE")
        data_visibility = _first(row, "data_visibility", default="READ_ONLY_GOLDEN_FIXTURE")
        scene_family, scene_role, price_verdict, retest_state, memory_family = _derive_family(label_fr, expected)
        state = _fixture_state(status, time_start_raw, time_end_raw, source_limits)
        fixture_id = _stable_id("B9GTF", [case_id, date, time_start, time_end, label_fr])
        tech_limits = [x.strip() for x in re.split(r"[;|]", source_limits) if x.strip()] or [source_limits]
        if not time_start_raw or not time_end_raw:
            tech_limits.append("Horodatage précis requis avant fixture stricte.")
        if "M1_BAR_PROXY" in source_limits or "RECONSTRUCTED" in source_limits:
            tech_limits.append("Source proxy/reconstruite : ne pas durcir en vérité raw.")
        if state == "FIXTURE_REJECT_RAW_UNAVAILABLE":
            tech_limits.append("Raw indisponible : fixture active rejetée, conservation audit seulement.")
        fixture = {
            "fixture_id": fixture_id,
            "source_case_id": case_id,
            "fixture_state": state,
            "date": date,
            "time_start": time_start,
            "time_end": time_end,
            "session": session,
            "label_fr": label_fr,
            "expected_scene_family": scene_family,
            "expected_scene_role": scene_role,
            "expected_price_verdict": price_verdict,
            "expected_retest_state": retest_state,
            "expected_memory_family": memory_family,
            "expected_source_limits": source_limits,
            "source_family": source_family,
            "source_mode": source_mode,
            "data_visibility": data_visibility,
            "acceptance_checks": _make_acceptance_checks(state, scene_role, price_verdict, retest_state, memory_family),
            "technical_limits": tech_limits,
            "fixture_reading_fr": _reading_fr(label_fr, scene_role, price_verdict, state),
            "no_decision_guard": True,
        }
        fixtures.append(fixture)
        if state.startswith("FIXTURE_REJECT"):
            rejected.append(fixture)
        elif state != "FIXTURE_READY":
            review.append(fixture)

    missing_counts: Dict[str, int] = {}
    for f in fixtures:
        for field in REQUIRED_FIXTURE_FIELDS:
            if field not in f or f[field] in (None, "", []):
                missing_counts[field] = missing_counts.get(field, 0) + 1

    state_counts: Dict[str, int] = {}
    family_counts: Dict[str, int] = {}
    for f in fixtures:
        state_counts[f["fixture_state"]] = state_counts.get(f["fixture_state"], 0) + 1
        family_counts[f["expected_scene_family"]] = family_counts.get(f["expected_scene_family"], 0) + 1

    output_text = json.dumps(fixtures, ensure_ascii=False)
    forbidden_hits = [p.pattern for p in FORBIDDEN_OUTPUT_PATTERNS if p.search(output_text)]

    summary = {
        "version": VERSION,
        "fixture_count": len(fixtures),
        "ready_count": state_counts.get("FIXTURE_READY", 0),
        "review_count": len(review),
        "rejected_count": len(rejected),
        "state_counts": state_counts,
        "scene_family_counts": family_counts,
        "missing_required_field_counts": missing_counts,
        "forbidden_language_hits": forbidden_hits,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return {"summary": summary, "fixtures": fixtures, "review": review, "rejected": rejected}


def _reading_fr(label_fr: str, scene_role: str, price_verdict: str, state: str) -> str:
    if state == "FIXTURE_READY":
        prefix = "Fixture prête"
    elif state.startswith("FIXTURE_REJECT"):
        prefix = "Fixture rejetée de l'actif"
    else:
        prefix = "Fixture à revoir"
    return f"{prefix} : {label_fr}. Rôle attendu : {scene_role}. Verdict attendu : {price_verdict}."


def write_outputs(result: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}
    summary = result["summary"]
    fixtures = result["fixtures"]
    review = result["review"]
    rejected = result["rejected"]

    json_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURES_V0.json"
    json_path.write_text(json.dumps({"summary": summary, "fixtures": fixtures}, ensure_ascii=False, indent=2), encoding="utf-8")
    files["json"] = str(json_path)

    csv_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURES_V0.csv"
    _write_csv(csv_path, fixtures)
    files["csv"] = str(csv_path)

    ready_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURES_READY_V0.csv"
    _write_csv(ready_path, [f for f in fixtures if f["fixture_state"] == "FIXTURE_READY"])
    files["ready_csv"] = str(ready_path)

    review_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURES_REVIEW_V0.csv"
    _write_csv(review_path, review)
    files["review_csv"] = str(review_path)

    rejected_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURES_REJECTED_V0.csv"
    _write_csv(rejected_path, rejected)
    files["rejected_csv"] = str(rejected_path)

    md_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURES_V0.md"
    md_path.write_text(_make_md(summary, fixtures, review, rejected), encoding="utf-8")
    files["md"] = str(md_path)

    manifest_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURE_BUILDER_MANIFEST.json"
    manifest = {"version": VERSION, "summary": summary, "files": files}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files["manifest"] = str(manifest_path)

    zip_path = output_dir / "B9_GOLDEN_TERRAIN_FIXTURE_BUILDER_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in [json_path, csv_path, ready_path, review_path, rejected_path, md_path, manifest_path]:
            zf.write(path, arcname=path.name)
    files["zip"] = str(zip_path)
    return files


def _flatten(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, list):
            out[k] = " | ".join(str(x) for x in v)
        elif isinstance(v, dict):
            out[k] = json.dumps(v, ensure_ascii=False)
        else:
            out[k] = v
    return out


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("fixture_id,fixture_state\n", encoding="utf-8")
        return
    flat = [_flatten(r) for r in rows]
    fieldnames = list(dict.fromkeys(k for row in flat for k in row.keys()))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat)


def _make_md(summary: Dict[str, Any], fixtures: List[Dict[str, Any]], review: List[Dict[str, Any]], rejected: List[Dict[str, Any]]) -> str:
    lines = [
        "# B9 Golden Terrain Fixture Builder V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "Une fixture terrain protège une lecture B9 ; elle ne produit pas une décision d'exécution.",
        "",
        "## Counts",
        "",
        f"- Fixtures totales : {summary.get('fixture_count', 0)}",
        f"- READY : {summary.get('ready_count', 0)}",
        f"- REVIEW : {summary.get('review_count', 0)}",
        f"- REJECTED : {summary.get('rejected_count', 0)}",
        f"- Forbidden language hits : {len(summary.get('forbidden_language_hits', []))}",
        "",
        "## Fixtures READY",
        "",
    ]
    for f in fixtures:
        if f["fixture_state"] == "FIXTURE_READY":
            lines += [f"### {f['source_case_id']} — {f['label_fr']}", "", f"- Période : {f['date']} {f['time_start']} → {f['time_end']}", f"- Rôle attendu : `{f['expected_scene_role']}`", f"- Verdict attendu : `{f['expected_price_verdict']}`", f"- Famille mémoire : `{f['expected_memory_family']}`", f"- Limites : {'; '.join(f['technical_limits'])}", ""]
    lines += ["## Fixtures REVIEW", ""]
    for f in review:
        lines += [f"- {f['source_case_id']} — {f['label_fr']} — {f['fixture_state']}"]
    lines += ["", "## Fixtures REJECTED", ""]
    for f in rejected:
        lines += [f"- {f['source_case_id']} — {f['label_fr']} — {f['fixture_state']}"]
    lines += ["", "## Ce que B9 ne doit pas conclure", "", "- Une fixture n'est pas une répétition certaine.", "- Une source proxy ne devient pas une vérité raw.", "- Une scène golden ne devient pas une décision d'exécution.", ""]
    return "\n".join(lines)


def build_from_csv(golden_cases_csv: Path, output_dir: Path) -> Dict[str, Any]:
    rows = load_golden_cases(golden_cases_csv)
    result = build_fixtures(rows)
    files = write_outputs(result, output_dir)
    result["summary"]["files"] = files
    return result
