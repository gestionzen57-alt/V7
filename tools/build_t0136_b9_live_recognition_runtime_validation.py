#!/usr/bin/env python3
"""
T0136 — B9 Live Recognition Loop Runtime Validation V0

Read-only runtime validator for T0135 B9 Live Scene Recognition Loop.
It verifies that the local Core contains the required T0135 runtime inputs,
optionally executes the T0135 CLI when available, and writes a transparent
validation report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_V0"

FORBIDDEN_PATTERNS = [
    r"\bBUY_SIGNAL\b",
    r"\bSELL_SIGNAL\b",
    r"\bACHETER\b",
    r"\bVENDRE\b",
    r"\bprobability_of_success\b",
    r"\btaux de réussite\b",
]

EXPECTED_INPUTS = {
    "live_scene_json": [
        "outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json",
        "outputs/b6_live_scene_adapter_v0_install_validation/B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json",
    ],
    "similarity_query_json": [
        "outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.json",
        "outputs/b6_live_scene_adapter_v0_t0115_query_validation/B6_SIMILARITY_QUERY_RESULT_V0.json",
        "outputs/b6_live_scene_adapter_v0_t0115_git_validation/B6_SIMILARITY_QUERY_RESULT_V0.json",
    ],
    "false_positive_json": [
        "outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.json",
    ],
    "terrain_synthesis_json": [
        "outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_SYNTHESIS_V0.json",
    ],
    "french_report_json": [
        "outputs/b9_french_trader_scene_report_v0/B9_FRENCH_TRADER_SCENE_REPORT_V0.json",
    ],
}

SAMPLE_INPUTS = {
    "live_scene_json": "sample_b9_live_scene_query_payload.json",
    "similarity_query_json": "sample_t0115_similarity_query_result.json",
    "false_positive_json": "sample_t0117_false_positive_context.json",
    "terrain_synthesis_json": "sample_t0118_human_terrain_synthesis.json",
    "french_report_json": "sample_b9_french_trader_scene_report.json",
    "precomputed_t0135_result_json": "sample_t0135_live_recognition_result.json",
}

T0135_CLI = "tools/build_t0135_b9_live_scene_recognition_loop.py"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def flatten_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for value in obj.values():
            yield from flatten_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from flatten_strings(value)
    elif isinstance(obj, str):
        yield obj


def forbidden_hits(*objects: Any) -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    for obj_index, obj in enumerate(objects):
        for text in flatten_strings(obj):
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    hits.append({"object_index": str(obj_index), "pattern": pattern, "text_excerpt": text[:160]})
    return hits


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class InputRecord:
    input_name: str
    required: bool
    found: bool
    path: str
    mode: str
    sha256: str = ""
    note: str = ""


@dataclass
class CheckRecord:
    check_name: str
    state: str
    severity: str
    detail: str


def resolve_runtime_inputs(core_root: Path) -> Tuple[Dict[str, Path], List[InputRecord]]:
    resolved: Dict[str, Path] = {}
    records: List[InputRecord] = []
    for name, candidates in EXPECTED_INPUTS.items():
        found_path: Optional[Path] = None
        for rel in candidates:
            path = core_root / rel
            if path.exists():
                found_path = path
                break
        if found_path is None:
            records.append(InputRecord(name, True, False, "", "runtime", note="missing_runtime_input"))
        else:
            resolved[name] = found_path
            records.append(InputRecord(name, True, True, str(found_path), "runtime", sha256=file_sha256(found_path)))
    return resolved, records


def resolve_sample_inputs(sample_dir: Path) -> Tuple[Dict[str, Path], List[InputRecord]]:
    resolved: Dict[str, Path] = {}
    records: List[InputRecord] = []
    for name, filename in SAMPLE_INPUTS.items():
        path = sample_dir / filename
        required = name != "precomputed_t0135_result_json"
        found = path.exists()
        if found:
            resolved[name] = path
        records.append(InputRecord(name, required, found, str(path) if found else "", "sample", sha256=file_sha256(path) if found else "", note="sample_fixture"))
    return resolved, records


def load_inputs(paths: Dict[str, Path]) -> Dict[str, Any]:
    loaded: Dict[str, Any] = {}
    for name, path in paths.items():
        if name.endswith("_json"):
            loaded[name] = read_json(path)
    return loaded


def summarize_t0135_result(result: Dict[str, Any]) -> Dict[str, Any]:
    matches = result.get("matches") or result.get("nearest_films") or result.get("memory_matches") or []
    if not isinstance(matches, list):
        matches = []
    top_film_id = ""
    if matches:
        first = matches[0]
        if isinstance(first, dict):
            top_film_id = str(first.get("film_id") or first.get("match_film_id") or first.get("id") or "")
    return {
        "recognition_state": result.get("recognition_state") or result.get("state") or "B9_LIVE_SCENE_RECOGNITION_RESULT_LOADED",
        "match_count": int(result.get("match_count", len(matches)) or 0),
        "top_match_film_id": str(result.get("top_match_film_id") or top_film_id),
        "cross_family_match_count": int(result.get("cross_family_match_count", 0) or 0),
        "low_trust_in_results": bool(result.get("low_trust_in_results", False)),
        "raw_unavailable_in_results": bool(result.get("raw_unavailable_in_results", False)),
        "false_positive_context_available": bool(result.get("false_positive_context_available", False)),
        "terrain_synthesis_available": bool(result.get("terrain_synthesis_available", False)),
    }


def run_t0135_cli(core_root: Path, inputs: Dict[str, Path], output_dir: Path, top_k: int) -> Tuple[Optional[Dict[str, Any]], List[CheckRecord]]:
    checks: List[CheckRecord] = []
    cli_path = core_root / T0135_CLI
    if not cli_path.exists():
        checks.append(CheckRecord("t0135_cli_present", "WARN", "BLOCKING_FOR_RUNTIME_EXECUTION", f"Missing {T0135_CLI}"))
        return None, checks

    run_dir = output_dir / "T0135_RUNTIME_EXECUTION"
    cmd = [
        sys.executable,
        str(cli_path),
        "--live-scene-json", str(inputs["live_scene_json"]),
        "--similarity-query-json", str(inputs["similarity_query_json"]),
        "--false-positive-json", str(inputs["false_positive_json"]),
        "--terrain-synthesis-json", str(inputs["terrain_synthesis_json"]),
        "--french-report-json", str(inputs["french_report_json"]),
        "--output-dir", str(run_dir),
        "--top-k", str(top_k),
    ]
    proc = subprocess.run(cmd, cwd=str(core_root), capture_output=True, text=True)
    checks.append(CheckRecord("t0135_cli_execution", "PASS" if proc.returncode == 0 else "FAIL", "P0", (proc.stdout + "\n" + proc.stderr)[-1200:]))
    if proc.returncode != 0:
        return None, checks

    result_candidates = [
        run_dir / "B9_LIVE_SCENE_RECOGNITION_LOOP_V0.json",
        run_dir / "B9_LIVE_SCENE_RECOGNITION_RESULT_V0.json",
        run_dir / "B9_LIVE_SCENE_RECOGNITION_LOOP_MANIFEST.json",
    ]
    for candidate in result_candidates:
        if candidate.exists():
            try:
                result = read_json(candidate)
                checks.append(CheckRecord("t0135_result_loaded", "PASS", "P0", str(candidate)))
                return result, checks
            except Exception as exc:  # pragma: no cover
                checks.append(CheckRecord("t0135_result_loaded", "FAIL", "P0", f"{candidate}: {exc}"))
    checks.append(CheckRecord("t0135_result_loaded", "WARN", "P1", "T0135 CLI ran but no known result JSON was found."))
    return None, checks


def build_markdown(manifest: Dict[str, Any], input_rows: List[Dict[str, Any]], check_rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# T0136 — B9 Live Recognition Loop Runtime Validation V0")
    lines.append("")
    lines.append("## Résumé")
    lines.append("")
    lines.append(f"- État runtime : `{manifest['runtime_validation_state']}`")
    lines.append(f"- Mode : `{manifest['mode']}`")
    lines.append(f"- Entrées requises trouvées : `{manifest['required_inputs_found']}/{manifest['required_inputs_total']}`")
    lines.append(f"- T0135 exécuté : `{manifest['t0135_executed']}`")
    lines.append(f"- Matches : `{manifest.get('match_count', 0)}`")
    lines.append(f"- Film B6 le plus proche : `{manifest.get('top_match_film_id', '')}`")
    lines.append(f"- Langage interdit : `{manifest['forbidden_language_hit_count']}`")
    lines.append("")
    lines.append("## Phrase de cap")
    lines.append("")
    lines.append("B9 lit la scène. B6 compare les films. T0136 vérifie que la boucle T0135 fonctionne réellement dans le Core local.")
    lines.append("")
    lines.append("## Entrées runtime")
    lines.append("")
    lines.append("| Entrée | Trouvée | Chemin | Note |")
    lines.append("|---|---:|---|---|")
    for row in input_rows:
        lines.append(f"| {row.get('input_name','')} | {row.get('found','')} | `{row.get('path','')}` | {row.get('note','')} |")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | État | Sévérité | Détail |")
    lines.append("|---|---|---|---|")
    for row in check_rows:
        detail = str(row.get("detail", "")).replace("\n", " ")[:220]
        lines.append(f"| {row.get('check_name','')} | {row.get('state','')} | {row.get('severity','')} | {detail} |")
    lines.append("")
    lines.append("## Limites")
    lines.append("")
    lines.append("- Read-only.")
    lines.append("- Aucune écriture powerflow.db.")
    lines.append("- Aucune écriture tick_archive.db.")
    lines.append("- Aucun dashboard.")
    lines.append("- Aucun Telegram.")
    lines.append("- Aucun ordre d'exécution.")
    lines.append("- Aucun taux de réussite.")
    lines.append("- Une similarité B6 reste une proximité de lecture, pas une répétition certaine.")
    return "\n".join(lines) + "\n"


def zip_outputs(output_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file() and path != zip_path:
                zf.write(path, path.relative_to(output_dir))


def validate(mode: str, core_root: Path, sample_dir: Path, output_dir: Path, top_k: int, execute_t0135: bool) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if mode == "sample":
        paths, input_records = resolve_sample_inputs(sample_dir)
    else:
        paths, input_records = resolve_runtime_inputs(core_root)

    input_rows = [asdict(r) for r in input_records]
    required_inputs_total = sum(1 for r in input_records if r.required)
    required_inputs_found = sum(1 for r in input_records if r.required and r.found)
    missing_required = [r.input_name for r in input_records if r.required and not r.found]

    checks: List[CheckRecord] = []
    checks.append(CheckRecord("read_only_contract", "PASS", "P0", "T0136 reads JSON inputs and writes only output artifacts."))
    checks.append(CheckRecord("required_inputs", "PASS" if not missing_required else "BLOCKED", "P0", ", ".join(missing_required) if missing_required else "All required inputs found."))

    loaded: Dict[str, Any] = {}
    if not missing_required:
        try:
            loaded = load_inputs(paths)
            checks.append(CheckRecord("json_inputs_loadable", "PASS", "P0", "All JSON inputs loaded."))
        except Exception as exc:
            checks.append(CheckRecord("json_inputs_loadable", "FAIL", "P0", str(exc)))
            missing_required.append("json_load_error")

    t0135_result: Optional[Dict[str, Any]] = None
    t0135_executed = False
    if not missing_required and execute_t0135 and mode == "runtime":
        t0135_result, run_checks = run_t0135_cli(core_root, paths, output_dir, top_k)
        checks.extend(run_checks)
        t0135_executed = t0135_result is not None
    elif mode == "sample" and "precomputed_t0135_result_json" in paths:
        t0135_result = read_json(paths["precomputed_t0135_result_json"])
        checks.append(CheckRecord("precomputed_t0135_sample_result", "PASS", "P0", str(paths["precomputed_t0135_result_json"])))
    elif not execute_t0135:
        checks.append(CheckRecord("t0135_cli_execution", "SKIPPED", "INFO", "Execution disabled by flag."))

    forbidden = forbidden_hits(loaded, t0135_result or {})
    checks.append(CheckRecord("forbidden_language", "PASS" if not forbidden else "FAIL", "P0", f"{len(forbidden)} hits"))

    summary = summarize_t0135_result(t0135_result or {})
    hard_fail = any(c.state == "FAIL" for c in checks)
    blocked = bool(missing_required)
    if hard_fail:
        state = "FAIL"
    elif blocked:
        state = "BLOCKED_MISSING_RUNTIME_INPUTS"
    elif summary.get("low_trust_in_results") or summary.get("raw_unavailable_in_results") or summary.get("cross_family_match_count", 0):
        state = "FAIL_CONTRACT_VIOLATION"
    elif mode == "runtime" and execute_t0135 and t0135_executed:
        state = "PASS_RUNTIME_T0135_EXECUTED"
    elif mode == "sample":
        state = "PASS_SAMPLE_CONTRACT"
    else:
        state = "PASS_INPUT_CONTRACT_ONLY"

    manifest: Dict[str, Any] = {
        "version": VERSION,
        "runtime_validation_state": state,
        "mode": mode,
        "core_root": str(core_root),
        "output_dir": str(output_dir),
        "required_inputs_total": required_inputs_total,
        "required_inputs_found": required_inputs_found,
        "missing_required_inputs": missing_required,
        "t0135_executed": t0135_executed,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
        "forbidden_language_hit_count": len(forbidden),
        "forbidden_language_hits": forbidden,
        **summary,
    }

    check_rows = [asdict(c) for c in checks]
    write_json(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_V0.json", manifest)
    write_csv(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_INPUTS_V0.csv", input_rows)
    write_csv(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_CHECKS_V0.csv", check_rows)
    if t0135_result is not None:
        write_json(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_T0135_RESULT_SAMPLE_V0.json", t0135_result)
    md = build_markdown(manifest, input_rows, check_rows)
    (output_dir / "B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_V0.md").write_text(md, encoding="utf-8")
    write_json(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_MANIFEST.json", manifest)
    zip_path = output_dir / "B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_V0.zip"
    zip_outputs(output_dir, zip_path)
    manifest["zip"] = str(zip_path)
    write_json(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_MANIFEST.json", manifest)
    write_json(output_dir / "B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_V0.json", manifest)
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["sample", "runtime"], default="runtime")
    parser.add_argument("--core-root", default=".")
    parser.add_argument("--sample-dir", default="samples/b9_live_recognition_runtime_validation_v0")
    parser.add_argument("--output-dir", default="outputs/b9_live_recognition_runtime_validation_v0")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--execute-t0135", action="store_true", help="Execute T0135 CLI when mode=runtime and inputs are present.")
    parser.add_argument("--fail-on-blocked", action="store_true", help="Return non-zero if runtime inputs are missing.")
    args = parser.parse_args(argv)

    manifest = validate(
        mode=args.mode,
        core_root=Path(args.core_root).resolve(),
        sample_dir=Path(args.sample_dir).resolve(),
        output_dir=Path(args.output_dir),
        top_k=args.top_k,
        execute_t0135=args.execute_t0135,
    )
    print(json.dumps({
        "version": manifest["version"],
        "runtime_validation_state": manifest["runtime_validation_state"],
        "mode": manifest["mode"],
        "required_inputs_found": manifest["required_inputs_found"],
        "required_inputs_total": manifest["required_inputs_total"],
        "t0135_executed": manifest["t0135_executed"],
        "match_count": manifest.get("match_count", 0),
        "top_match_film_id": manifest.get("top_match_film_id", ""),
        "cross_family_match_count": manifest.get("cross_family_match_count", 0),
        "low_trust_in_results": manifest.get("low_trust_in_results", False),
        "raw_unavailable_in_results": manifest.get("raw_unavailable_in_results", False),
        "forbidden_language_hit_count": manifest["forbidden_language_hit_count"],
        "zip": manifest.get("zip", ""),
    }, ensure_ascii=False, indent=2))

    if manifest["runtime_validation_state"].startswith("FAIL"):
        return 1
    if args.fail_on_blocked and manifest["runtime_validation_state"].startswith("BLOCKED"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
