from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "Core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from pf_b9_runtime_bridge import sample_runtime_window  # noqa: E402
from test_b9_runtime_1h_dryrun import run_b9_dryrun_1h  # noqa: E402
from activate_telegram_b9_progressive import activate_telegram_progressive  # noqa: E402


class FakeBridge:
    def __init__(self):
        self.count = 0

    def process_tick_window(self, symbol, window_data):
        self.count += 1
        return {"status": "NODE_CREATED", "node": {"symbol": symbol}}


def test_dryrun_short_creates_nodes():
    bridge = FakeBridge()
    nodes, errors = run_b9_dryrun_1h(
        minutes=1,
        poll_seconds=0.1,
        window_provider=lambda: sample_runtime_window(),
        bridge=bridge,
        max_windows=2,
    )
    assert nodes >= 1
    assert errors == []
    assert bridge.count >= 1


def test_activation_script_prints_protocol(capsys):
    activate_telegram_progressive()
    out = capsys.readouterr().out
    assert "Phase 1" in out
    assert "DRY-RUN" in out
    assert "Perception transmise" in out
