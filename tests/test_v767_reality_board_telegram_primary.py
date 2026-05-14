from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "patch" / "pf_telegram_reality_board_v767.py"
WRAPPER = ROOT / "run_powerflow_v767_reality_telegram_cycle.ps1"


def test_reality_telegram_script_static_contract():
    text = SCRIPT.read_text(encoding="utf-8", errors="replace")
    assert "V767_REALITY_BOARD_TELEGRAM_PRIMARY" in text
    assert "should_alert" in text
    assert "fingerprint" in text


def test_stdout_is_utf8_safe_for_windows_console():
    text = SCRIPT.read_text(encoding="utf-8", errors="replace")
    assert "sys.stdout.reconfigure" in text
    assert 'encoding="utf-8"' in text


def test_wrapper_uses_hashtable_splatting():
    text = WRAPPER.read_text(encoding="utf-8", errors="replace")
    assert "$legacyParams" in text
    assert "@legacyParams" in text
    assert 'TelegramMode = "dry-run"' in text
    assert '$legacyParams["RunCoreScheduler"] = $true' in text


def test_script_dry_run_executes_without_cp1252_crash():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    cp = subprocess.run(
        [sys.executable, str(SCRIPT), "--symbol", "GBPUSD", "--mode", "dry-run"],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    assert cp.returncode == 0, cp.stdout
    assert "V7.6.7 REALITY BOARD TELEGRAM PRIMARY" in cp.stdout
    assert "GBPUSD" in cp.stdout
