#!/usr/bin/env python3
"""T0126 - B9 V4 Runtime Replay Pack Collector V0.

Read-only collector that scans a PowerFlow Core tree for real B9/T009 replay
summary JSON files and builds a clean batch candidate pack for T0125.

Doctrine:
- no DB write
- no dashboard
- no telegram
- no BUY/SELL
- no probability of success
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

VERSION = "T0126_B9_RUNTIME_REPLAY_PACK_COLLECTOR_V0"

DEFAULT_NAME_PATTERNS = [
    "t009_sequence_summary*.json",
    "*t009*summary*.json",
    "*sequence_summary*.json",
    "*B9*summary*.json",
    "*b9*summary*.json",
]

EXCLUDED_DIR_TOKENS = {
    "samples",
    "_extract",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "node_modules",
}

EXCLUDED_PATH_TOKENS = [
    "_validation",
    "_install_validation",
    "_git_validation",
    "_regenerated",
    "golden_replay_batch_runner_v0",
    "regression_guard_golden_replay_cases_v0",
    "native_runtime_validation_v0",
    "replay_runtime_comparison_v0",
    "native_summarizer_v4_contract_patch_v0",
    "native_summarizer_v4_integration_patch_v0",
]

FORBIDDEN_RE = re.compile(r"\b(BUY|SELL|ACHETER|VENDRE|probabilit[eé] de succ[eè]s|success probability)\b", re.I)


@dataclass
class Candidate:
    path: str
    file_name: str
    size_bytes: int
    sha256_12: str
    reason: str
    replay_candidate_state: str
    source_family_guess: str
    moment_count: int
    has_moments: bool
    has_v4_fields: bool
    has_source_quality: bool
    has_timestamp_policy: bool
    has_forbidden_language: bool
    date_guess: str
    session_guess: str
    summary_recovery_type_guess: str
    technical_limits: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_hash(text: str, n: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:n].upper()


def file_sha256_12(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12].upper()


def is_excluded(path: Path, scan_root: Path) -> tuple[bool, str]:
    try:
        rel_parts = path.relative_to(scan_root).parts
    except ValueError:
        rel_parts = path.parts
    lowered_parts = [p.lower() for p in rel_parts]
    for part in lowered_parts:
        if part in EXCLUDED_DIR_TOKENS:
            return True, f"excluded_dir:{part}"
    lowered_str = str(path).replace("\\", "/").lower()
    for token in EXCLUDED_PATH_TOKENS:
        if token.lower() in lowered_str:
            return True, f"excluded_path_token:{token}"
    return False, ""


def load_json_safe(path: Path) -> tuple[dict[str, Any] | list[Any] | None, str]:
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f), ""
    except Exception as exc:  # noqa: BLE001 - collector must not crash on one bad file
        return None, f"json_error:{type(exc).__name__}:{exc}"


def find_moments(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, dict):
        for key in ("moments", "sequence_moments", "b9_moments", "scenes"):
            value = obj.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        # Some summaries store result under summary.moments or output.moments.
        for key in ("summary", "output", "result", "data"):
            value = obj.get(key)
            nested = find_moments(value)
            if nested:
                return nested
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    return []


def get_any(obj: dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def guess_date(path: Path, obj: Any, moments: list[dict[str, Any]]) -> str:
    if isinstance(obj, dict):
        for key in ("date", "trading_date", "session_date"):
            val = obj.get(key)
            if val:
                m = re.search(r"20\d{2}[-_]?\d{2}[-_]?\d{2}", str(val))
                if m:
                    raw = m.group(0).replace("_", "-")
                    if "-" not in raw and len(raw) == 8:
                        raw = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                    return raw
    for moment in moments[:5]:
        val = get_any(moment, ("date", "time_start", "orig_start", "start", "timestamp"))
        m = re.search(r"20\d{2}[-_]?\d{2}[-_]?\d{2}", val)
        if m:
            raw = m.group(0).replace("_", "-")
            if "-" not in raw and len(raw) == 8:
                raw = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
            return raw
    m = re.search(r"20\d{6}", path.name)
    if m:
        raw = m.group(0)
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return "UNKNOWN_DATE"


def guess_session(path: Path, obj: Any, moments: list[dict[str, Any]]) -> str:
    text = f"{path.name} {json.dumps(obj, ensure_ascii=False)[:4000] if obj is not None else ''}".lower()
    if "london" in text:
        return "LONDON"
    if "asian" in text or "asia" in text:
        return "ASIAN"
    if "ny" in text or "new_york" in text or "us" in text:
        return "NY_US"
    # Infer from first hour if available.
    for moment in moments[:3]:
        val = get_any(moment, ("time_start", "orig_start", "start"))
        hm = re.search(r"\b(\d{2}):(\d{2})\b", val)
        if hm:
            hour = int(hm.group(1))
            if 7 <= hour < 12:
                return "LONDON"
            if 12 <= hour < 16:
                return "OVERLAP_OR_US_OPEN"
            if 22 <= hour or hour < 7:
                return "ASIAN"
    return "UNKNOWN_SESSION"


def detect_v4_fields(moment: dict[str, Any]) -> bool:
    required_any = [
        "what_happens_fr",
        "why_it_matters_fr",
        "how_it_happened_fr",
        "b9_effort_result_progress_state",
        "b9_center_path_state",
        "b9_native_retest_judgment",
        "b9_v4_timestamp_policy",
    ]
    return any(k in moment and moment.get(k) not in (None, "") for k in required_any)


def build_candidate(path: Path, scan_root: Path) -> Candidate:
    obj, err = load_json_safe(path)
    moments = find_moments(obj)
    sample_text = ""
    if obj is not None:
        try:
            sample_text = json.dumps(obj, ensure_ascii=False)[:30000]
        except Exception:
            sample_text = str(obj)[:30000]

    has_forbidden = bool(FORBIDDEN_RE.search(sample_text))
    has_moments = bool(moments)
    has_v4 = any(detect_v4_fields(m) for m in moments)
    has_source_quality = any(
        any(k in m for k in ("source_quality_state", "source_quality_score", "source_mode", "data_visibility", "confidence_cap"))
        for m in moments
    )
    has_timestamp_policy = any(
        any(k in m for k in ("b9_v4_timestamp_policy", "timestamp_policy", "time_start_real", "orig_start"))
        for m in moments
    )

    if err:
        state = "REJECT_JSON_UNREADABLE"
        reason = err
    elif not has_moments:
        state = "REVIEW_NO_MOMENTS_DETECTED"
        reason = "json_readable_but_no_moments_key_detected"
    elif has_forbidden:
        state = "REVIEW_FORBIDDEN_LANGUAGE_DETECTED"
        reason = "forbidden_language_detected"
    elif has_v4 and has_source_quality:
        state = "B9_REPLAY_PACK_KEEP_V4_READY"
        reason = "moments_detected_with_v4_and_source_quality"
    elif has_source_quality:
        state = "B9_REPLAY_PACK_KEEP_PRE_V4"
        reason = "moments_detected_with_source_quality_pre_v4_candidate"
    else:
        state = "B9_REPLAY_PACK_REVIEW_SOURCE_QUALITY_WEAK"
        reason = "moments_detected_but_source_quality_not_visible"

    summary_recovery = "UNKNOWN_SUMMARY_FAMILY"
    if isinstance(obj, dict):
        summary_recovery = get_any(obj, ("summary_recovery_type", "source_family", "recovery_type"), "UNKNOWN_SUMMARY_FAMILY")
    if summary_recovery == "UNKNOWN_SUMMARY_FAMILY":
        lowered = path.name.lower()
        if "force_snapshot" in lowered:
            summary_recovery = "FORCE_SNAPSHOT_DERIVED"
        elif "recovered" in lowered:
            summary_recovery = "RECOVERED_EXISTING_B9_SUMMARY"
        elif has_moments:
            summary_recovery = "ORIGINAL_OR_RUNTIME_SUMMARY_CANDIDATE"

    tech_limits = []
    if not has_v4:
        tech_limits.append("V4_FIELDS_NOT_NATIVE_OR_NOT_VISIBLE")
    if not has_timestamp_policy:
        tech_limits.append("TIMESTAMP_POLICY_NOT_VISIBLE")
    if not has_source_quality:
        tech_limits.append("SOURCE_QUALITY_NOT_VISIBLE")
    if has_forbidden:
        tech_limits.append("FORBIDDEN_LANGUAGE_REVIEW_REQUIRED")
    if err:
        tech_limits.append("JSON_READ_ERROR")

    try:
        rel_path = str(path.relative_to(scan_root))
    except ValueError:
        rel_path = str(path)

    return Candidate(
        path=rel_path.replace("\\", "/"),
        file_name=path.name,
        size_bytes=path.stat().st_size,
        sha256_12=file_sha256_12(path),
        reason=reason,
        replay_candidate_state=state,
        source_family_guess=summary_recovery,
        moment_count=len(moments),
        has_moments=has_moments,
        has_v4_fields=has_v4,
        has_source_quality=has_source_quality,
        has_timestamp_policy=has_timestamp_policy,
        has_forbidden_language=has_forbidden,
        date_guess=guess_date(path, obj, moments),
        session_guess=guess_session(path, obj, moments),
        summary_recovery_type_guess=summary_recovery,
        technical_limits=";".join(tech_limits) if tech_limits else "NONE",
    )


def discover_files(scan_root: Path) -> list[Path]:
    candidates: dict[Path, None] = {}
    for pattern in DEFAULT_NAME_PATTERNS:
        for path in scan_root.rglob(pattern):
            if not path.is_file():
                continue
            excluded, _ = is_excluded(path, scan_root)
            if excluded:
                continue
            candidates[path.resolve()] = None
    return sorted(candidates.keys(), key=lambda p: str(p).lower())


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_md(path: Path, manifest: dict[str, Any], candidates: list[Candidate]) -> None:
    keep = [c for c in candidates if c.replay_candidate_state.startswith("B9_REPLAY_PACK_KEEP")]
    review = [c for c in candidates if "REVIEW" in c.replay_candidate_state]
    rejected = [c for c in candidates if c.replay_candidate_state.startswith("REJECT")]
    lines = [
        "# T0126 — B9 Runtime Replay Pack Collector V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "Le collector ne prédit rien : il prépare un lot replay propre pour les guards T0124/T0125.",
        "",
        "## Counts",
        "",
        f"- scanned_root: `{manifest['scan_root']}`",
        f"- files_discovered: {manifest['files_discovered']}",
        f"- candidates_keep: {manifest['candidates_keep']}",
        f"- candidates_review: {manifest['candidates_review']}",
        f"- candidates_rejected: {manifest['candidates_rejected']}",
        "",
        "## KEEP candidates",
        "",
    ]
    if keep:
        for c in keep[:50]:
            lines.append(f"- `{c.path}` — {c.replay_candidate_state} — moments={c.moment_count} — date={c.date_guess} — session={c.session_guess}")
    else:
        lines.append("Aucun candidat KEEP détecté dans ce scan.")
    lines += ["", "## REVIEW candidates", ""]
    if review:
        for c in review[:50]:
            lines.append(f"- `{c.path}` — {c.replay_candidate_state} — limits={c.technical_limits}")
    else:
        lines.append("Aucun candidat REVIEW détecté.")
    lines += ["", "## Rejected", ""]
    if rejected:
        for c in rejected[:50]:
            lines.append(f"- `{c.path}` — {c.replay_candidate_state} — {c.reason}")
    else:
        lines.append("Aucun fichier rejeté.")
    lines += [
        "",
        "## Usage T0125",
        "",
        "Copier ou pointer les fichiers KEEP vers un batch réel, puis lancer T0125 sur ce lot.",
        "",
        "## Limites techniques",
        "",
        "- Read-only : aucune DB touchée.",
        "- Le collector classe les fichiers par structure JSON et metadata visible.",
        "- Un fichier REVIEW peut devenir exploitable après inspection humaine.",
        "- Les samples, validations, regenerated et _extract sont exclus pour éviter les faux lots.",
        "- La présence V4 est détectée, mais la vérité runtime reste validée par T0122/T0123/T0125.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(scan_root: Path, output_dir: Path, max_files: int | None = None) -> dict[str, Any]:
    scan_root = scan_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    files = discover_files(scan_root)
    if max_files is not None:
        files = files[:max_files]
    candidates = [build_candidate(p, scan_root) for p in files]

    rows = [asdict(c) for c in candidates]
    fieldnames = list(asdict(candidates[0]).keys()) if candidates else list(Candidate.__annotations__.keys())

    keep = [c for c in candidates if c.replay_candidate_state.startswith("B9_REPLAY_PACK_KEEP")]
    review = [c for c in candidates if "REVIEW" in c.replay_candidate_state]
    rejected = [c for c in candidates if c.replay_candidate_state.startswith("REJECT")]

    index_csv = output_dir / "B9_RUNTIME_REPLAY_PACK_INDEX_V0.csv"
    index_json = output_dir / "B9_RUNTIME_REPLAY_PACK_INDEX_V0.json"
    candidates_md = output_dir / "B9_RUNTIME_REPLAY_PACK_CANDIDATES_V0.md"
    keep_csv = output_dir / "B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv"
    review_csv = output_dir / "B9_RUNTIME_REPLAY_PACK_REVIEW_V0.csv"
    rejected_csv = output_dir / "B9_RUNTIME_REPLAY_PACK_REJECTED_V0.csv"

    write_csv(index_csv, rows, fieldnames)
    write_csv(keep_csv, [asdict(c) for c in keep], fieldnames)
    write_csv(review_csv, [asdict(c) for c in review], fieldnames)
    write_csv(rejected_csv, [asdict(c) for c in rejected], fieldnames)

    index_payload = {
        "version": VERSION,
        "generated_at": now_iso(),
        "scan_root": str(scan_root),
        "files": rows,
    }
    index_json.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "version": VERSION,
        "generated_at": now_iso(),
        "scan_root": str(scan_root),
        "output_dir": str(output_dir),
        "files_discovered": len(candidates),
        "candidates_keep": len(keep),
        "candidates_review": len(review),
        "candidates_rejected": len(rejected),
        "files_with_v4_fields": sum(1 for c in candidates if c.has_v4_fields),
        "files_with_source_quality": sum(1 for c in candidates if c.has_source_quality),
        "files_with_timestamp_policy": sum(1 for c in candidates if c.has_timestamp_policy),
        "forbidden_language_files": sum(1 for c in candidates if c.has_forbidden_language),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }

    write_md(candidates_md, manifest, candidates)

    manifest_path = output_dir / "B9_RUNTIME_REPLAY_PACK_COLLECTOR_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = output_dir / "B9_RUNTIME_REPLAY_PACK_COLLECTOR_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in [index_csv, index_json, candidates_md, keep_csv, review_csv, rejected_csv, manifest_path]:
            zf.write(p, p.name)

    manifest["zip"] = str(zip_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0126 B9 runtime replay pack collector outputs.")
    parser.add_argument("--scan-root", required=True, help="PowerFlow Core root to scan.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--max-files", type=int, default=None, help="Optional max files for very large trees.")
    args = parser.parse_args()
    manifest = run(Path(args.scan_root), Path(args.output_dir), args.max_files)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
