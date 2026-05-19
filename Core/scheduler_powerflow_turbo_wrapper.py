#!/usr/bin/env python3
"""
PowerFlow V7.3 turbo scheduler wrapper.

Purpose:
- Run the existing multi-symbol PowerFlow scheduler once.
- Then refresh the auxiliary surface layers:
  data health, ontology, signal adaptive, price schema, topdown reader.

Doctrine:
- Read-only analytical layers after the scheduler core.
- No trade decision, no BUY/SELL output.
- M1 is qualified, never censored.
- V7.3 topdown stack: HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
import time
import sqlite3
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

# PowerFlow V7.6.7 core multi-symbol environment guard
os.environ.setdefault('POWERFLOW_SYMBOL', 'GBPUSD')
os.environ.setdefault('POWERFLOW_SYMBOLS', 'GBPUSD,EURUSD,AUDUSD,NZDUSD,USDJPY,USDCAD,USDCHF,EURGBP,GBPJPY,GBPAUD,GBPCAD,GBPCHF,GBPNZD')

# --- B9 Scheduler Live Integration / DRY-RUN contract ---
# B9 stays fail-soft: if the runtime module is missing or raises, the turbo wrapper continues.
# Telegram is always OFF here; this wrapper only transmits perception into output/b9_nodes_live.
try:
    from b9_runtime_integration import init_b9_runtime, process_tick_window_b9
except Exception as _b9_import_exc:  # pragma: no cover - depends on local runtime pack
    init_b9_runtime = None  # type: ignore[assignment]
    process_tick_window_b9 = None  # type: ignore[assignment]
    B9_IMPORT_ERROR = repr(_b9_import_exc)
else:
    B9_IMPORT_ERROR = None

B9_LIVE_SYMBOL = "GBPUSD"
B9_TICK_WINDOW_LIMIT = int(os.environ.get("B9_TICK_WINDOW_LIMIT", "300"))
B9_ALLOW_CORE_MISSING = os.environ.get("B9_ALLOW_CORE_MISSING", "1") not in {"0", "false", "False", "NO", "no"}
POWERFLOW_CORE_SCHEDULER = os.environ.get("POWERFLOW_CORE_SCHEDULER", "").strip()



TAIL_LIMIT = 12000


@dataclass
class StepResult:
    label: str
    returncode: int
    elapsed_seconds: float
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _now_seconds() -> float:
    return time.perf_counter()


def _emit_tail(label: str, stream_name: str, text: str, limit: int = TAIL_LIMIT) -> None:
    if not text:
        return
    clean = text.strip()
    if not clean:
        return
    if len(clean) > limit:
        clean = "[...TRUNCATED_TO_TAIL...]\n" + clean[-limit:]
    print(f"{stream_name} {label}: {clean}")


def _resolve_command_and_cwd(command: Sequence[str], cwd: Path) -> tuple[List[str], Path]:
    """Resolve Python script commands against the actual repo layout.

    The local repo can contain a nested Core/Core folder. If a script is found
    there, run it with that folder as cwd so its own relative runner calls work.
    """
    parts = [str(part) for part in command]
    if len(parts) < 2 or not parts[1].lower().endswith(".py"):
        return parts, cwd

    script = Path(parts[1])
    if script.is_absolute():
        if script.exists():
            return parts, script.parent
        return parts, cwd

    direct = cwd / script
    nested = cwd / "Core" / script
    parent_nested = cwd.parent / "Core" / script

    if direct.exists():
        parts[1] = str(direct)
        return parts, direct.parent
    if nested.exists():
        parts[1] = str(nested)
        return parts, nested.parent
    if parent_nested.exists():
        parts[1] = str(parent_nested)
        return parts, parent_nested.parent

    return parts, cwd


def run_step(label: str, command: Sequence[str], cwd: Path, required: bool = True) -> StepResult:
    started = _now_seconds()
    resolved_command, resolved_cwd = _resolve_command_and_cwd(command, cwd)
    printable = " ".join(str(part) for part in resolved_command)
    print(f"> {printable}")
    if resolved_cwd != cwd:
        print(f"STEP_CWD {label}: {resolved_cwd}")

    proc = subprocess.run(
        resolved_command,
        cwd=str(resolved_cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    elapsed = round(_now_seconds() - started, 3)
    result = StepResult(
        label=label,
        returncode=proc.returncode,
        elapsed_seconds=elapsed,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )

    status = "OK" if result.ok else "FAIL"
    print(f"STEP_END {label} status={status} returncode={result.returncode} elapsed={elapsed}s")
    _emit_tail(label, "STDOUT", result.stdout)
    _emit_tail(label, "STDERR", result.stderr)

    if required and not result.ok:
        raise RuntimeError(f"required step failed: {label} returncode={result.returncode}")

    return result


def parse_symbols(raw: str) -> str:
    symbols = [part.strip().upper() for part in raw.split(",") if part.strip()]
    if not symbols:
        raise ValueError("no symbols provided")
    return ",".join(symbols)


# --- B9 live helpers -------------------------------------------------------

def _b9_symbols_contains(symbols: str, target: str = B9_LIVE_SYMBOL) -> bool:
    return target.upper() in {part.strip().upper() for part in symbols.split(",") if part.strip()}


def _b9_quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _b9_connect_readonly(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _b9_tick_db_candidates(core: Path) -> List[Path]:
    return [
        core / "tick_archive.db",
        core.parent / "tick_archive.db",
        core / "data" / "tick_archive.db",
        core.parent / "data" / "tick_archive.db",
        Path.cwd() / "tick_archive.db",
    ]


def _b9_find_tick_archive(core: Path) -> Optional[Path]:
    for candidate in _b9_tick_db_candidates(core):
        if candidate.exists():
            return candidate
    return None


def _b9_table_names(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [str(row[0]) for row in rows]


def _b9_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({_b9_quote_identifier(table)})").fetchall()
    return [str(row[1]) for row in rows]


def _b9_pick_column(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    lower_to_original = {col.lower(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in lower_to_original:
            return lower_to_original[candidate.lower()]
    for col in columns:
        col_l = col.lower()
        for candidate in candidates:
            if candidate.lower() in col_l:
                return col
    return None


def _b9_choose_tick_table(conn: sqlite3.Connection) -> Optional[str]:
    tables = _b9_table_names(conn)
    if not tables:
        return None

    preferred = ["ticks", "tick_archive", "mt4_ticks", "raw_ticks", "tick_data", "market_ticks", "quotes"]
    lower_to_original = {table.lower(): table for table in tables}
    for name in preferred:
        if name in lower_to_original:
            return lower_to_original[name]

    scored: List[tuple[int, str]] = []
    for table in tables:
        tl = table.lower()
        score = 0
        if "tick" in tl:
            score += 10
        if "quote" in tl:
            score += 6
        if "price" in tl:
            score += 3
        if score:
            scored.append((score, table))
    if not scored:
        return tables[0]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]


def _b9_normalize_tick_row(row: Dict[str, Any], symbol: str, time_col: str) -> Dict[str, Any]:
    item = dict(row)
    item.setdefault("symbol", symbol)
    if "timestamp" not in item and time_col in item:
        item["timestamp"] = item[time_col]

    if "current_price" not in item:
        bid = item.get("bid")
        ask = item.get("ask")
        price = item.get("price", item.get("last", item.get("close")))
        try:
            if bid is not None and ask is not None:
                item["current_price"] = (float(bid) + float(ask)) / 2.0
            elif price is not None:
                item["current_price"] = float(price)
        except Exception:
            pass
    return item


def _b9_load_tick_window(core: Path, symbol: str = B9_LIVE_SYMBOL, limit: int = B9_TICK_WINDOW_LIMIT) -> List[Dict[str, Any]]:
    db_path = _b9_find_tick_archive(core)
    if db_path is None:
        print("[B9] tick_archive.db not found; live node creation skipped")
        return []

    try:
        with _b9_connect_readonly(db_path) as conn:
            table = _b9_choose_tick_table(conn)
            if not table:
                print(f"[B9] no table found in {db_path}; live node creation skipped")
                return []

            columns = _b9_table_columns(conn, table)
            if not columns:
                print(f"[B9] no columns in {db_path}:{table}; live node creation skipped")
                return []

            time_col = _b9_pick_column(columns, ["timestamp", "time", "datetime", "ts", "created_at", "date"])
            if not time_col:
                print(f"[B9] no timestamp column detected in {db_path}:{table}; live node creation skipped")
                return []

            symbol_col = _b9_pick_column(columns, ["symbol", "pair", "instrument"])
            params: List[Any] = []
            where_sql = ""
            if symbol_col:
                where_sql = f" WHERE UPPER({_b9_quote_identifier(symbol_col)}) = ?"
                params.append(symbol.upper())

            query = (
                f"SELECT * FROM {_b9_quote_identifier(table)}"
                f"{where_sql}"
                f" ORDER BY {_b9_quote_identifier(time_col)} DESC"
                " LIMIT ?"
            )
            params.append(int(limit))
            rows = conn.execute(query, params).fetchall()
            raw_items = [dict(zip(columns, row)) for row in rows]
            items = [_b9_normalize_tick_row(row, symbol=symbol.upper(), time_col=time_col) for row in reversed(raw_items)]
            print(f"[B9] Loaded tick window symbol={symbol.upper()} ticks={len(items)} source={db_path.name}:{table}")
            return items
    except Exception as exc:
        print(f"[B9] ERROR loading tick window: {exc}")
        return []


def _b9_init_runtime(core: Path) -> bool:
    if init_b9_runtime is None:
        print(f"[B9] Runtime unavailable; import_error={B9_IMPORT_ERROR}")
        return False

    output_dir = core / "output" / "b9_nodes_live"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        init_b9_runtime(
            {
                "ENABLE_TELEGRAM": False,
                "DB_PATH": str(core / "powerflow.db"),
                "SOURCE_MODE": "SCHEDULER_TURBO_WRAPPER",
            },
            str(output_dir),
        )
    except Exception as exc:
        print(f"[B9] Runtime init failed; Telegram OFF; error={exc}")
        return False

    print(f"[B9] Engine initialized - Telegram OFF (DRY-RUN) - output={output_dir}")
    return True



def _b9_first_value(row: Dict[str, Any], names: Sequence[str]) -> Any:
    lower = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    for key, value in row.items():
        kl = str(key).lower()
        for name in names:
            if name.lower() in kl:
                return value
    return None


def _b9_float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _b9_compact_window_data(window_data: Sequence[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
    compact: List[Dict[str, Any]] = []
    for row in window_data:
        ts = _b9_first_value(row, ["timestamp", "time", "datetime", "ts", "created_at", "date"])
        bid = _b9_float_or_none(_b9_first_value(row, ["bid"]))
        ask = _b9_float_or_none(_b9_first_value(row, ["ask"]))
        price = _b9_float_or_none(_b9_first_value(row, ["current_price", "price", "last", "close", "mid"]))

        if price is None and bid is not None and ask is not None:
            price = (bid + ask) / 2.0
        if bid is None and price is not None:
            bid = price
        if ask is None and price is not None:
            ask = price

        item: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "timestamp": str(ts) if ts is not None else "",
            "bid": bid,
            "ask": ask,
            "price": price,
            "current_price": price,
        }
        compact.append(item)
    return compact



def _b9_build_window_payload(window_data: Sequence[Dict[str, Any]], symbol: str, source: str = "tick_archive.db:tick_stream") -> Dict[str, Any]:
    """Build the dict contract expected by b9_runtime_integration.process_tick_window_b9."""
    ticks = list(window_data)
    payload: Dict[str, Any] = {
        "symbol": symbol.upper(),
        "ticks": ticks,
        "tick_window": ticks,
        "window_data": ticks,
        "source": source,
        "source_mode": "SCHEDULER_TICK_ARCHIVE",
        "source_stack": "SCHEDULER_TURBO_WRAPPER",
        "telegram_enabled": False,
        "ENABLE_TELEGRAM": False,
        "metadata": {
            "symbol": symbol.upper(),
            "tick_count": len(ticks),
            "source": source,
            "telegram_enabled": False,
            "contract": "B9_WINDOW_DICT_V1",
        },
    }
    if ticks:
        payload["start_timestamp"] = ticks[0].get("timestamp")
        payload["end_timestamp"] = ticks[-1].get("timestamp")
        payload["current_price"] = ticks[-1].get("current_price") or ticks[-1].get("price")
    return payload


def _b9_log_runtime_result(prefix: str, result: Dict[str, Any]) -> None:
    status = result.get("status", "UNKNOWN")
    risks = result.get("technical_risks") or result.get("risks") or []
    error = result.get("error") or result.get("exception") or result.get("message") or result.get("reason")
    print(f"[B9] {prefix} status={status} risks={risks}")
    if error:
        print(f"[B9] {prefix} error={error}")
    try:
        preview = json.dumps(result, ensure_ascii=False, default=str)[:1600]
        print(f"[B9] {prefix} result_preview={preview}")
    except Exception:
        pass



def _b9_process_after_scheduler_core(core: Path, symbols: str, runtime_ready: bool) -> Optional[Dict[str, Any]]:
    if not runtime_ready:
        return None
    if not _b9_symbols_contains(symbols, B9_LIVE_SYMBOL):
        print(f"[B9] {B9_LIVE_SYMBOL} not requested; B9 live window skipped")
        return None
    if process_tick_window_b9 is None:
        print(f"[B9] process_tick_window_b9 unavailable; import_error={B9_IMPORT_ERROR}")
        return None

    window_data = _b9_load_tick_window(core, B9_LIVE_SYMBOL)
    if not window_data:
        print("[B9] No GBPUSD window_data available; node not created")
        return None

    try:
        raw_payload = _b9_build_window_payload(
            window_data,
            B9_LIVE_SYMBOL,
            source="tick_archive.db:tick_stream",
        )
        print(f"[B9] Sending window payload contract=dict ticks={len(window_data)}")
        result = process_tick_window_b9(B9_LIVE_SYMBOL, raw_payload)
        if not isinstance(result, dict):
            print(f"[B9] Unexpected runtime result type: {type(result).__name__}")
            return None

        if result.get("status") == "B9_RUNTIME_ERROR":
            _b9_log_runtime_result("Runtime raw-dict-window", result)
            compact_window = _b9_compact_window_data(window_data, B9_LIVE_SYMBOL)
            compact_payload = _b9_build_window_payload(
                compact_window,
                B9_LIVE_SYMBOL,
                source="tick_archive.db:tick_stream:compact",
            )
            print(f"[B9] Retrying with compact dict tick window rows={len(compact_window)}")
            retry_result = process_tick_window_b9(B9_LIVE_SYMBOL, compact_payload)
            if isinstance(retry_result, dict):
                result = retry_result
            else:
                print(f"[B9] Unexpected compact retry result type: {type(retry_result).__name__}")
                return None

        status = result.get("status", "UNKNOWN")
        node = result.get("node") or {}
        if status == "NODE_CREATED":
            verdict = node.get("verdict", node.get("price_verdict_candidate", "UNKNOWN"))
            price = node.get("current_price", node.get("price", "n/a"))
            node_id = node.get("node_id", node.get("id", "n/a"))
            print(f"[B9] Node created: id={node_id} verdict={verdict} price={price}")
        else:
            _b9_log_runtime_result("Runtime", result)
        return result
    except Exception as exc:
        print(f"[B9] ERROR: {exc}")
        return None


def _b9_find_core_scheduler(core: Path) -> Optional[Path]:
    if POWERFLOW_CORE_SCHEDULER:
        explicit_raw = Path(POWERFLOW_CORE_SCHEDULER)
        explicit_candidates: List[Path]
        if explicit_raw.is_absolute():
            explicit_candidates = [explicit_raw]
        else:
            explicit_candidates = [
                core / explicit_raw,
                core / "Core" / explicit_raw,
                core.parent / "Core" / explicit_raw,
            ]
        for explicit in explicit_candidates:
            if explicit.exists():
                print(f"[B9] POWERFLOW_CORE_SCHEDULER selected: {explicit}")
                return explicit
        print("[B9] POWERFLOW_CORE_SCHEDULER not found in candidates: " + ", ".join(str(p) for p in explicit_candidates))

    candidates = [
        "run_powerflow_live_stack_once.py",
        "run_powerflow_cycle_once.py",
        "run_powerflow_live_once.py",
        "scheduler_powerflow.py",
        "scheduler_powerflow_live.py",
        "scheduler_powerflow_v7.py",
    ]
    for name in candidates:
        for base_dir in [core, core / "Core", core.parent / "Core"]:
            direct = base_dir / name
            if direct.exists():
                return direct

    scored: List[tuple[int, Path]] = []
    for root in [core, core.parent]:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            name = path.name.lower()
            score = 0
            if "scheduler" in name:
                score += 20
            if "powerflow" in name:
                score += 15
            if "live" in name:
                score += 8
            if "cycle" in name:
                score += 5
            if "wrapper" in name:
                score -= 10
            if path.name == Path(__file__).name:
                score -= 100
            if score > 0:
                scored.append((score, path))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], str(item[1])))
    selected = scored[0][1]
    print(f"[B9] Auto-selected scheduler_core script: {selected}")
    return selected


def _b9_scheduler_core_command(py: str, core: Path, symbols: str) -> Optional[List[str]]:
    script = _b9_find_core_scheduler(core)
    if script is None:
        return None

    name = script.name.lower()
    if name == "scheduler_powerflow.py":
        return [py, str(script), "--once", "--symbols", symbols]

    if name == "run_powerflow_live_stack_once.py":
        return [py, str(script), "--symbols", symbols, "--primary", B9_LIVE_SYMBOL]

    if name.endswith("_once.py") or name.startswith("run_"):
        return [py, str(script), "--symbols", symbols]

    return [py, str(script), "--symbols", symbols]


# --- End B9 live helpers ---------------------------------------------------




def is_overlap_skip(result: StepResult) -> bool:
    text = f"{result.stdout}\n{result.stderr}".upper()
    return result.label == "scheduler_core" and "OVERLAP_SKIP" in text
def build_steps(py: str, symbols: str, core: Path) -> List[tuple[str, List[str]]]:
    scheduler_core_command = _b9_scheduler_core_command(py, core, symbols)
    steps: List[tuple[str, List[str]]] = []
    if scheduler_core_command is None:
        print("[B9] scheduler_core script not found; B9 direct tick_archive pass will still run")
    else:
        steps.append(("scheduler_core", scheduler_core_command))

    steps.extend([
        (
            "data_health_monitor",
            [
                py,
                "run_data_health_monitor_once.py",
                "--db",
                "powerflow.db",
                "--symbols",
                symbols,
                "--output",
                "output/data_health_monitor.json",
            ],
        ),
        (
            "data_health_normalize",
            [
                py,
                "dashboard_normalize_data_health.py",
                "--input",
                "output/data_health_monitor.json",
                "--output",
                "output/dashboard_surface/data_health.json",
            ],
        ),
        (
            "flow_ontology_cycle",
            [py, "run_flow_ontology_cycle_once.py", "--symbols", symbols],
        ),
        (
            "signal_adaptive_all",
            [
                py,
                "run_signal_adaptive_all_once.py",
                "--symbols",
                symbols,
                "--data-health",
                "output/data_health_monitor.json",
            ],
        ),
        (
            "signal_adaptive_normalize",
            [
                py,
                "dashboard_normalize_signal_adaptive.py",
                "--input",
                "output/dashboard_surface/signal_adaptive_profiles.json",
                "--output",
                "output/dashboard_surface/signal_adaptive.json",
            ],
        ),
        (
            "price_schema_probe",
            [py, "pf_price_schema_probe.py"],
        ),
        (
            "topdown_market_reader_all",
            [py, "run_topdown_market_reader_all_once.py", "--symbols", symbols],
        ),
        (
            "topdown_reader_normalize",
            [
                py,
                "dashboard_normalize_topdown_reader.py",
                "--input",
                "output/dashboard_surface/topdown_market_reader.json",
                "--output",
                "output/dashboard_surface/topdown_reader.json",
            ],
        ),
    ])
    return steps


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.3 turbo wrapper")
    parser.add_argument("--symbols", default=os.environ.get("POWERFLOW_SYMBOLS", "GBPUSD,EURUSD,AUDUSD,NZDUSD,USDJPY,USDCAD,USDCHF,EURGBP,GBPJPY,GBPAUD,GBPCAD,GBPCHF,GBPNZD"))
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    core = Path(__file__).resolve().parent
    symbols = parse_symbols(args.symbols)
    py = sys.executable

    started = _now_seconds()
    results: List[StepResult] = []
    errors: List[str] = []

    print(f"TURBO_V73_CYCLE_START | symbols={symbols} | core={core}")

    b9_runtime_ready = _b9_init_runtime(core) if _b9_symbols_contains(symbols, B9_LIVE_SYMBOL) else False
    b9_processed = False

    for label, command in build_steps(py, symbols, core):
        try:
            result = run_step(label, command, cwd=core, required=not args.continue_on_error)
            results.append(result)
            if label == "scheduler_core":
                _b9_process_after_scheduler_core(core, symbols, b9_runtime_ready)
                b9_processed = True
        except Exception as exc:
            if label == "scheduler_core":
                _b9_process_after_scheduler_core(core, symbols, b9_runtime_ready)
                b9_processed = True
                if B9_ALLOW_CORE_MISSING:
                    print("[B9] scheduler_core failed, but B9 dry-run hook was attempted; continuing because B9_ALLOW_CORE_MISSING=1")
                    continue
            errors.append(f"{label}:{exc}")
            print(f"STEP_EXCEPTION {label}: {exc}")
            if not args.continue_on_error:
                elapsed = round(_now_seconds() - started, 3)
                print(
                    "TURBO_V73_CYCLE_FAIL | "
                    f"symbols={symbols} | completed_steps={len(results)} | "
                    f"errors={len(errors)} | duration_seconds={elapsed}"
                )
                return 1

    if not b9_processed:
        _b9_process_after_scheduler_core(core, symbols, b9_runtime_ready)
        b9_processed = True

    overlap_skips = [result.label for result in results if is_overlap_skip(result)]
    if overlap_skips and args.continue_on_error:
        print("TURBO_V73_OVERLAP_SKIP_CONTINUE | scheduler_core lock active; continuing analytical layers")
    failed = [
        result.label
        for result in results
        if not result.ok and not (args.continue_on_error and is_overlap_skip(result))
    ]
    errors.extend(failed)
    elapsed = round(_now_seconds() - started, 3)

    if errors:
        print(
            "TURBO_V73_CYCLE_FAIL | "
            f"symbols={symbols} | steps={len(results)} | errors={errors} | "
            f"duration_seconds={elapsed}"
        )
        return 1


    run_step("gbpusd_live_decision", [
        sys.executable, "pf_gbpusd_live_decision_once.py",
    ], core)
    run_step("cockpit_live_status", [
        sys.executable, "pf_cockpit_live_status_once.py",
    ], core)
    run_step("powerflow_live_brief", [
        sys.executable, "pf_powerflow_live_brief_once.py",
    ], core)
    run_step("live_brief_normalize", [
        sys.executable, "dashboard_normalize_live_brief.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/live_brief_dashboard.json",
    ], core)

    run_step("b6_live_fusion", [
        sys.executable, "pf_b6_live_fusion_once.py",
    ], core)
    run_step("b6_live_fusion_normalize", [
        sys.executable, "dashboard_normalize_b6_live_fusion.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/b6_live_fusion_dashboard.json",
    ], core)
    run_step("multiread_synthesis", [
        sys.executable, "pf_powerflow_multiread_synthesis_once.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/powerflow_multiread_synthesis.json",
    ], core)
    run_step("multiread_synthesis_normalize", [
        sys.executable, "dashboard_normalize_multiread_synthesis.py",
        "--input", "output/dashboard_surface/powerflow_multiread_synthesis.json",
        "--output", "output/dashboard_surface/multiread_synthesis_dashboard.json",
    ], core)

    run_step("time_profile_ltf", [
        sys.executable, "run_ltf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profile_mtf", [
        sys.executable, "run_mtf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profile_htf", [
        sys.executable, "run_htf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profiles_normalize", [
        sys.executable, "dashboard_normalize_time_profiles.py",
        "--symbol", "GBPUSD",
        "--output", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)

    run_step("trader_cockpit", [
        sys.executable, "pf_trader_cockpit_once.py",
        "--symbols", symbols,
        "--trade-symbol", "GBPUSD",
        "--output", "output/dashboard_surface/trader_cockpit.json",
        "--txt", "output/dashboard_surface/trader_cockpit.txt",
    ], core)
    run_step("trader_cockpit_time_profiles_enrich", [
        sys.executable, "pf_trader_cockpit_time_profiles_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)

    run_step("b8_cross_surface", [
        sys.executable, "pf_b8_cross_surface_once.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/b8_cross_surface.json",
        "--txt", "output/dashboard_surface/b8_cross_surface.txt",
    ], core)

    run_step("trader_cockpit_b8_enrich", [
        sys.executable, "pf_trader_cockpit_b8_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--b8", "output/dashboard_surface/b8_cross_surface.json",
    ], core)

    run_step("phase_synthesis", [
        sys.executable, "pf_phase_synthesizer_once.py",
        "--symbol", "GBPUSD",
        "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
        "--cockpit", "output/dashboard_surface/trader_cockpit.json",
        "--b8", "output/dashboard_surface/b8_cross_surface.json",
        "--output", "output/dashboard_surface/phase_synthesis.json",
        "--txt", "output/dashboard_surface/phase_synthesis.txt",
    ], core)

    run_step("trader_cockpit_phase_enrich", [
        sys.executable, "pf_trader_cockpit_phase_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--phase", "output/dashboard_surface/phase_synthesis.json",
    ], core)

    run_step("evidence_bus", [
        sys.executable, "pf_evidence_bus_once.py",
        "--symbol", "GBPUSD",
        "--output", "output/dashboard_surface/evidence_bus.json",
        "--txt", "output/dashboard_surface/evidence_bus.txt",
    ], core)

    run_step("evidence_reading", [
        sys.executable, "pf_evidence_reading_once.py",
        "--evidence-bus", "output/dashboard_surface/evidence_bus.json",
        "--output", "output/dashboard_surface/evidence_reading.json",
        "--txt", "output/dashboard_surface/evidence_reading.txt",
    ], core)

    run_step("trader_cockpit_evidence_enrich", [
        sys.executable, "pf_trader_cockpit_evidence_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--evidence-reading", "output/dashboard_surface/evidence_reading.json",
        "--evidence-bus", "output/dashboard_surface/evidence_bus.json",
    ], core)

    run_step("dashboard_v74_contract_check", [
        sys.executable, "dashboard_v74_contract_check.py",
        "--html", "dashboard_powerflow_v74.html",
    ], core, required=False)

    run_step("trader_journal_j1", [
        sys.executable, "pf_trader_journal_j1.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/trader_journal_j1.json",
        "--md", "output/dashboard_surface/trader_journal_j1.md",
    ], core)

    print(
        "TURBO_V73_CYCLE_OK | "
        f"symbols={symbols} | steps={len(results)} | duration_seconds={elapsed} | "
        "layers=data_health,ontology,signal_adaptive,price_schema,topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,b8,phase_synthesis,evidence_bus,evidence_reading,daily_journal"
    )


    return 0


if __name__ == "__main__":
    raise SystemExit(main())

    run_step("daily_journal_all", [
        sys.executable, "run_daily_journal_all_once.py",
        "--db", "powerflow.db",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/daily_journal.json",
    ], core)
    run_step("daily_journal_normalize", [
        sys.executable, "dashboard_normalize_daily_journal.py",
        "--input", "output/dashboard_surface/daily_journal.json",
        "--output", "output/dashboard_surface/daily_journal_dashboard.json",
    ], core)
