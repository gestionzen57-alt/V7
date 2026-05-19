# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

import pytest


CORE = Path(__file__).resolve().parents[1] / "Core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from telegram_alert_sender_b9 import FINAL_LINE, VERDICT_EMOJI, format_b9_alert, send_b9_alert


def base_node(verdict="PULLBACK_ABSORBED"):
    return {
        "symbol": "GBPUSD",
        "node_role_fr": "Pullback absorbé sur zone basse",
        "zone_low": 1.3350,
        "zone_high": 1.3374,
        "price_verdict": {"verdict": verdict, "confidence": 0.82},
        "data_visibility": "TACTICAL_OK",
    }


def base_requalified():
    return {
        "requalified_event": "RELEASE_UP_PULLBACK_ABSORBED",
        "requalified_event_fr": "Release UP — pullback absorbé",
        "source_stack": "RAW_TICK_PLUS_FORCE_CONTEXT",
    }


@pytest.mark.parametrize(
    "verdict,emoji",
    [
        ("REJECTED", "🔴"),
        ("FAILED_REINTEGRATION", "🟥"),
        ("PULLBACK_ABSORBED", "🟢"),
        ("ACCEPTED", "🟢"),
        ("CENTER_MIGRATION", "🔵"),
        ("EFFORT_WITHOUT_RESULT", "🟡"),
        ("INCONCLUSIVE", "⚪"),
    ],
)
def test_format_message_uses_verdict_emoji(verdict, emoji):
    message = format_b9_alert(base_node(verdict), base_requalified())
    assert message.startswith(f"{emoji} GBPUSD")
    assert f"Verdict : {verdict}" in message


def test_message_ends_with_doctrinal_final_line():
    message = format_b9_alert(base_node(), base_requalified())
    assert message.endswith(FINAL_LINE)
    assert message.splitlines()[-1] == FINAL_LINE


def test_no_forbidden_nanny_words_in_message():
    message = format_b9_alert(base_node(), base_requalified()).lower()
    for forbidden in ("conseil", "risque", "attendre", "considérez"):
        assert forbidden not in message


def test_dry_run_when_telegram_disabled(capsys):
    result = send_b9_alert(base_node(), base_requalified(), {"ENABLE_TELEGRAM": False})
    captured = capsys.readouterr().out
    assert result["sent"] is False
    assert result["dry_run"] is True
    assert "[DRY-RUN B9 TELEGRAM]" in captured
    assert FINAL_LINE in captured


def test_width_pips_is_computed_correctly():
    message = format_b9_alert(base_node(), base_requalified())
    assert "(24.0 pips)" in message


def test_node_role_fr_is_used_not_english_role():
    node = base_node()
    node["node_role"] = "ENGLISH_INTERNAL_ROLE"
    message = format_b9_alert(node, base_requalified())
    first_line = message.splitlines()[0]
    assert "Pullback absorbé sur zone basse" in first_line
    assert "ENGLISH_INTERNAL_ROLE" not in message


def test_unknown_verdict_defaults_to_white_emoji():
    message = format_b9_alert(base_node("UNKNOWN_VERDICT"), base_requalified())
    assert message.startswith("⚪ GBPUSD")


def test_missing_telegram_config_falls_back_to_dry_run(capsys):
    result = send_b9_alert(base_node(), base_requalified(), {"ENABLE_TELEGRAM": True})
    captured = capsys.readouterr().out
    assert result["sent"] is False
    assert result["dry_run"] is True
    assert "MISSING CONFIG" in captured


def test_send_enabled_posts_to_telegram(monkeypatch):
    calls = []

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

    class RequestsStub:
        @staticmethod
        def post(url, data, timeout):
            calls.append({"url": url, "data": data, "timeout": timeout})
            return Response()

    monkeypatch.setitem(sys.modules, "requests", RequestsStub)
    result = send_b9_alert(
        base_node(),
        base_requalified(),
        {"ENABLE_TELEGRAM": True, "TELEGRAM_BOT_TOKEN": "TOKEN", "TELEGRAM_CHAT_ID": "CHAT"},
    )
    assert result["sent"] is True
    assert calls[0]["url"] == "https://api.telegram.org/botTOKEN/sendMessage"
    assert calls[0]["data"]["chat_id"] == "CHAT"
    assert calls[0]["data"]["text"].endswith(FINAL_LINE)


def test_requalified_event_fr_is_displayed():
    message = format_b9_alert(base_node(), base_requalified())
    assert "Requalifié : Release UP — pullback absorbé" in message


def test_visibility_and_source_are_displayed():
    message = format_b9_alert(base_node(), base_requalified())
    assert "Visibility : TACTICAL_OK" in message
    assert "Source : RAW_TICK_PLUS_FORCE_CONTEXT" in message


def test_verdict_registry_contains_required_values():
    assert VERDICT_EMOJI["REJECTED"] == "🔴"
    assert VERDICT_EMOJI["FAILED_REINTEGRATION"] == "🟥"
    assert VERDICT_EMOJI["EFFORT_WITHOUT_RESULT"] == "🟡"
