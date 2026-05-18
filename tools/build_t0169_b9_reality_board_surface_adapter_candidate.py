#!/usr/bin/env python3
"""T0169 - B9 Reality Board dashboard surfaces recovery/regeneration.

Read-only surface builder:
- reads available B9 JSON/CSV outputs from the filesystem;
- produces a dashboard read model, a human scene panel candidate and a surface adapter payload;
- never writes to databases;
- never triggers live cockpit, Telegram, or execution logic.

Doctrine:
    The dashboard displays. It does not decide.
    Comparing is not predicting.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


VERSION = "T0169_B9_REALITY_BOARD_DASHBOARD_SURFACES_V0"
READ_MODEL_DIR = "b9_reality_board_read_model_v01"
SCENE_PANEL_DIR = "b9_reality_board_scene_panel_candidate_v01"
SURFACE_ADAPTER_DIR = "b9_reality_board_surface_adapter_candidate_v0"

READ_MODEL_FILE = "B9_REALITY_BOARD_READ_MODEL_V01.json"
SCENE_PANEL_FILE = "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json"
SURFACE_ADAPTER_FILE = "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json"

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "_extract",
    "_tmp",
    "tmp",
}


INPUT_SPECS: Dict[str, Sequence[str]] = {
    "reality_board_integration_candidate": (
        "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
        "B9_REALITY_BOARD_INTEGRATION_CANDIDATE*.json",
    ),
    "market_compare_board": (
        "B9_MARKET_COMPARE_BOARD_V0.json",
        "B9_MARKET_COMPARE_BOARD*.json",
    ),
    "market_compare_matches": (
        "B9_MARKET_COMPARE_BOARD_MATCHES_V0.csv",
        "B9_MARKET_COMPARE_BOARD_V0_MATCHES_V0.csv",
        "*MARKET_COMPARE*MATCHES*.csv",
    ),
    "market_compare_differences": (
        "B9_MARKET_COMPARE_BOARD_DIFFERENCES_V0.csv",
        "B9_MARKET_COMPARE_BOARD_V0_DIFFERENCES_V0.csv",
        "*MARKET_COMPARE*DIFFERENCES*.csv",
    ),
    "market_compare_technical_risks": (
        "B9_MARKET_COMPARE_BOARD_TECHNICAL_RISKS_V0.csv",
        "B9_MARKET_COMPARE_BOARD_V0_TECHNICAL_RISKS_V0.csv",
        "*MARKET_COMPARE*TECHNICAL_RISKS*.csv",
    ),
    "t0167_b9_b6_realignment": (
        "T0167_B9_B6_REALIGNMENT_V0.json",
        "B9_B6_REALIGNMENT_V0.json",
        "*T0167*REALIGNMENT*.json",
        "*B9*B6*REALIGNMENT*.json",
    ),
    "trader_attention_packet": (
        "B9_TRADER_ATTENTION_PACKET_V0.json",
        "*TRADER_ATTENTION_PACKET*.json",
    ),
    "live_brief_once": (
        "B9_LIVE_BRIEF_ONCE_V0.json",
        "*LIVE_BRIEF_ONCE*.json",
    ),
    "human_terrain_synthesis": (
        "B9_HUMAN_TERRAIN_SYNTHESIS_V0.json",
        "*HUMAN_TERRAIN_SYNTHESIS*.json",
    ),
    "memory_confidence_ladder": (
        "B9_MEMORY_CONFIDENCE_LADDER_V0.json",
        "*MEMORY_CONFIDENCE_LADDER*.json",
    ),
    "false_positive_memory_explainer": (
        "B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.json",
        "*FALSE_POSITIVE_MEMORY_EXPLAINER*.json",
        "*FALSE_POSITIVE_CONTEXT*.json",
    ),
}


@dataclass(frozen=True)
class InputRecord:
    key: str
    path: Optional[Path]
    found: bool
    data_type: str
    rows: int = 0
    load_error: Optional[str] = None


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        parts: List[str] = []
        for k, v in value.items():
            if len(parts) >= 12:
                break
            nv = norm_text(v)
            if nv:
                parts.append(f"{k}: {nv}")
        return " | ".join(parts)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return " | ".join(norm_text(v) for v in value if norm_text(v))
    return str(value).strip()


def tokenize(value: Any) -> List[str]:
    text = norm_text(value).lower()
    return [t for t in re.split(r"[^a-z0-9_]+", text) if len(t) >= 3]


def first_non_empty(*values: Any, default: str = "UNKNOWN") -> str:
    for value in values:
        text = norm_text(value)
        if text:
            return text
    return default


def deep_get(data: Any, paths: Sequence[str], default: Any = None) -> Any:
    for path in paths:
        node = data
        ok = True
        for part in path.split("."):
            if isinstance(node, Mapping) and part in node:
                node = node[part]
            elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)) and part.isdigit():
                idx = int(part)
                if idx < len(node):
                    node = node[idx]
                else:
                    ok = False
                    break
            else:
                ok = False
                break
        if ok and node not in (None, "", [], {}):
            return node
    return default


def should_skip_dir(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def candidate_roots(core_root: Path, input_root: Optional[Path]) -> List[Path]:
    roots: List[Path] = []
    if input_root:
        roots.append(input_root)
    preferred = [
        core_root / "outputs",
        core_root / "Docs" / "Reports",
        core_root / "samples",
        core_root / "Docs",
        core_root,
    ]
    for root in preferred:
        if root.exists() and root not in roots:
            roots.append(root)
    return roots


def score_path(path: Path) -> Tuple[int, float, int]:
    norm = str(path).replace("\\", "/").lower()
    score = 0
    if "/outputs/" in norm:
        score += 100
    if "/docs/reports/" in norm:
        score += 60
    if "/samples/" in norm:
        score += 20
    if "sample" in path.name.lower():
        score -= 10
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return (score, mtime, -len(norm))


def safe_rglob(root: Path, pattern: str) -> Iterable[Path]:
    try:
        iterator = root.rglob(pattern)
        for path in iterator:
            if not path.is_file():
                continue
            if should_skip_dir(path.relative_to(root)) if path.is_relative_to(root) else should_skip_dir(path):
                continue
            yield path
    except Exception:
        return


def find_input_file(core_root: Path, input_root: Optional[Path], patterns: Sequence[str]) -> Optional[Path]:
    matches: List[Path] = []
    seen = set()
    for root in candidate_roots(core_root, input_root):
        for pattern in patterns:
            for path in safe_rglob(root, pattern):
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                matches.append(path)
    if not matches:
        return None
    matches.sort(key=score_path, reverse=True)
    return matches[0]


def load_json(path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
        if isinstance(value, dict):
            return value, None
        return {"items": value}, None
    except Exception as exc:
        return {}, f"{type(exc).__name__}: {exc}"


def load_csv(path: Path) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def discover_inputs(core_root: Path, input_root: Optional[Path]) -> Tuple[Dict[str, InputRecord], Dict[str, Any]]:
    records: Dict[str, InputRecord] = {}
    payloads: Dict[str, Any] = {}
    for key, patterns in INPUT_SPECS.items():
        path = find_input_file(core_root, input_root, patterns)
        if path is None:
            records[key] = InputRecord(key=key, path=None, found=False, data_type="missing")
            payloads[key] = None
            continue

        suffix = path.suffix.lower()
        if suffix == ".json":
            data, err = load_json(path)
            records[key] = InputRecord(
                key=key,
                path=path,
                found=err is None,
                data_type="json",
                rows=1 if err is None else 0,
                load_error=err,
            )
            payloads[key] = data if err is None else None
        elif suffix == ".csv":
            rows, err = load_csv(path)
            records[key] = InputRecord(
                key=key,
                path=path,
                found=err is None,
                data_type="csv",
                rows=len(rows),
                load_error=err,
            )
            payloads[key] = rows if err is None else None
        else:
            records[key] = InputRecord(key=key, path=path, found=False, data_type=suffix or "unknown", load_error="unsupported file type")
            payloads[key] = None
    return records, payloads


def flatten_strings(value: Any, limit: int = 80) -> List[str]:
    out: List[str] = []

    def visit(node: Any) -> None:
        if len(out) >= limit:
            return
        if isinstance(node, str):
            if node.strip():
                out.append(node.strip())
        elif isinstance(node, Mapping):
            for v in node.values():
                visit(v)
                if len(out) >= limit:
                    break
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for item in node:
                visit(item)
                if len(out) >= limit:
                    break

    visit(value)
    return out


def summarize_source_quality(payloads: Mapping[str, Any], records: Mapping[str, InputRecord]) -> Dict[str, Any]:
    quality_terms: List[str] = []
    for key in ("reality_board_integration_candidate", "market_compare_board", "t0167_b9_b6_realignment", "trader_attention_packet", "live_brief_once"):
        data = payloads.get(key)
        if not isinstance(data, Mapping):
            continue
        for path in (
            "source_quality",
            "source_quality_summary",
            "data_visibility",
            "technical_context.source_quality",
            "metadata.source_quality",
            "board.source_quality",
        ):
            value = deep_get(data, [path])
            if value:
                quality_terms.append(norm_text(value))

    found_count = sum(1 for r in records.values() if r.found)
    missing_count = sum(1 for r in records.values() if not r.found)
    if quality_terms:
        label = first_non_empty(*quality_terms, default="SOURCE_QUALITY_PRESENT")
    elif found_count == 0:
        label = "NO_SOURCE_INPUTS_FOUND"
    elif missing_count:
        label = "SOURCE_QUALITY_PARTIAL"
    else:
        label = "SOURCE_QUALITY_AVAILABLE"

    return {
        "label": label,
        "found_inputs": found_count,
        "missing_inputs": missing_count,
        "source_notes": quality_terms[:8],
    }


def extract_rows_as_list(payloads: Mapping[str, Any], key: str, limit: int = 12) -> List[Dict[str, Any]]:
    rows = payloads.get(key)
    if isinstance(rows, list):
        return [dict(row) for row in rows[:limit] if isinstance(row, Mapping)]
    return []


def collect_technical_risks(payloads: Mapping[str, Any], records: Mapping[str, InputRecord]) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []

    for row in extract_rows_as_list(payloads, "market_compare_technical_risks", limit=20):
        risks.append({
            "source": "market_compare_technical_risks",
            "risk": first_non_empty(row.get("risk"), row.get("technical_risk"), row.get("label"), row.get("name"), default="TECHNICAL_RISK"),
            "details": first_non_empty(row.get("details"), row.get("description"), row.get("reason"), row, default=""),
        })

    for key in ("market_compare_board", "t0167_b9_b6_realignment", "reality_board_integration_candidate", "trader_attention_packet"):
        data = payloads.get(key)
        if not isinstance(data, Mapping):
            continue
        values = deep_get(data, ["technical_risks", "risks", "technical_limits", "limits"], default=[])
        if isinstance(values, str):
            values = [values]
        if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
            for item in values[:20]:
                risks.append({
                    "source": key,
                    "risk": first_non_empty(deep_get(item, ["risk", "label", "name"], default=None), item, default="TECHNICAL_RISK"),
                    "details": first_non_empty(deep_get(item, ["details", "description", "reason"], default=None), item, default=""),
                })

    for key, rec in records.items():
        if rec.load_error:
            risks.append({"source": key, "risk": "INPUT_LOAD_ERROR", "details": rec.load_error})

    # Deduplicate while preserving order.
    dedup: List[Dict[str, Any]] = []
    seen = set()
    for risk in risks:
        ident = (risk.get("source"), risk.get("risk"), risk.get("details"))
        if ident in seen:
            continue
        seen.add(ident)
        dedup.append(risk)
    return dedup[:30]


def collect_missing_inputs(records: Mapping[str, InputRecord]) -> List[str]:
    return [key for key, rec in records.items() if not rec.found]


def readiness(records: Mapping[str, InputRecord], risks: Sequence[Mapping[str, Any]]) -> str:
    primary = any(records.get(k) and records[k].found for k in (
        "reality_board_integration_candidate",
        "trader_attention_packet",
        "live_brief_once",
        "market_compare_board",
        "t0167_b9_b6_realignment",
    ))
    if not primary:
        return "PARTIAL"
    missing = collect_missing_inputs(records)
    if len(missing) >= 5:
        return "PARTIAL"
    if risks:
        return "READY_WITH_WARNINGS"
    return "READY"


def extract_candidate_id(payloads: Mapping[str, Any]) -> str:
    for key in ("reality_board_integration_candidate", "trader_attention_packet", "live_brief_once", "t0167_b9_b6_realignment", "market_compare_board"):
        data = payloads.get(key)
        if isinstance(data, Mapping):
            value = deep_get(data, [
                "candidate_id",
                "candidate.candidate_id",
                "latest_candidate.candidate_id",
                "scene.candidate_id",
                "metadata.candidate_id",
            ])
            if value:
                return norm_text(value)
    return "UNKNOWN_CANDIDATE"


def extract_scene_state(payloads: Mapping[str, Any]) -> str:
    for key in ("reality_board_integration_candidate", "live_brief_once", "trader_attention_packet", "human_terrain_synthesis", "market_compare_board"):
        data = payloads.get(key)
        if isinstance(data, Mapping):
            value = deep_get(data, [
                "scene_state",
                "current_scene",
                "scene.current_scene",
                "scene.scene_state",
                "film_state",
                "state",
                "board.current_scene",
            ])
            if value:
                return norm_text(value)
    return "SCENE_NOT_AVAILABLE"


def extract_memory_family(payloads: Mapping[str, Any]) -> str:
    for key in ("t0167_b9_b6_realignment", "market_compare_board", "memory_confidence_ladder", "human_terrain_synthesis"):
        data = payloads.get(key)
        if isinstance(data, Mapping):
            value = deep_get(data, [
                "memory_family",
                "family",
                "top_match.memory_family",
                "top_match.family",
                "alignment.memory_family",
                "board.memory_family",
            ])
            if value:
                return norm_text(value)
    rows = extract_rows_as_list(payloads, "market_compare_matches", limit=1)
    if rows:
        return first_non_empty(rows[0].get("memory_family"), rows[0].get("family"), rows[0].get("film_family"), default="MEMORY_FAMILY_FROM_MATCHES")
    return "MEMORY_FAMILY_NOT_AVAILABLE"


def extract_top_match(payloads: Mapping[str, Any]) -> Dict[str, Any]:
    realignment = payloads.get("t0167_b9_b6_realignment")
    if isinstance(realignment, Mapping):
        candidate = deep_get(realignment, ["top_match", "alignment.top_match", "matches.0"], default=None)
        if isinstance(candidate, Mapping):
            return dict(candidate)
        film_id = deep_get(realignment, ["top_match_film_id", "alignment.top_match_film_id"])
        if film_id:
            return {"film_id": film_id, "source": "t0167_b9_b6_realignment"}

    board = payloads.get("market_compare_board")
    if isinstance(board, Mapping):
        candidate = deep_get(board, ["top_match", "matches.0", "board.top_match"], default=None)
        if isinstance(candidate, Mapping):
            return dict(candidate)
        film = deep_get(board, ["top_match_film_id", "top_match"], default=None)
        if film:
            return {"film_id": film, "source": "market_compare_board"}

    rows = extract_rows_as_list(payloads, "market_compare_matches", limit=1)
    if rows:
        return dict(rows[0])
    return {}


def extract_panel_field(payloads: Mapping[str, Any], names: Sequence[str], default: str) -> str:
    for key in ("reality_board_integration_candidate", "trader_attention_packet", "live_brief_once", "human_terrain_synthesis", "market_compare_board", "t0167_b9_b6_realignment"):
        data = payloads.get(key)
        if isinstance(data, Mapping):
            value = deep_get(data, names)
            if value:
                return norm_text(value)
    return default


def build_technical_limits(records: Mapping[str, InputRecord], risks: Sequence[Mapping[str, Any]]) -> List[str]:
    limits: List[str] = [
        "Dashboard surface only: display layer, no decision layer.",
        "Read-only filesystem generation; no database write.",
        "No live cockpit activation.",
        "No Telegram emission.",
        "Comparison is contextual memory alignment, not prediction.",
    ]
    missing = collect_missing_inputs(records)
    if missing:
        limits.append("Missing inputs reduce display readiness: " + ", ".join(missing[:12]))
    if risks:
        limits.append("Technical risks require visible dashboard warning badges.")
    return limits


def input_inventory(records: Mapping[str, InputRecord], core_root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key, rec in records.items():
        path_text = None
        if rec.path:
            try:
                path_text = str(rec.path.resolve().relative_to(core_root.resolve()))
            except Exception:
                path_text = str(rec.path)
        rows.append({
            "input_key": key,
            "found": rec.found,
            "path": path_text,
            "data_type": rec.data_type,
            "rows": rec.rows,
            "load_error": rec.load_error,
        })
    return rows


def build_read_model(core_root: Path, records: Mapping[str, InputRecord], payloads: Mapping[str, Any]) -> Dict[str, Any]:
    risks = collect_technical_risks(payloads, records)
    source_quality = summarize_source_quality(payloads, records)
    top_match = extract_top_match(payloads)
    model = {
        "version": VERSION,
        "surface": "B9_REALITY_BOARD_READ_MODEL_V01",
        "generated_at_utc": utc_now(),
        "display_doctrine": "Dashboard displays; it does not decide.",
        "display_readiness": readiness(records, risks),
        "candidate_id": extract_candidate_id(payloads),
        "scene_state": extract_scene_state(payloads),
        "source_quality": source_quality.get("label"),
        "source_quality_summary": source_quality,
        "data_visibility": extract_panel_field(payloads, ["data_visibility", "source_quality.data_visibility", "visibility"], "DATA_VISIBILITY_NOT_AVAILABLE"),
        "memory_family": extract_memory_family(payloads),
        "top_memory_match": top_match,
        "latest_available_outputs": [
            item["input_key"] for item in input_inventory(records, core_root) if item["found"]
        ],
        "missing_inputs": collect_missing_inputs(records),
        "technical_risks": risks,
        "technical_limits": build_technical_limits(records, risks),
        "input_inventory": input_inventory(records, core_root),
    }
    return model


def make_section(title: str, value: str, status: str = "INFO") -> Dict[str, str]:
    return {"title": title, "value": value, "status": status}


def build_scene_panel(read_model: Mapping[str, Any], payloads: Mapping[str, Any]) -> Dict[str, Any]:
    risks = read_model.get("technical_risks") or []
    top_match = read_model.get("top_memory_match") if isinstance(read_model.get("top_memory_match"), Mapping) else {}
    top_match_label = first_non_empty(
        deep_get(top_match, ["film_id", "film_name", "case_id", "name", "title"], default=None),
        default="AUCUN_FILM_PROCHE_CONFIRME",
    )

    sections = [
        make_section("Scène actuelle", str(read_model.get("scene_state") or "SCENE_NOT_AVAILABLE"), "PRIMARY"),
        make_section("Famille mémoire", str(read_model.get("memory_family") or "MEMORY_FAMILY_NOT_AVAILABLE"), "INFO"),
        make_section("Film proche", top_match_label, "INFO"),
        make_section("Zone active", extract_panel_field(payloads, ["current_zone", "zone", "scene.current_zone", "active_zone"], "ZONE_NOT_AVAILABLE"), "INFO"),
        make_section("Session", extract_panel_field(payloads, ["session", "session_phase", "scene.session", "context.session"], "SESSION_NOT_AVAILABLE"), "INFO"),
        make_section("Retest", extract_panel_field(payloads, ["retest", "retest_state", "scene.retest", "retest_source"], "RETEST_NOT_AVAILABLE"), "INFO"),
        make_section("Center path", extract_panel_field(payloads, ["center_path", "center_path_state", "scene.center_path"], "CENTER_PATH_NOT_AVAILABLE"), "INFO"),
        make_section(
            "Pièges techniques",
            "; ".join(first_non_empty(r.get("risk"), r, default="TECHNICAL_RISK") for r in risks[:6]) if risks else "AUCUN_PIEGE_TECHNIQUE_EXPLICITE",
            "WARNING" if risks else "INFO",
        ),
        make_section(
            "Ce que B9 ne peut pas conclure",
            "B9 ne conclut pas une action. Il affiche la scène, les rapprochements mémoire et les limites techniques.",
            "LIMIT",
        ),
    ]

    return {
        "version": VERSION,
        "surface": "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01",
        "generated_at_utc": utc_now(),
        "display_readiness": read_model.get("display_readiness", "PARTIAL"),
        "candidate_id": read_model.get("candidate_id", "UNKNOWN_CANDIDATE"),
        "panel_language": "fr_trader_sober",
        "headline": f"{read_model.get('scene_state', 'SCENE_NOT_AVAILABLE')} | {read_model.get('memory_family', 'MEMORY_FAMILY_NOT_AVAILABLE')}",
        "sections": sections,
        "technical_limits": read_model.get("technical_limits", []),
    }


def badge(label: str, level: str) -> Dict[str, str]:
    return {"label": label, "level": level}


def build_surface_adapter(read_model: Mapping[str, Any], scene_panel: Mapping[str, Any]) -> Dict[str, Any]:
    readiness_value = str(read_model.get("display_readiness", "PARTIAL"))
    badges = [
        badge(readiness_value, "warning" if readiness_value == "PARTIAL" else "info"),
        badge(str(read_model.get("source_quality", "SOURCE_UNKNOWN")), "info"),
        badge("DISPLAY_ONLY", "limit"),
        badge("NO_DECISION_LAYER", "limit"),
    ]

    warnings = []
    for risk in (read_model.get("technical_risks") or [])[:10]:
        if isinstance(risk, Mapping):
            warnings.append({
                "label": first_non_empty(risk.get("risk"), default="TECHNICAL_RISK"),
                "details": first_non_empty(risk.get("details"), default=""),
                "source": first_non_empty(risk.get("source"), default="unknown"),
            })

    cards = []
    for section in scene_panel.get("sections", []):
        cards.append({
            "card_id": re.sub(r"[^a-z0-9]+", "_", section.get("title", "card").lower()).strip("_"),
            "title": section.get("title", "Card"),
            "body": section.get("value", ""),
            "status": section.get("status", "INFO"),
        })

    return {
        "version": VERSION,
        "surface": "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0",
        "generated_at_utc": utc_now(),
        "status": readiness_value,
        "display_contract": {
            "role": "dashboard_surface_adapter",
            "decision_layer": False,
            "live_cockpit_activation": False,
            "telegram_emission": False,
            "database_write": False,
        },
        "source_quality_summary": read_model.get("source_quality_summary", {}),
        "badges": badges,
        "cards": cards,
        "warnings": warnings,
        "sections": scene_panel.get("sections", []),
        "technical_limits": read_model.get("technical_limits", []),
        "missing_inputs": read_model.get("missing_inputs", []),
    }


def write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def write_inventory_csv(path: Path, records: Mapping[str, InputRecord], core_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["input_key", "found", "path", "data_type", "rows", "load_error"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in input_inventory(records, core_root):
            writer.writerow(row)


def zip_outputs(output_root: Path) -> Path:
    zip_path = output_root / "T0169_B9_REALITY_BOARD_DASHBOARD_SURFACES_V0.zip"
    targets = [
        output_root / READ_MODEL_DIR / READ_MODEL_FILE,
        output_root / SCENE_PANEL_DIR / SCENE_PANEL_FILE,
        output_root / SURFACE_ADAPTER_DIR / SURFACE_ADAPTER_FILE,
        output_root / "T0169_B9_REALITY_BOARD_DASHBOARD_SURFACES_INPUTS.csv",
    ]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for target in targets:
            if target.exists():
                archive.write(target, arcname=str(target.relative_to(output_root)))
    return zip_path


def build_surfaces(core_root: Path, output_root: Path, input_root: Optional[Path]) -> Dict[str, Any]:
    records, payloads = discover_inputs(core_root, input_root)

    read_model = build_read_model(core_root, records, payloads)
    scene_panel = build_scene_panel(read_model, payloads)
    surface_adapter = build_surface_adapter(read_model, scene_panel)

    read_model_path = output_root / READ_MODEL_DIR / READ_MODEL_FILE
    scene_panel_path = output_root / SCENE_PANEL_DIR / SCENE_PANEL_FILE
    surface_adapter_path = output_root / SURFACE_ADAPTER_DIR / SURFACE_ADAPTER_FILE
    inventory_path = output_root / "T0169_B9_REALITY_BOARD_DASHBOARD_SURFACES_INPUTS.csv"

    write_json(read_model_path, read_model)
    write_json(scene_panel_path, scene_panel)
    write_json(surface_adapter_path, surface_adapter)
    write_inventory_csv(inventory_path, records, core_root)
    zip_path = zip_outputs(output_root)

    return {
        "version": VERSION,
        "display_readiness": read_model["display_readiness"],
        "candidate_id": read_model["candidate_id"],
        "scene_state": read_model["scene_state"],
        "outputs": {
            "read_model": str(read_model_path),
            "scene_panel": str(scene_panel_path),
            "surface_adapter": str(surface_adapter_path),
            "input_inventory": str(inventory_path),
            "zip": str(zip_path),
        },
        "missing_inputs": read_model["missing_inputs"],
        "technical_limits": read_model["technical_limits"],
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build T0169 B9 dashboard read model, scene panel and surface adapter payloads.")
    parser.add_argument("--core-root", default=".", help="PowerFlow core root. Default: current directory.")
    parser.add_argument("--input-root", default=None, help="Optional root to prefer when discovering B9 inputs.")
    parser.add_argument("--output-root", default="outputs", help="Output root directory. Default: outputs.")
    parser.add_argument("--strict-exit", action="store_true", help="Return non-zero when no primary B9 input is found.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    core_root = Path(args.core_root).resolve()
    input_root = Path(args.input_root).resolve() if args.input_root else None
    output_root = Path(args.output_root).resolve()

    result = build_surfaces(core_root=core_root, output_root=output_root, input_root=input_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.strict_exit and result["display_readiness"] == "PARTIAL" and len(result["missing_inputs"]) == len(INPUT_SPECS):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
