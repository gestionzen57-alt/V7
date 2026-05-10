#!/usr/bin/env python3
r"""
PowerFlow V7.2 — Batch test robuste toutes briques V4

Objectif:
- Exécuter les runners PowerFlow sans modifier le Core.
- Essayer automatiquement deux contextes:
  1) depuis la racine repo: python Core\runner.py --db Core\powerflow.db
  2) depuis Core: python runner.py --db powerflow.db
- Capturer les JSON de manière robuste.
- Qualifier chaque brique: PASS / PARTIAL / FAIL / MISSING / TIMEOUT / ERROR.
- Générer 4 rapports lisibles: JSON, CSV, HTML, Markdown.

Usage:
    python test_batch_all_bricks.py
    python test_batch_all_bricks.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_ORDER = {
    "PASS": 0,
    "PARTIAL": 1,
    "MISSING": 2,
    "TIMEOUT": 3,
    "FAIL": 4,
    "ERROR": 5,
}


@dataclass(frozen=True)
class BrickSpec:
    name: str
    runner: str
    arg_sets_root: Tuple[Tuple[str, ...], ...]
    arg_sets_core: Tuple[Tuple[str, ...], ...]
    category: str
    critical_group: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent


def display_path(path: Path) -> str:
    return str(path).replace("/", "\\")


def extract_first_json(text: str) -> Optional[Any]:
    """Extract first valid JSON object or array from mixed stdout."""
    if not text:
        return None

    starts = [idx for idx, ch in enumerate(text) if ch in "{["]
    for start in starts:
        stack: List[str] = []
        in_string = False
        escaped = False

        for idx in range(start, len(text)):
            ch = text[idx]

            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch in "{[":
                stack.append(ch)
                continue

            if ch in "}]":
                if not stack:
                    break
                top = stack[-1]
                if (top == "{" and ch != "}") or (top == "[" and ch != "]"):
                    break
                stack.pop()
                if not stack:
                    candidate = text[start : idx + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    return None


def deep_find(data: Any, keys: Iterable[str]) -> Optional[Tuple[str, Any]]:
    ordered_keys = list(keys)

    if isinstance(data, dict):
        for key in ordered_keys:
            if key in data:
                return key, data[key]
        for value in data.values():
            found = deep_find(value, ordered_keys)
            if found is not None:
                return found

    if isinstance(data, list):
        for item in data:
            found = deep_find(item, ordered_keys)
            if found is not None:
                return found

    return None


def collect_risks(data: Any) -> List[str]:
    risks: List[str] = []

    if isinstance(data, dict):
        value = data.get("technical_risks")
        if isinstance(value, list):
            risks.extend(str(x) for x in value)
        for child in data.values():
            risks.extend(collect_risks(child))
    elif isinstance(data, list):
        for item in data:
            risks.extend(collect_risks(item))

    seen = set()
    unique = []
    for risk in risks:
        if risk not in seen:
            unique.append(risk)
            seen.add(risk)
    return unique


def key_info_from_data(data: Any) -> str:
    if data is None:
        return ""

    preferred_keys = [
        "regime",
        "confidence",
        "cycle_state",
        "compression_ratio",
        "cascade_state",
        "events_count",
        "resonance_state",
        "state",
        "resonance_score",
        "energy_state",
        "elastic_tension_score",
        "alert_entropy_state",
        "valid",
        "status",
        "session",
        "session_phase",
    ]

    parts: List[str] = []
    used = set()
    for key in preferred_keys:
        found = deep_find(data, [key])
        if found is not None:
            k, v = found
            if k in used:
                continue
            used.add(k)
            if isinstance(v, float):
                parts.append(f"{k}={v:.4f}")
            else:
                parts.append(f"{k}={v}")
        if len(parts) >= 4:
            break

    if parts:
        return " | ".join(parts)

    if isinstance(data, dict):
        keys = list(data.keys())[:6]
        return "keys=" + ",".join(keys)
    if isinstance(data, list):
        return f"list_len={len(data)}"

    return str(data)[:120]


class BrickTester:
    def __init__(
        self,
        root: Path,
        db_root: str,
        symbol: str,
        tfs: str,
        timeout: int,
        output_dir: str,
    ) -> None:
        self.root = root
        self.core = root / "Core"
        self.db_root = db_root
        self.db_core = "powerflow.db" if db_root.replace("/", "\\").lower().startswith("core\\") else db_root
        self.symbol = symbol
        self.tfs = tfs
        self.timeout = timeout
        self.output_dir = root / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []

        self.latest_db_timestamp = self._latest_db_timestamp()
        self.window_start, self.window_end, self.since_date = self._derive_time_window()

    def _latest_db_timestamp(self) -> Optional[datetime]:
        db_file = self.root / self.db_root
        if not db_file.exists():
            return None
        try:
            conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
            try:
                row = conn.execute("SELECT MAX(timestamp) FROM force_snapshots").fetchone()
            finally:
                conn.close()
            if not row or not row[0]:
                return None
            raw = str(row[0]).replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(raw)
            except ValueError:
                # Common fallback when timestamp has no timezone.
                dt = datetime.fromisoformat(raw.split("+")[0])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def _derive_time_window(self) -> Tuple[str, str, str]:
        latest = self.latest_db_timestamp or datetime.now(timezone.utc)
        start = latest - timedelta(hours=3)
        # Keep ISO format acceptable for most argparse/date parsers.
        start_s = start.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        end_s = latest.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        since_s = latest.date().isoformat()
        return start_s, end_s, since_s

    def specs(self) -> List[BrickSpec]:
        db_r = self.db_root
        db_c = self.db_core
        symbol = self.symbol
        tfs = self.tfs
        start = self.window_start
        end = self.window_end
        since = self.since_date
        hmm_root = str(Path("output") / "hmm.pkl")
        hmm_core = str(Path("..") / "output" / "hmm.pkl")

        return [
            BrickSpec(
                "B1 Legacy Regime",
                "run_regime_engine_once.py",
                (("--db", db_r, "--pretty"), ("--pretty",), tuple()),
                (("--db", db_c, "--pretty"), ("--pretty",), tuple()),
                "B1",
                "B1",
            ),
            BrickSpec(
                "B1+ HMM Regime",
                "run_hmm_regime_once.py",
                (("--db", db_r, "--train", "--model", hmm_root, "--pretty"), ("--db", db_r, "--predict", "--model", hmm_root, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--train", "--model", hmm_core, "--pretty"), ("--db", db_c, "--predict", "--model", hmm_core, "--pretty"), ("--pretty",)),
                "B1+",
                "B1",
            ),
            BrickSpec(
                "B2 Cascade Engine",
                "run_cascade_engine_once.py",
                (("--db", db_r, "--pretty"), ("--pretty",), tuple()),
                (("--db", db_c, "--pretty"), ("--pretty",), tuple()),
                "B2",
                "",
            ),
            BrickSpec(
                "B3 Kinematics",
                "run_force_kinematics_once.py",
                (("--db", db_r, "--symbol", symbol, "--start", start, "--end", end, "--json"), ("--db", db_r, "--start", start, "--end", end, "--json")),
                (("--db", db_c, "--symbol", symbol, "--start", start, "--end", end, "--json"), ("--db", db_c, "--start", start, "--end", end, "--json")),
                "B3",
                "",
            ),
            BrickSpec(
                "B4 Temporal Density",
                "run_temporal_density_once.py",
                (("--db", db_r, "--tfs", tfs, "--summary", "--pretty"), ("--db", db_r, "--tfs", tfs, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--tfs", tfs, "--summary", "--pretty"), ("--db", db_c, "--tfs", tfs, "--pretty"), ("--pretty",)),
                "B4",
                "B4",
            ),
            BrickSpec(
                "B4+ Wavelet Density",
                "run_wavelet_density_once.py",
                (("--db", db_r, "--symbol", symbol, "--timeframe", "5", "--pretty"), ("--db", db_r, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--symbol", symbol, "--timeframe", "5", "--pretty"), ("--db", db_c, "--pretty"), ("--pretty",)),
                "B4+",
                "B4",
            ),
            BrickSpec(
                "B5 Spearman Gravity",
                "run_spearman_gravity_once.py",
                (("--db", db_r, "--tfs", tfs, "--summary", "--pretty"), ("--db", db_r, "--tfs", tfs, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--tfs", tfs, "--summary", "--pretty"), ("--db", db_c, "--tfs", tfs, "--pretty"), ("--pretty",)),
                "B5",
                "B5",
            ),
            BrickSpec(
                "B6 Memory Engine",
                "run_memory_query_once.py",
                (("--db", db_r, "--pretty"), ("--pretty",), ("--self-test", "--pretty")),
                (("--db", db_c, "--pretty"), ("--pretty",), ("--self-test", "--pretty")),
                "B6",
                "B6",
            ),
            BrickSpec(
                "B7 Fractal Resonance",
                "run_fractal_resonance_once.py",
                (("--db", db_r, "--symbol", symbol, "--tfs", tfs, "--pretty"), ("--db", db_r, "--symbol", symbol, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--symbol", symbol, "--tfs", tfs, "--pretty"), ("--db", db_c, "--symbol", symbol, "--pretty"), ("--pretty",)),
                "B7",
                "B7",
            ),
            BrickSpec(
                "B7+ Volatility Texture",
                "run_volatility_texture_once.py",
                (("--db", db_r, "--symbol", symbol, "--pretty"), ("--db", db_r, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--symbol", symbol, "--pretty"), ("--db", db_c, "--pretty"), ("--pretty",)),
                "B7+",
                "",
            ),
            BrickSpec(
                "P1 Currency Energy",
                "run_currency_energy_probe_once.py",
                (("--db", db_r, "--symbol", symbol, "--pretty"), ("--db", db_r, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--symbol", symbol, "--pretty"), ("--db", db_c, "--pretty"), ("--pretty",)),
                "P1",
                "",
            ),
            BrickSpec(
                "P2 Alert Mapper",
                "run_behavioral_alert_mapper_once.py",
                (("--db", db_r, "--symbol", symbol, "--pretty"), ("--db", db_r, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--symbol", symbol, "--pretty"), ("--db", db_c, "--pretty"), ("--pretty",)),
                "P2",
                "",
            ),
            BrickSpec(
                "P4 Confluence Alert",
                "run_confluence_alert.py",
                (("--db", db_r, "--once", "--pretty"), ("--db", db_r, "--zone-tf", "15", "--once", "--pretty"), ("--once", "--pretty"), ("--zone-tf", "15", "--once")),
                (("--db", db_c, "--once", "--pretty"), ("--db", db_c, "--zone-tf", "15", "--once", "--pretty"), ("--once", "--pretty"), ("--zone-tf", "15", "--once")),
                "P4",
                "",
            ),
            BrickSpec(
                "Guard Data Quality",
                "run_data_quality_guard_once.py",
                (("--db", db_r, "--since", since, "--pretty"), ("--db", db_r, "--since", since), ("--since", since, "--pretty")),
                (("--db", db_c, "--since", since, "--pretty"), ("--db", db_c, "--since", since), ("--since", since, "--pretty")),
                "GUARD",
                "",
            ),
            BrickSpec(
                "Guard Market Open",
                "run_market_open_validator_once.py",
                (("--db", db_r, "--pretty"), ("--pretty",), tuple()),
                (("--db", db_c, "--pretty"), ("--pretty",), tuple()),
                "GUARD",
                "",
            ),
            BrickSpec(
                "Guard Entropy",
                "run_entropy_engine_once.py",
                (("--db", db_r, "--symbol", symbol, "--pretty"), ("--db", db_r, "--pretty"), ("--pretty",)),
                (("--db", db_c, "--symbol", symbol, "--pretty"), ("--db", db_c, "--pretty"), ("--pretty",)),
                "GUARD",
                "",
            ),
            BrickSpec(
                "Guard Session Overlay",
                "run_session_overlay_once.py",
                (("--pretty",), ("--compact",), tuple()),
                (("--pretty",), ("--compact",), tuple()),
                "GUARD",
                "",
            ),
            BrickSpec(
                "Lab Full V3",
                "lab_powerflow.py",
                (("--query", "full_v3", "--db", db_r, "--symbol", symbol, "--horizons", "MTF", "--once", "--lookback", "300", "--pretty"), ("--query", "full_v3", "--db", db_r, "--symbol", symbol, "--once", "--pretty"), ("--query", "full_v3", "--pretty")),
                (("--query", "full_v3", "--db", db_c, "--symbol", symbol, "--horizons", "MTF", "--once", "--lookback", "300", "--pretty"), ("--query", "full_v3", "--db", db_c, "--symbol", symbol, "--once", "--pretty"), ("--query", "full_v3", "--pretty")),
                "LAB",
                "",
            ),
            BrickSpec(
                "Cycle Orchestrator",
                "run_powerflow_cycle_once.py",
                (("--db", db_r, "--symbol", symbol, "--dry-run", "--pretty"), ("--db", db_r, "--symbol", symbol, "--pretty"), ("--dry-run", "--pretty")),
                (("--db", db_c, "--symbol", symbol, "--dry-run", "--pretty"), ("--db", db_c, "--symbol", symbol, "--pretty"), ("--dry-run", "--pretty")),
                "ORCH",
                "ORCH",
            ),
            BrickSpec(
                "Multi-Symbol Smoke",
                "run_multi_symbol_smoke_tests.py",
                (("--db", db_r, "--pretty"), ("--pretty",), tuple()),
                (("--db", db_c, "--pretty"), ("--pretty",), tuple()),
                "MULTI",
                "",
            ),
        ]

    def run_all(self) -> Dict[str, Any]:
        print("=" * 88)
        print("PowerFlow V7.2 — Batch Test robuste toutes briques V4")
        print(f"Repo      : {self.root}")
        print(f"DB root   : {self.db_root}")
        print(f"DB core   : {self.db_core}")
        print(f"Symbol    : {self.symbol}")
        print(f"TFs       : {self.tfs}")
        print(f"Timestamp : {now_iso()}")
        print("=" * 88)
        print()

        for spec in self.specs():
            print(f"Testing {spec.name:<32}", end=" ", flush=True)
            result = self.run_spec(spec)
            self.results.append(result)
            print(f"[{result['status']}] {result.get('key_info', '')}")

        report = self.build_report()
        self.print_summary(report)
        self.write_reports(report)
        return report

    def run_spec(self, spec: BrickSpec) -> Dict[str, Any]:
        root_runner = self.root / "Core" / spec.runner
        core_runner = self.core / spec.runner

        if not root_runner.exists():
            return {
                "name": spec.name,
                "category": spec.category,
                "critical_group": spec.critical_group,
                "runner": spec.runner,
                "status": "MISSING",
                "error": f"Runner not found: {display_path(root_runner)}",
                "technical_risks": ["RUNNER_NOT_FOUND"],
                "timestamp": now_iso(),
            }

        attempts: List[Dict[str, Any]] = []
        best: Optional[Dict[str, Any]] = None

        candidates: List[Tuple[Path, str, Tuple[str, ...], str]] = []
        for args in spec.arg_sets_root:
            candidates.append((self.root, display_path(root_runner), args, "root"))
        for args in spec.arg_sets_core:
            candidates.append((self.core, spec.runner, args, "core"))

        for cwd, runner_ref, args, mode in candidates:
            cmd = [sys.executable, runner_ref, *args]
            attempt = self.execute(spec, cmd, cwd, args, mode)
            attempts.append({
                "mode": mode,
                "args": list(args),
                "status": attempt.get("status"),
                "returncode": attempt.get("returncode"),
                "error": (attempt.get("error") or "")[:240],
            })

            if attempt["status"] == "PASS":
                attempt["attempts"] = attempts
                return attempt

            if best is None or STATUS_ORDER.get(attempt["status"], 99) < STATUS_ORDER.get(best["status"], 99):
                best = attempt

            # Keep trying all candidates. Old runners have inconsistent CLIs.

        assert best is not None
        best["attempts"] = attempts
        return best

    def execute(self, spec: BrickSpec, cmd: Sequence[str], cwd: Path, args: Sequence[str], mode: str) -> Dict[str, Any]:
        try:
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            proc = subprocess.run(
                list(cmd),
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return {
                "name": spec.name,
                "category": spec.category,
                "critical_group": spec.critical_group,
                "runner": spec.runner,
                "status": "TIMEOUT",
                "cmd": list(cmd),
                "cwd_mode": mode,
                "args_used": list(args),
                "error": f"Execution exceeded {self.timeout}s",
                "technical_risks": ["RUNNER_TIMEOUT"],
                "timestamp": now_iso(),
            }
        except Exception as exc:
            return {
                "name": spec.name,
                "category": spec.category,
                "critical_group": spec.critical_group,
                "runner": spec.runner,
                "status": "ERROR",
                "cmd": list(cmd),
                "cwd_mode": mode,
                "args_used": list(args),
                "error": str(exc),
                "technical_risks": ["RUNNER_EXCEPTION"],
                "timestamp": now_iso(),
            }

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        data = extract_first_json(stdout)

        if proc.returncode == 0 and data is not None:
            risks = collect_risks(data)
            status = "PASS"
            if isinstance(data, dict) and data.get("valid") is False:
                status = "PARTIAL"
                risks.append("VALID_FALSE")
            return {
                "name": spec.name,
                "category": spec.category,
                "critical_group": spec.critical_group,
                "runner": spec.runner,
                "status": status,
                "cmd": list(cmd),
                "cwd_mode": mode,
                "args_used": list(args),
                "returncode": proc.returncode,
                "data": data,
                "key_info": key_info_from_data(data),
                "technical_risks": sorted(set(risks)),
                "timestamp": now_iso(),
            }

        if proc.returncode == 0:
            return {
                "name": spec.name,
                "category": spec.category,
                "critical_group": spec.critical_group,
                "runner": spec.runner,
                "status": "PARTIAL",
                "cmd": list(cmd),
                "cwd_mode": mode,
                "args_used": list(args),
                "returncode": proc.returncode,
                "error": "Returncode 0 but no JSON parsed",
                "raw_output": stdout[:1600],
                "stderr": stderr[:1600],
                "technical_risks": ["JSON_NOT_PARSED"],
                "timestamp": now_iso(),
            }

        return {
            "name": spec.name,
            "category": spec.category,
            "critical_group": spec.critical_group,
            "runner": spec.runner,
            "status": "FAIL",
            "cmd": list(cmd),
            "cwd_mode": mode,
            "args_used": list(args),
            "returncode": proc.returncode,
            "error": (stderr or stdout or "Runner failed")[:1600],
            "raw_output": stdout[:1600],
            "stderr": stderr[:1600],
            "technical_risks": ["RUNNER_RETURNED_NON_ZERO"],
            "timestamp": now_iso(),
        }

    def build_report(self) -> Dict[str, Any]:
        counts = {status: 0 for status in ["PASS", "PARTIAL", "MISSING", "TIMEOUT", "FAIL", "ERROR"]}
        for result in self.results:
            counts[result["status"]] = counts.get(result["status"], 0) + 1

        # Critical logic by group:
        # a group is critical only if no member in that group passes.
        group_status: Dict[str, List[str]] = {}
        for r in self.results:
            group = r.get("critical_group")
            if not group:
                continue
            group_status.setdefault(group, []).append(r["status"])

        critical_failures = []
        for group, statuses in group_status.items():
            if "PASS" not in statuses and "PARTIAL" not in statuses:
                critical_failures.append(group)

        if critical_failures:
            verdict = "FAIL_INVESTIGATE_CRITICAL_GROUP"
        elif counts.get("FAIL") or counts.get("TIMEOUT") or counts.get("ERROR"):
            verdict = "PARTIAL_INVESTIGATE_NON_CRITICAL"
        elif counts.get("PARTIAL") or counts.get("MISSING"):
            verdict = "PARTIAL_ACCEPTABLE_IF_WEEKEND"
        else:
            verdict = "PASS_READY_FOR_PROMPT_3"

        return {
            "timestamp": now_iso(),
            "db_path_root": self.db_root,
            "db_path_core": self.db_core,
            "symbol": self.symbol,
            "timeframes": self.tfs,
            "total_tests": len(self.results),
            "summary": {
                "pass": counts.get("PASS", 0),
                "partial": counts.get("PARTIAL", 0),
                "missing": counts.get("MISSING", 0),
                "timeout": counts.get("TIMEOUT", 0),
                "fail": counts.get("FAIL", 0),
                "error": counts.get("ERROR", 0),
            },
            "critical_group_status": group_status,
            "critical_failures": critical_failures,
            "verdict": verdict,
            "results": self.results,
        }

    def print_summary(self, report: Dict[str, Any]) -> None:
        s = report["summary"]
        print()
        print("=" * 88)
        print("SUMMARY")
        print(f"PASS    : {s['pass']}/{report['total_tests']}")
        print(f"PARTIAL : {s['partial']}/{report['total_tests']}")
        print(f"MISSING : {s['missing']}/{report['total_tests']}")
        print(f"TIMEOUT : {s['timeout']}/{report['total_tests']}")
        print(f"FAIL    : {s['fail']}/{report['total_tests']}")
        print(f"ERROR   : {s['error']}/{report['total_tests']}")
        print(f"VERDICT : {report['verdict']}")
        if report["critical_failures"]:
            print("Critical group failures: " + ", ".join(report["critical_failures"]))
        print("=" * 88)

    def write_reports(self, report: Dict[str, Any]) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.output_dir / f"batch_test_report_{stamp}.json"
        csv_path = self.output_dir / "BRICKS_SUMMARY.csv"
        html_path = self.output_dir / "HEALTH_CHECK.html"
        md_path = self.output_dir / "BATCH_TEST_NARRATIVE.md"

        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        self.write_csv(csv_path)
        self.write_html(html_path, report)
        self.write_markdown(md_path, report)

        print()
        print(f"JSON     : {display_path(json_path)}")
        print(f"CSV      : {display_path(csv_path)}")
        print(f"HTML     : {display_path(html_path)}")
        print(f"Markdown : {display_path(md_path)}")

    def write_csv(self, path: Path) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Brique", "Categorie", "Runner", "Status", "Critical Group", "Key Info", "Technical Risks", "Action"])
            for r in self.results:
                status = r.get("status", "")
                if status == "PASS":
                    action = "OK"
                elif status == "PARTIAL":
                    action = "Qualifier limite weekend / JSON / data"
                elif status == "MISSING":
                    action = "Runner absent: confirmer si attendu"
                else:
                    action = "Investiguer runner/args/runtime"
                writer.writerow([
                    r.get("name", ""),
                    r.get("category", ""),
                    r.get("runner", ""),
                    status,
                    r.get("critical_group", ""),
                    r.get("key_info", "") or r.get("error", "")[:200],
                    "; ".join(r.get("technical_risks", [])),
                    action,
                ])

    def write_html(self, path: Path, report: Dict[str, Any]) -> None:
        s = report["summary"]
        cards = []
        for r in self.results:
            status = r.get("status", "UNKNOWN")
            cls = status.lower()
            info = r.get("key_info", "") or r.get("error", "No info")
            risks = ", ".join(r.get("technical_risks", [])) or "—"
            cards.append(f"""
<section class="card {cls}">
  <div class="top">
    <h2>{html.escape(r.get("name", "?"))}</h2>
    <span class="badge {cls}">{html.escape(status)}</span>
  </div>
  <p><strong>Runner:</strong> {html.escape(r.get("runner", ""))}</p>
  <p><strong>Mode:</strong> {html.escape(str(r.get("cwd_mode", "—")))}</p>
  <p><strong>Info:</strong> {html.escape(str(info)[:240])}</p>
  <p><strong>Risques techniques:</strong> {html.escape(risks)}</p>
</section>""")

        content = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>PowerFlow V7.2 — Health Check</title>
<style>
body {{ margin:0; padding:24px; background:#111; color:#e8e8e8; font-family:Consolas,'Courier New',monospace; }}
h1 {{ margin:0 0 8px; }}
.meta {{ color:#aaa; margin-bottom:20px; }}
.summary {{ display:grid; grid-template-columns:repeat(6,minmax(110px,1fr)); gap:10px; margin:20px 0; }}
.tile {{ background:#1d1d1d; border:1px solid #333; border-radius:10px; padding:14px; }}
.tile strong {{ display:block; font-size:24px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:14px; }}
.card {{ background:#1a1a1a; border-left:6px solid #777; border-radius:10px; padding:14px 16px; box-shadow:0 2px 16px rgba(0,0,0,.25); }}
.card.pass {{ border-left-color:#22c55e; }}
.card.partial {{ border-left-color:#eab308; }}
.card.missing {{ border-left-color:#777; }}
.card.timeout, .card.fail, .card.error {{ border-left-color:#ef4444; }}
.top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
h2 {{ font-size:16px; margin:0 0 8px; color:#fff; }}
p {{ margin:6px 0; color:#cfcfcf; }}
.badge {{ border-radius:999px; padding:4px 10px; font-weight:bold; color:#111; }}
.badge.pass {{ background:#22c55e; }}
.badge.partial {{ background:#eab308; }}
.badge.missing {{ background:#999; }}
.badge.timeout, .badge.fail, .badge.error {{ background:#ef4444; color:#fff; }}
.verdict {{ padding:14px 16px; border:1px solid #444; border-radius:10px; margin:16px 0 22px; background:#181818; }}
</style>
</head>
<body>
<h1>PowerFlow V7.2 — Health Check</h1>
<div class="meta">Timestamp: {html.escape(report['timestamp'])} | DB: {html.escape(report['db_path_root'])} | Symbol: {html.escape(report['symbol'])}</div>
<div class="summary">
  <div class="tile">PASS<strong>{s['pass']}</strong></div>
  <div class="tile">PARTIAL<strong>{s['partial']}</strong></div>
  <div class="tile">MISSING<strong>{s['missing']}</strong></div>
  <div class="tile">TIMEOUT<strong>{s['timeout']}</strong></div>
  <div class="tile">FAIL<strong>{s['fail']}</strong></div>
  <div class="tile">ERROR<strong>{s['error']}</strong></div>
</div>
<div class="verdict"><strong>Verdict:</strong> {html.escape(report['verdict'])}</div>
<div class="grid">
{''.join(cards)}
</div>
</body>
</html>"""
        path.write_text(content, encoding="utf-8")

    def write_markdown(self, path: Path, report: Dict[str, Any]) -> None:
        s = report["summary"]
        lines = [
            "# PowerFlow V7.2 — Batch Test Report",
            "",
            f"**Timestamp:** {report['timestamp']}",
            f"**DB root:** `{report['db_path_root']}`",
            f"**DB core:** `{report['db_path_core']}`",
            f"**Symbol:** `{report['symbol']}`",
            f"**Timeframes:** `{report['timeframes']}`",
            "",
            "## Résumé",
            "",
            f"- PASS: **{s['pass']}**",
            f"- PARTIAL: **{s['partial']}**",
            f"- MISSING: **{s['missing']}**",
            f"- TIMEOUT: **{s['timeout']}**",
            f"- FAIL: **{s['fail']}**",
            f"- ERROR: **{s['error']}**",
            f"- Verdict: **{report['verdict']}**",
            "",
        ]

        if report["critical_failures"]:
            lines.append("## Groupes critiques bloqués")
            lines.append("")
            for group in report["critical_failures"]:
                lines.append(f"- {group}")
            lines.append("")

        lines.append("## Détail par brique")
        lines.append("")
        for r in self.results:
            lines.append(f"### {r.get('name')} — `{r.get('status')}`")
            lines.append("")
            lines.append(f"- Runner: `{r.get('runner')}`")
            lines.append(f"- Catégorie: `{r.get('category')}`")
            lines.append(f"- Groupe critique: `{r.get('critical_group') or '—'}`")
            lines.append(f"- Mode réussi/meilleur: `{r.get('cwd_mode', '—')}`")
            info = r.get("key_info") or r.get("error", "")
            if info:
                lines.append(f"- Info: {info}")
            risks = r.get("technical_risks", [])
            if risks:
                lines.append(f"- Risques techniques: {', '.join(risks)}")
            if r.get("status") != "PASS":
                lines.append("- Action: investiguer si le groupe critique échoue, sinon qualifier comme limite technique.")
            lines.append("")

        lines += [
            "## Prochaines étapes",
            "",
            "1. Si verdict PASS_READY_FOR_PROMPT_3 ou PARTIAL_ACCEPTABLE_IF_WEEKEND: passer au dashboard.",
            "2. Si verdict PARTIAL_INVESTIGATE_NON_CRITICAL: lire les FAIL non critiques et décider s'ils bloquent vraiment.",
            "3. Si verdict FAIL_INVESTIGATE_CRITICAL_GROUP: corriger le groupe critique puis relancer.",
            "",
            "## Doctrine",
            "",
            "- Ce batch observe. Il ne décide pas.",
            "- Aucun BUY/SELL.",
            "- Aucun write manuel DB.",
            "- Les outputs sont des rapports de perception technique.",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow V7.2 robust batch tester V4")
    parser.add_argument("--db", default=r"Core\powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--tfs", default="1,5,15,30,60")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output-dir", default="output")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    root = repo_root_from_script()
    os.chdir(root)

    tester = BrickTester(
        root=root,
        db_root=args.db,
        symbol=args.symbol,
        tfs=args.tfs,
        timeout=args.timeout,
        output_dir=args.output_dir,
    )
    report = tester.run_all()

    if report["verdict"] == "FAIL_INVESTIGATE_CRITICAL_GROUP":
        return 2
    if report["summary"]["fail"] or report["summary"]["error"] or report["summary"]["timeout"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
