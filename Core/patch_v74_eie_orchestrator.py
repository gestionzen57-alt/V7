from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("run_confluence_alert.py")

text = TARGET.read_text(encoding="utf-8", errors="replace")
backup = TARGET.with_suffix(".py.bak_eie_orchestrator_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

# 1) Add args
old = '''    ap.add_argument("--send", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
'''
new = '''    ap.add_argument("--send", action="store_true")
    ap.add_argument("--mark-dry-run", action="store_true")
    ap.add_argument("--min-level", default="ACTIVE")
    ap.add_argument("--interval", type=int, default=300)
'''
if old not in text:
    raise SystemExit("PATCH_FAIL | args insertion point not found")
text = text.replace(old, new, 1)

# 2) Replace single elastic run with full chain
old = '''    rc = run([
        py,
        "pf_confluence_elastic.py",
        "--db",
        args.db,
        "--symbol",
        symbol,
        "--zone-tf",
        str(args.zone_tf),
        "--pretty",
    ])

    out_json = OUT / symbol / "eie_confluence.json"
    out_txt = OUT / symbol / "eie_confluence.txt"
    primary = load_json(out_json)

    missing_outputs = []
    if not out_json.exists():
        missing_outputs.append(str(out_json))
    if not out_txt.exists():
        missing_outputs.append(str(out_txt))

    if missing_outputs:
        rc = 2

    report = {
'''

new = '''    steps = []

    rc_elastic = run([
        py,
        "pf_confluence_elastic.py",
        "--db",
        args.db,
        "--symbol",
        symbol,
        "--zone-tf",
        str(args.zone_tf),
        "--pretty",
    ])
    steps.append({"step": "elastic", "returncode": rc_elastic})

    rc_gravity = run([
        py,
        "pf_confluence_gravity.py",
        "--symbol",
        symbol,
        "--pretty",
    ])
    steps.append({"step": "gravity", "returncode": rc_gravity})

    gate_cmd = [
        py,
        "pf_eie_telegram_gate_once.py",
        "--symbol",
        symbol,
        "--min-level",
        args.min_level,
    ]

    if args.send:
        gate_cmd.append("--send")
    if args.mark_dry_run:
        gate_cmd.append("--mark-dry-run")

    rc_gate = run(gate_cmd)
    steps.append({"step": "telegram_gate", "returncode": rc_gate})

    rc = max(rc_elastic, rc_gravity, rc_gate)

    out_json = OUT / symbol / "eie_confluence.json"
    out_txt = OUT / symbol / "eie_confluence.txt"
    gravity_json = OUT / symbol / "eie_gravity.json"
    gravity_txt = OUT / symbol / "eie_gravity.txt"
    telegram_json = OUT / symbol / "eie_telegram_decision.json"
    telegram_txt = OUT / symbol / "eie_telegram_decision.txt"

    primary = load_json(out_json)
    gravity = load_json(gravity_json)
    telegram = load_json(telegram_json)

    missing_outputs = []
    for p in [out_json, out_txt, gravity_json, gravity_txt, telegram_json, telegram_txt]:
        if not p.exists():
            missing_outputs.append(str(p))

    if missing_outputs:
        rc = 2

    report = {
'''
if old not in text:
    raise SystemExit("PATCH_FAIL | run chain insertion point not found")
text = text.replace(old, new, 1)

# 3) enrich report fields
old = '''        "send_requested": bool(args.send),
        "returncode": rc,
        "missing_outputs": missing_outputs,
        "outputs": {
            "eie_confluence_json": str(OUT / symbol / "eie_confluence.json"),
            "eie_confluence_txt": str(OUT / symbol / "eie_confluence.txt"),
        },
        "primary": primary,
        "note": "Surface-only EIE V7.4. Telegram gate will be added in next step.",
'''
new = '''        "send_requested": bool(args.send),
        "mark_dry_run": bool(args.mark_dry_run),
        "min_level": args.min_level,
        "returncode": rc,
        "steps": steps,
        "missing_outputs": missing_outputs,
        "outputs": {
            "eie_confluence_json": str(out_json),
            "eie_confluence_txt": str(out_txt),
            "eie_gravity_json": str(gravity_json),
            "eie_gravity_txt": str(gravity_txt),
            "eie_telegram_decision_json": str(telegram_json),
            "eie_telegram_decision_txt": str(telegram_txt),
        },
        "primary": primary,
        "gravity": gravity,
        "telegram": telegram,
        "note": "EIE V7.4 orchestrator: elastic -> gravity -> telegram gate.",
'''
if old not in text:
    raise SystemExit("PATCH_FAIL | report replacement point not found")
text = text.replace(old, new, 1)

TARGET.write_text(text, encoding="utf-8")

print("PATCH_OK | run_confluence_alert now orchestrates elastic gravity telegram")
print("backup=", backup.name)
