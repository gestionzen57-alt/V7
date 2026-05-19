"""Activation Telegram B9 progressive."""
from __future__ import annotations

import os


def activate_telegram_progressive() -> None:
    """Print the progressive activation protocol for B9 Telegram."""
    print("[Phase 1] Validation DRY-RUN 1h")
    print("Run: python test_b9_runtime_1h_dryrun.py")
    print("Expected: 0 errors and at least 1 NODE_CREATED in live market context")

    print("\n[Phase 2] Telegram logs mode")
    print("Set environment variable:")
    print("  $env:B9_ENABLE_TELEGRAM='1'")
    print("Keep TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID configured in environment")
    print("Check that every message ends with:")
    print("  ⚡ Perception transmise — Trader filtre.")

    print("\n[Phase 3] Production LIVE")
    token_present = bool(os.getenv("TELEGRAM_BOT_TOKEN", ""))
    chat_present = bool(os.getenv("TELEGRAM_CHAT_ID", ""))
    print(f"Token present: {token_present}")
    print(f"Chat id present: {chat_present}")
    print("Start live scheduler only after Phase 1 and Phase 2 logs are clean.")


if __name__ == "__main__":
    activate_telegram_progressive()
