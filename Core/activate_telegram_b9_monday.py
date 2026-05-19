"""PowerFlow B9 Telegram progressive activation helper.

This file does not send Telegram messages. It prints the safe activation sequence.
"""
from __future__ import annotations

import os


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    print("PowerFlow B9 — Activation Telegram progressive")
    print("")
    print("Phase 1 — DRY-RUN runtime")
    print('  cd "C:\\Users\\User\\Desktop\\ProjetPowerFlow\\IA\\GPT\\Core"')
    print("  python test_b9_runtime_10min_dryrun.py")
    print("  Critere: 0 erreur + >= 1 node")
    print("")
    print("Phase 2 — Verifier variables Telegram")
    print("  TELEGRAM_BOT_TOKEN:", "OK" if token else "MISSING")
    print("  TELEGRAM_CHAT_ID:", "OK" if chat_id else "MISSING")
    print("")
    print("Phase 3 — Activer dans la config runtime seulement apres validation")
    print('  "ENABLE_TELEGRAM": True')
    print("")
    print("Regles message:")
    print("  - Aucun BUY/SELL")
    print("  - Aucun conseil decisionnel")
    print('  - Fin stricte: "⚡ Perception transmise — Trader filtre."')
    print("")
    if not token or not chat_id:
        print("[TECHNICAL_RISK] TELEGRAM_ENV_MISSING")
        return 2
    print("[OK] Telegram env present. Activation possible apres DRY-RUN valide.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
