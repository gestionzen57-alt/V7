from __future__ import annotations

import ast
from pathlib import Path
import sys
from types import SimpleNamespace


def _core() -> Path:
    return Path(__file__).resolve().parents[1] / "Core"


def test_derive_tick_context_from_bid_ask_objects():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_tick_context

    tick = SimpleNamespace(symbol="GBPUSD", timestamp="2026-05-15T17:30:00Z", bid=1.2500, ask=1.2502)
    prev = SimpleNamespace(symbol="GBPUSD", timestamp="2026-05-15T17:29:00Z", bid=1.2490, ask=1.2492)

    ctx = derive_tick_context(tick, prev)

    assert ctx.symbol == "GBPUSD"
    assert ctx.price == 1.2501
    assert round(ctx.prev_price, 6) == 1.2491
    assert round(ctx.price_delta, 6) == 0.001
    assert round(ctx.spread, 6) == 0.0002


def test_derive_tick_context_from_dict_price_priority():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_tick_context

    tick = {"symbol": "EURUSD", "timestamp": "t1", "price": "1.1000", "bid": 1.0, "ask": 2.0}
    prev = {"symbol": "EURUSD", "timestamp": "t0", "price": "1.0990"}

    ctx = derive_tick_context(tick, prev)

    assert ctx.symbol == "EURUSD"
    assert ctx.price == 1.1
    assert ctx.prev_price == 1.099
    assert round(ctx.price_delta, 6) == 0.001
    assert ctx.spread == 1.0


def test_tick_context_handles_missing_prev_without_crash():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_tick_context

    ctx = derive_tick_context({"symbol": "USDJPY", "bid": 155.10, "ask": 155.12}, None)

    assert ctx.symbol == "USDJPY"
    assert ctx.price == 155.11
    assert ctx.prev_price is None
    assert ctx.price_delta is None


def test_tick_context_to_dict_returns_plain_dict():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_tick_context, tick_context_to_dict

    ctx = derive_tick_context({"symbol": "GBPUSD", "price": 1.25}, {"price": 1.24})
    data = tick_context_to_dict(ctx)

    assert data["symbol"] == "GBPUSD"
    assert data["price_delta"] == 0.010000000000000009


def test_pf_engine_v6_core_has_no_forbidden_runtime_imports():
    core_file = _core() / "pf_engine_v6_core.py"
    text = core_file.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)

    forbidden_roots = {"engine", "capture_bridge", "sqlite3", "telegram_v6"}
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split('.')[0])

    for imported in imports:
        assert imported not in forbidden_roots


def test_pf_engine_v6_core_has_no_runtime_side_effect_tokens_outside_comments():
    core_file = _core() / "pf_engine_v6_core.py"
    lines = core_file.read_text(encoding="utf-8", errors="replace").splitlines()

    code_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        code_lines.append(line)

    code = '\n'.join(code_lines)
    forbidden_tokens = [".execute(", ".commit(", "send_alert(", "dashboard_", "cockpit_"]

    for token in forbidden_tokens:
        assert token not in code

