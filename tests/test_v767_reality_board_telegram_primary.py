from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "patch" / "pf_telegram_reality_board_v767.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pf_telegram_reality_board_v767", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_reality_telegram_text_is_trader_french_not_raw_enums():
    mod = load_module()
    state = {
        "symbol": "GBPUSD",
        "qualified_bias": "HIGH_ZONE_EXHAUSTION_RISK",
        "data_visibility": "READING_PARTIAL",
        "session_alignment": "ALIGNED_OR_PARTIAL",
        "b6_nearest_film": "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND",
        "dominant_strategy": {"label_fr": "Priorité lecture rejet haut / unwind."},
        "alternative_strategy": {"label_fr": "Alternative : réintégration propre au-dessus de la zone haute."},
        "trap": {"label_fr": "Confondre extension tardive avec continuation saine."},
        "time_profile_roles": {
            "htf": {"label_fr": "HTF - Analyse", "summary_fr": "HTF_REACTION_ZONE | bias=PAIR_DOWN"},
            "mtf": {"label_fr": "MTF - Plan", "summary_fr": "MTF_REACTION_OR_REJECTION | bias=PAIR_DOWN"},
            "ltf": {"label_fr": "LTF - Action", "summary_fr": "LTF_DIVERGENT_RELEASE | bias=PAIR_UP"},
        },
    }
    text = mod.build_reality_telegram_text(state)
    assert "GBPUSD - Réalité marché" in text
    assert "HTF - Analyse" in text
    assert "MTF - Plan" in text
    assert "LTF - Action" in text
    assert "risque d’épuisement en zone haute" in text
    assert "lecture partielle" in text
    assert "alignement partiel" in text
    assert "high tardif rejeté puis unwind profond" in text
    for raw in mod.RAW_DISPLAY_TERMS:
        assert raw not in text


def test_wrapper_makes_legacy_dryrun_and_reality_primary():
    text = (ROOT / "run_powerflow_v767_reality_telegram_cycle.ps1").read_text(encoding="utf-8", errors="replace")
    assert "Legacy V7.6 Telegram mode: dry-run/debug" in text
    assert "run_powerflow_v76_telegram_cycle.ps1" in text
        assert "$legacyParams" in text
    assert 'TelegramMode = "dry-run"' in text
    assert '$legacyParams["RunCoreScheduler"] = $true' in text
    assert "pf_telegram_reality_board_v767.py" in text


def test_script_dry_run_writes_result_if_reality_board_exists():
    rb = ROOT / "output" / "dashboard_surface" / "GBPUSD" / "reality_board_state.json"
    if not rb.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "patch" / "pf_reality_board_state_once.py"), "--symbol", "GBPUSD"],
            cwd=str(ROOT),
            check=True,
        )
    subprocess.run(
        [sys.executable, str(SCRIPT), "--symbol", "GBPUSD", "--mode", "dry-run"],
        cwd=str(ROOT),
        check=True,
    )
    out = ROOT / "output" / "dashboard_surface" / "GBPUSD" / "v767_reality_telegram_result.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["engine"] == "V767_REALITY_BOARD_TELEGRAM_PRIMARY"
    assert data["mode"] == "dry-run"
    assert "Réalité marché" in data["text_fr"]


def test_stdout_is_utf8_safe_for_windows_console():
    script = SCRIPT.read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_STDOUT_UTF8_SAFE_V2" in script
    assert "sys.stdout.reconfigure" in script


def test_wrapper_uses_hashtable_splatting_not_positional_legacy_args():
    text = (ROOT / "run_powerflow_v767_reality_telegram_cycle.ps1").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_HASHTABLE_SPLAT_FIX_V2" in text
    assert "$legacyParams" in text
    assert "@legacyParams" in text
