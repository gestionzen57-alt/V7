#!/usr/bin/env python3
"""
T0138 - B9 Real Replay Day Pack Runner V0

Read-only runner that applies B9 V4 replay/runtime checks over real replay summaries
collected by T0126 (or directly from a scan directory), while excluding samples,
validation outputs, regenerated outputs and extraction artifacts.

PowerFlow doctrine:
- B9 does not seek a signal; B9 reads the trace left by effort.
- A similarity or replay pass is not a prediction.
- No DB write, no dashboard, no Telegram, no BUY/SELL, no probability of success.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0138_B9_REAL_REPLAY_DAY_PACK_RUNNER_V0"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bACHETER\b", re.IGNORECASE),
    re.compile(r"\bVENDRE\b", re.IGNORECASE),
    re.compile(r"probabilit[eé]\s+de\s+succ[eè]s", re.IGNORECASE),
    re.compile(r"success\s+probability", re.IGNORECASE),
]

EXCLUDE_PARTS = {
    ".git",
    "_extract",
    "samples",
}
EXCLUDE_SUBSTRINGS = [
    "_validation",
    "_install_validation",
    "_git_validation",
    "_regenerated",
]

REQUIRED_OR_USEFUL_FIELDS = [
    "label_fr",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "b9_source_quality_gate_state",
    "b9_effort_result_progress_state",
    "b9_center_path_visibility",
    "b9_session",
    "retest_visible",
    "retest_result",
    "b9_v4_timestamp_policy",
]

PRESERVED_FIELDS = [
    "time_start",
    "time_end",
    "label_fr",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "summary_recovery_type",
    "proxy_vs_raw_verdict",
]

@dataclass
class ReplayFileResult:
    replay_id: str
    path: str
    status: str
    reason: str
    moment_count: int
    source_family: str
    summary_recovery_type: str
    source_mode: str
    data_visibility: str
    confidence_cap: str
    proxy_vs_raw_verdict: str
    fields_present_count: int
    fields_missing_count: int
    missing_fields: str
    v4_field_ratio: float
    has_timestamp_policy: bool
    has_retest_fields: bool
    has_source_quality_gate: bool
    has_effort_result_progress: bool
    has_center_path: bool
    has_session_overlay: bool
    forbidden_language_hits: int
    raw_unavailable_count: int
    nuanced_by_raw_count: int
    confirmed_by_raw_count: int
    first_time: str
    last_time: str


def is_excluded_path(path: Path, allow_samples: bool = False) -> bool:
    parts = {p.lower() for p in path.parts}
    excluded_parts = set(EXCLUDE_PARTS)
    if allow_samples:
        excluded_parts.discard("samples")
    if any(part.lower() in parts for part in excluded_parts):
        return True
    pstr = str(path).lower()
    return any(s.lower() in pstr for s in EXCLUDE_SUBSTRINGS)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_moments(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [m for m in payload if isinstance(m, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("moments", "sequence_moments", "b9_moments", "items", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return [m for m in value if isinstance(m, dict)]
    # Some T009 outputs wrap under summary / result
    for key in ("summary", "result", "data"):
        value = payload.get(key)
        if isinstance(value, dict):
            found = find_moments(value)
            if found:
                return found
    return []


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def first_non_empty(moments: List[Dict[str, Any]], keys: Iterable[str]) -> str:
    for m in moments:
        for k in keys:
            v = m.get(k)
            if v not in (None, "", []):
                return safe_str(v)
    return ""


def count_verdict(moments: List[Dict[str, Any]], needle: str) -> int:
    n = needle.upper()
    count = 0
    for m in moments:
        joined = " ".join(safe_str(m.get(k, "")) for k in ("proxy_vs_raw_verdict", "b9_source_quality_gate_state", "source_quality_state"))
        if n in joined.upper():
            count += 1
    return count


def forbidden_hits(payload: Any) -> int:
    text = json.dumps(payload, ensure_ascii=False)
    total = 0
    for pattern in FORBIDDEN_PATTERNS:
        total += len(pattern.findall(text))
    return total


def infer_status(moment_count: int, missing_count: int, forbidden_count: int, raw_unavailable: int, has_timestamp: bool) -> Tuple[str, str]:
    if moment_count <= 0:
        return "REJECT", "NO_MOMENTS_FOUND"
    if forbidden_count > 0:
        return "REJECT", "FORBIDDEN_LANGUAGE_FOUND"
    if raw_unavailable and raw_unavailable == moment_count:
        return "REJECT", "ALL_RAW_UNAVAILABLE"
    if missing_count <= 3 and has_timestamp:
        return "KEEP", "REAL_REPLAY_READY"
    return "REVIEW", "PARTIAL_FIELD_COVERAGE"


def result_for_file(path: Path, scan_root: Path) -> ReplayFileResult:
    payload = load_json(path)
    moments = find_moments(payload)
    moment_count = len(moments)
    field_present = 0
    missing = []
    for field in REQUIRED_OR_USEFUL_FIELDS:
        present = any(m.get(field) not in (None, "", []) for m in moments)
        if present:
            field_present += 1
        else:
            missing.append(field)
    missing_count = len(missing)
    forbidden = forbidden_hits(payload)
    raw_unavailable = count_verdict(moments, "RAW_UNAVAILABLE")
    nuanced = count_verdict(moments, "NUANCED_BY_RAW")
    confirmed = count_verdict(moments, "CONFIRMED_BY_RAW")
    has_timestamp = any(m.get("b9_v4_timestamp_policy") or m.get("timestamp_policy") for m in moments)
    has_retest = any("retest_visible" in m or "retest_result" in m or "retest_judgment_fr" in m for m in moments)
    has_source_gate = any("b9_source_quality_gate_state" in m for m in moments)
    has_erp = any("b9_effort_result_progress_state" in m for m in moments)
    has_center = any("b9_center_path_visibility" in m or "b9_center_path_shape" in m for m in moments)
    has_session = any("b9_session" in m or "b9_session_phase" in m for m in moments)
    status, reason = infer_status(moment_count, missing_count, forbidden, raw_unavailable, has_timestamp)
    rel = path.relative_to(scan_root) if path.is_relative_to(scan_root) else path
    source_family = first_non_empty(moments, ["source_family", "b9_source_truth_family"])
    summary_recovery_type = first_non_empty(moments, ["summary_recovery_type"])
    source_mode = first_non_empty(moments, ["source_mode"])
    data_visibility = first_non_empty(moments, ["data_visibility"])
    confidence_cap = first_non_empty(moments, ["confidence_cap", "b9_source_confidence_cap_effective"])
    proxy_vs_raw = first_non_empty(moments, ["proxy_vs_raw_verdict"])
    first_time = first_non_empty(moments[:1], ["time_start_real", "time_start", "start", "timestamp"])
    last_time = first_non_empty(moments[-1:] if moments else [], ["time_end_real", "time_end", "end", "timestamp"])
    return ReplayFileResult(
        replay_id=path.stem,
        path=str(rel).replace("\\", "/"),
        status=status,
        reason=reason,
        moment_count=moment_count,
        source_family=source_family,
        summary_recovery_type=summary_recovery_type,
        source_mode=source_mode,
        data_visibility=data_visibility,
        confidence_cap=confidence_cap,
        proxy_vs_raw_verdict=proxy_vs_raw,
        fields_present_count=field_present,
        fields_missing_count=missing_count,
        missing_fields="|".join(missing),
        v4_field_ratio=round(field_present / max(1, len(REQUIRED_OR_USEFUL_FIELDS)), 4),
        has_timestamp_policy=has_timestamp,
        has_retest_fields=has_retest,
        has_source_quality_gate=has_source_gate,
        has_effort_result_progress=has_erp,
        has_center_path=has_center,
        has_session_overlay=has_session,
        forbidden_language_hits=forbidden,
        raw_unavailable_count=raw_unavailable,
        nuanced_by_raw_count=nuanced,
        confirmed_by_raw_count=confirmed,
        first_time=first_time,
        last_time=last_time,
    )


def read_index_csv(path: Path, scan_root: Path) -> List[Path]:
    files: List[Path] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("status") or row.get("candidate_state") or row.get("decision") or "").upper()
            if status and status not in {"KEEP", "B9_KEEP_CANDIDATE", "REVIEW", "B9_REVIEW_CANDIDATE"}:
                continue
            raw_path = row.get("path") or row.get("file_path") or row.get("source_path") or row.get("json_path")
            if raw_path:
                p = Path(raw_path)
                if not p.is_absolute():
                    p = scan_root / p
                if p.exists() and p.suffix.lower() == ".json" and not is_excluded_path(p):
                    files.append(p)
    return files


def discover_json_files(scan_root: Path, allow_samples: bool = False) -> List[Path]:
    patterns = [
        "**/t009_sequence_summary*.json",
        "**/*sequence_summary*.json",
        "**/*B9*summary*.json",
        "**/*b9*summary*.json",
    ]
    seen = set()
    files: List[Path] = []
    for pattern in patterns:
        for p in scan_root.glob(pattern):
            if not p.is_file():
                continue
            if p in seen or is_excluded_path(p, allow_samples=allow_samples):
                continue
            seen.add(p)
            files.append(p)
    return sorted(files)


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_markdown(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    keep = [r for r in rows if r["status"] == "KEEP"]
    review = [r for r in rows if r["status"] == "REVIEW"]
    reject = [r for r in rows if r["status"] == "REJECT"]
    lines = [
        "# T0138 — B9 Real Replay Day Pack Runner V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal. B9 cherche la trace laissée par l'effort.",
        "T0138 applique les guards B9 V4 sur un lot de summaries replay réels ou collectés par T0126.",
        "",
        "## Counts",
        "",
        f"- batch_state : `{summary['batch_state']}`",
        f"- files_processed : `{summary['files_processed']}`",
        f"- files_keep : `{summary['files_keep']}`",
        f"- files_review : `{summary['files_review']}`",
        f"- files_rejected : `{summary['files_rejected']}`",
        f"- total_moments : `{summary['total_moments']}`",
        f"- forbidden_language_files : `{summary['forbidden_language_files']}`",
        "",
        "## KEEP",
        "",
    ]
    if keep:
        for r in keep[:25]:
            lines.append(f"- `{r['path']}` — {r['moment_count']} moments — {r['reason']}")
    else:
        lines.append("Aucun fichier KEEP.")
    lines += ["", "## REVIEW", ""]
    if review:
        for r in review[:25]:
            lines.append(f"- `{r['path']}` — {r['reason']} — missing: {r['missing_fields']}")
    else:
        lines.append("Aucun fichier REVIEW.")
    lines += ["", "## REJECT", ""]
    if reject:
        for r in reject[:25]:
            lines.append(f"- `{r['path']}` — {r['reason']}")
    else:
        lines.append("Aucun fichier REJECT.")
    lines += [
        "",
        "## Limites techniques",
        "",
        "- Read-only : aucune écriture `powerflow.db` ou `tick_archive.db`.",
        "- Les fichiers `samples/`, `_validation`, `_install_validation`, `_git_validation`, `_regenerated` et `_extract` sont exclus.",
        "- Un replay partiel reste REVIEW tant que timestamp/retest/source quality ne sont pas suffisamment visibles.",
        "- RAW_UNAVAILABLE complet est rejeté de la mémoire active.",
        "",
        "## Ce que B9 peut conclure",
        "",
        "B9 peut dire qu'un replay est exploitable, partiel ou rejeté pour validation terrain.",
        "",
        "## Ce que B9 ne doit pas conclure",
        "",
        "Aucun ordre d'exécution, aucun BUY/SELL, aucune probabilité de succès.",
    ]
    return "\n".join(lines) + "\n"


def zip_dir(output_zip: Path, files: Iterable[Path], base: Path) -> None:
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.is_file():
                zf.write(f, f.relative_to(base).as_posix())


def run(args: argparse.Namespace) -> Dict[str, Any]:
    scan_root = Path(args.scan_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates: List[Path] = []
    if args.input_index_csv:
        index_path = Path(args.input_index_csv).resolve()
        if not index_path.exists():
            raise FileNotFoundError(f"input index csv not found: {index_path}")
        candidates.extend(read_index_csv(index_path, scan_root))
    if args.input_dir:
        input_dir = Path(args.input_dir).resolve()
        candidates.extend(discover_json_files(input_dir, allow_samples=True))
    if not candidates:
        candidates.extend(discover_json_files(scan_root, allow_samples=False))

    # dedupe
    unique = []
    seen = set()
    for p in candidates:
        rp = p.resolve()
        if rp not in seen and rp.exists() and not is_excluded_path(rp, allow_samples=bool(args.input_dir)):
            seen.add(rp)
            unique.append(rp)

    results: List[ReplayFileResult] = []
    failures: List[Dict[str, Any]] = []
    for p in unique:
        try:
            results.append(result_for_file(p, scan_root))
        except Exception as exc:
            failures.append({"path": str(p), "status": "REJECT", "reason": f"READ_ERROR:{type(exc).__name__}:{exc}"})

    rows = [asdict(r) for r in results]
    rows.extend(failures)
    fieldnames = list(asdict(results[0]).keys()) if results else list(ReplayFileResult.__annotations__.keys())
    # failure rows may be sparse; normalize
    norm_rows = []
    for r in rows:
        norm = {k: r.get(k, "") for k in fieldnames}
        norm_rows.append(norm)

    keep = [r for r in norm_rows if r.get("status") == "KEEP"]
    review = [r for r in norm_rows if r.get("status") == "REVIEW"]
    reject = [r for r in norm_rows if r.get("status") == "REJECT"]

    batch_state = "PASS" if norm_rows and not reject else ("PARTIAL" if norm_rows else "BLOCKED_NO_REPLAY_FILES")
    summary = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "batch_state": batch_state,
        "scan_root": str(scan_root),
        "files_discovered": len(unique),
        "files_processed": len(norm_rows),
        "files_keep": len(keep),
        "files_review": len(review),
        "files_rejected": len(reject),
        "total_moments": sum(int(r.get("moment_count") or 0) for r in norm_rows),
        "forbidden_language_files": sum(1 for r in norm_rows if int(r.get("forbidden_language_hits") or 0) > 0),
        "raw_unavailable_files": sum(1 for r in norm_rows if int(r.get("raw_unavailable_count") or 0) > 0),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }

    write_json(output_dir / "B9_REAL_REPLAY_DAY_RUNNER_V0.json", {"summary": summary, "files": norm_rows})
    write_csv(output_dir / "B9_REAL_REPLAY_DAY_RESULTS_V0.csv", norm_rows, fieldnames)
    write_csv(output_dir / "B9_REAL_REPLAY_DAY_KEEP_V0.csv", keep, fieldnames)
    write_csv(output_dir / "B9_REAL_REPLAY_DAY_REVIEW_V0.csv", review, fieldnames)
    write_csv(output_dir / "B9_REAL_REPLAY_DAY_FAILURES_V0.csv", reject, fieldnames)

    coverage_rows = []
    for field in REQUIRED_OR_USEFUL_FIELDS:
        coverage_rows.append({
            "field": field,
            "files_with_field": sum(1 for r in norm_rows if field not in str(r.get("missing_fields", "")).split("|")),
            "files_total": len(norm_rows),
            "coverage_ratio": round(sum(1 for r in norm_rows if field not in str(r.get("missing_fields", "")).split("|")) / max(1, len(norm_rows)), 4),
        })
    write_csv(output_dir / "B9_REAL_REPLAY_DAY_COVERAGE_V0.csv", coverage_rows, ["field", "files_with_field", "files_total", "coverage_ratio"])

    md = build_markdown(summary, norm_rows)
    (output_dir / "B9_REAL_REPLAY_DAY_RUNNER_V0.md").write_text(md, encoding="utf-8")

    manifest = {
        "version": VERSION,
        "outputs": [p.name for p in output_dir.iterdir() if p.is_file()],
        "summary": summary,
    }
    write_json(output_dir / "B9_REAL_REPLAY_DAY_RUNNER_MANIFEST.json", manifest)

    zip_path = output_dir / "B9_REAL_REPLAY_DAY_RUNNER_V0.zip"
    zip_dir(zip_path, [p for p in output_dir.iterdir() if p.is_file() and p.name != zip_path.name], output_dir)
    summary["zip"] = str(zip_path)
    write_json(output_dir / "B9_REAL_REPLAY_DAY_RUNNER_V0.json", {"summary": summary, "files": norm_rows})
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T0138 B9 real replay day pack runner")
    parser.add_argument("--scan-root", default=".")
    parser.add_argument("--input-index-csv", default="")
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
