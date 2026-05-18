from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "b9_telegram_preview_audit_board.py"
spec = importlib.util.spec_from_file_location("audit_tool", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def valid_msg(colon=" : "):
    return "\n".join([
        f"B9 voit{colon}une scène demande attention",
        f"Zone{colon}zone active",
        f"État{colon}lecture à confirmer",
        f"Mémoire proche{colon}mémoire non établie",
        f"Piège technique{colon}source limitée",
        f"À surveiller{colon}réaction de zone",
        f"Limite{colon}lecture informative",
    ])

def test_section_detection_accepts_colon_without_spaces():
    msg = valid_msg(":")
    assert mod.section_missing(msg) == []

def test_ready_no_send_preview(tmp_path):
    root = tmp_path / "preview"; root.mkdir()
    msg = valid_msg(" : ")
    (root / "B9_TELEGRAM_FR_PREVIEW_V0.json").write_text(json.dumps({"version":"B9_TELEGRAM_FR_PREVIEW_V0","telegram_send_enabled":False,"message_candidate":msg}, ensure_ascii=False), encoding="utf-8")
    (root / "B9_TELEGRAM_DRY_RUN_GATE_V0.json").write_text(json.dumps({"version":"B9_TELEGRAM_DRY_RUN_GATE_V0","telegram_send_enabled":False,"send_attempted":False,"dry_run_only":True,"gate_status":"DRY_RUN_PASS","message_candidate":msg}, ensure_ascii=False), encoding="utf-8")
    rows, _ = mod.build_board(root)
    assert rows[0]["audit_status"] == "READY_FOR_HUMAN_REVIEW_NO_SEND"

def test_blocks_forbidden_language(tmp_path):
    root = tmp_path / "preview"; root.mkdir()
    msg = valid_msg(" : ").replace("une scène demande attention", "BUY")
    (root / "B9_TELEGRAM_FR_PREVIEW_V0.json").write_text(json.dumps({"telegram_send_enabled":False,"message_candidate":msg}), encoding="utf-8")
    (root / "B9_TELEGRAM_DRY_RUN_GATE_V0.json").write_text(json.dumps({"telegram_send_enabled":False,"send_attempted":False,"dry_run_only":True,"gate_status":"DRY_RUN_PASS","message_candidate":msg}), encoding="utf-8")
    rows, _ = mod.build_board(root)
    assert rows[0]["audit_status"] == "BLOCKED_FORBIDDEN_LANGUAGE"

def test_cli_nonfatal_by_default_when_blocked(tmp_path):
    root = tmp_path / "preview"; root.mkdir()
    out = tmp_path / "audit"
    msg = "B9 voit : incomplete"
    (root / "B9_TELEGRAM_FR_PREVIEW_V0.json").write_text(json.dumps({"telegram_send_enabled":False,"message_candidate":msg}), encoding="utf-8")
    (root / "B9_TELEGRAM_DRY_RUN_GATE_V0.json").write_text(json.dumps({"telegram_send_enabled":False,"send_attempted":False,"dry_run_only":True,"gate_status":"DRY_RUN_PASS","message_candidate":msg}), encoding="utf-8")
    result = subprocess.run([sys.executable, str(TOOL), "--preview-root", str(root), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0
    assert (out / "B9_TELEGRAM_PREVIEW_AUDIT_BOARD_V0.csv").exists()

def test_cli_strict_exit_blocks_when_requested(tmp_path):
    root = tmp_path / "preview"; root.mkdir()
    out = tmp_path / "audit"
    msg = "B9 voit : incomplete"
    (root / "B9_TELEGRAM_FR_PREVIEW_V0.json").write_text(json.dumps({"telegram_send_enabled":False,"message_candidate":msg}), encoding="utf-8")
    (root / "B9_TELEGRAM_DRY_RUN_GATE_V0.json").write_text(json.dumps({"telegram_send_enabled":False,"send_attempted":False,"dry_run_only":True,"gate_status":"DRY_RUN_PASS","message_candidate":msg}), encoding="utf-8")
    result = subprocess.run([sys.executable, str(TOOL), "--preview-root", str(root), "--output-dir", str(out), "--strict-exit"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 2
