from __future__ import annotations
import json, subprocess, sys, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "b9_telegram_fr_preview_dry_run_gate.py"
spec = importlib.util.spec_from_file_location("telegram_preview_tool", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_forbidden_language_detects_interdits():
    assert mod.forbidden_hits("B9 voit : BUY maintenant. signal gagnant.")

def test_preview_contains_required_sections_without_send():
    candidate = {"telegram_fr":"une absorption locale probable","zone":"zone basse active","b6_memory_candidate_state":"B6_REVIEW_CANDIDATE","near_memory_fr":"film proche","t0112_reason_flags":"RAW_NUANCED_PROXY","watch_fr":"retest et acceptation","technical_limits":"source proxy"}
    preview = mod.derive_preview(candidate, {}, {}, {}, {})
    for section in mod.REQUIRED_SECTIONS:
        assert f"{section} :" in preview["message_candidate"]
    assert preview["telegram_send_enabled"] is False

def test_gate_blocks_forbidden_language():
    preview = {"message_candidate": "\n".join(["B9 voit : achat","Zone : z","État : e","Mémoire proche : m","Piège technique : p","À surveiller : a","Limite : l"])}
    gate = mod.build_gate(preview, {})
    assert gate["gate_status"] == "DRY_RUN_BLOCKED"
    assert gate["telegram_send_enabled"] is False
    assert gate["send_attempted"] is False

def test_cli_writes_preview_and_gate(tmp_path):
    gate_candidate = tmp_path / "gate.json"
    reality = tmp_path / "reality.json"
    attention = tmp_path / "attention.json"
    display = tmp_path / "display.json"
    out = tmp_path / "out"
    gate_candidate.write_text(json.dumps({"telegram_candidates":[{"telegram_fr":"une poussée locale reste sous contrôle source","zone":"zone test","b6_memory_candidate_state":"B6_KEEP_CANDIDATE","proxy_vs_raw_verdict":"CONFIRMED_BY_RAW","raw_texture_role":"RAW_PROGRESS_CONFIRMED","watch_fr":"réaction prix et retest","technical_limits":"lecture informative"}]}, ensure_ascii=False), encoding="utf-8")
    reality.write_text("{}", encoding="utf-8")
    attention.write_text("{}", encoding="utf-8")
    display.write_text("{}", encoding="utf-8")
    result = subprocess.run([sys.executable, str(TOOL), "--gate-candidate", str(gate_candidate), "--reality-board", str(reality), "--attention-packet", str(attention), "--display-contract", str(display), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    gate = json.loads((out / "B9_TELEGRAM_DRY_RUN_GATE_V0.json").read_text(encoding="utf-8"))
    assert gate["gate_status"] == "DRY_RUN_PASS"
    assert gate["dry_run_only"] is True

def test_no_telegram_import_or_send_language_in_tool():
    text = TOOL.read_text(encoding="utf-8").lower()
    assert "import telegram" not in text
    assert "bot.send" not in text
    assert "send_message" not in text
