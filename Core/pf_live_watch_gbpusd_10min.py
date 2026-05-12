import time, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

SYMBOL = "GBPUSD"
SCRIPT = "pf_packet_live_gate_once.py"
OUT = Path(f"output/dashboard_surface/{SYMBOL}/flow_packet.json")

last_signature = None

print("LIVE_WATCH_START | symbol=", SYMBOL)

for i in range(30):  # 30 cycles x 20 sec = 10 min
    print(f"\n--- cycle {i+1}/30 | {datetime.now(timezone.utc).isoformat()} ---")

    try:
        subprocess.run([sys.executable, SCRIPT], check=False)

        if OUT.exists():
            j = json.loads(OUT.read_text(encoding="utf-8"))
            top = j.get("top_live_packet")
            gate = j.get("live_gate", {})

            if not top:
                print(
                    "STATE=NO_LIVE_PACKET",
                    "| live=", gate.get("live_count"),
                    "| expired=", gate.get("expired_count"),
                )
            else:
                sig = (
                    top.get("packet_type"),
                    top.get("packet_level"),
                    top.get("pair_bias"),
                    top.get("timeframe"),
                    top.get("last_signal_at"),
                )

                print("STATE=LIVE_PACKET")
                print("type=", top.get("packet_type"))
                print("level=", top.get("packet_level"))
                print("bias=", top.get("pair_bias"))
                print("tf=", top.get("timeframe"))
                print("score=", top.get("score"))
                print("age_min=", top.get("age_min"), "/", top.get("max_age_min"))
                print("types=", top.get("types"))

                if sig != last_signature:
                    print("NEW_PACKET_SIGNATURE")
                    last_signature = sig
                else:
                    print("SAME_PACKET_SIGNATURE")

    except Exception as e:
        print("LIVE_WATCH_ERROR", type(e).__name__, e)

    time.sleep(20)

print("\nLIVE_WATCH_END")
