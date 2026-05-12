from pathlib import Path
from datetime import datetime
import re

FILES = [
    "pf_time_profile_window.py",
    "dashboard_normalize_time_profiles.py",
    "run_ltf_profile_once.py",
    "run_mtf_profile_once.py",
    "run_htf_profile_once.py",
    "dashboard_ltf_profile.html",
    "dashboard_mtf_profile.html",
    "dashboard_htf_profile.html",
]

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for f in FILES:
    p = Path(f)
    if p.exists():
        b = Path(f"{f}.bak_broker_time_v737e_{stamp}")
        b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

print("BACKUP_OK | broker time backups written")

# ---------------------------------------------------------------------
# 1) pf_time_profile_window.py
# ---------------------------------------------------------------------
p = Path("pf_time_profile_window.py")
text = p.read_text(encoding="utf-8")

marker = "PF_BROKER_TIME_ALIGNMENT_V737E"

if marker not in text:
    # Ensure imports
    if "from datetime import" in text:
        text = re.sub(
            r"from datetime import ([^\n]+)",
            lambda m: m.group(0) if "timedelta" in m.group(1) else m.group(0) + ", timedelta",
            text,
            count=1,
        )
    else:
        text = "from datetime import datetime, timezone, timedelta\n" + text

    helper = r'''

# PF_BROKER_TIME_ALIGNMENT_V737E
def _pf_parse_iso_utc(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _pf_time_projection(value, broker_offset_hours=1):
    """
    DB candles are broker-clock stamped. Broker is H+1 vs local reference.
    Keep raw timestamp untouched and add a projected local-reference timestamp.
    """
    dt = _pf_parse_iso_utc(value)
    if dt is None:
        return {
            "timestamp_broker": value,
            "timestamp_local_reference": None,
            "broker_offset_hours": broker_offset_hours,
            "freshness_seconds_local": None,
        }

    local_dt = dt - timedelta(hours=float(broker_offset_hours))
    now_utc = datetime.now(timezone.utc)
    freshness_local = (now_utc - local_dt).total_seconds()

    return {
        "timestamp_broker": dt.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "timestamp_local_reference": local_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "broker_offset_hours": broker_offset_hours,
        "freshness_seconds_local": round(freshness_local, 1),
    }
'''

    # Insert helper after imports block.
    insert_pos = 0
    lines = text.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_pos = i + 1
    lines.insert(insert_pos, helper + "\n")
    text = "".join(lines)

    # Add argparse arg after parser creation if possible.
    text = re.sub(
        r"(parser\s*=\s*argparse\.ArgumentParser\([^\n]*\)\s*)",
        r"\1\n    parser.add_argument('--broker-offset-hours', type=float, default=1.0, help='Broker clock offset vs local reference. Broker H+1 => 1.')",
        text,
        count=1,
    )

    # If args exists and no variable, add variable after parse_args.
    text = re.sub(
        r"(args\s*=\s*parser\.parse_args\([^\n]*\)\s*)",
        r"\1\n    broker_offset_hours = getattr(args, 'broker_offset_hours', 1.0)",
        text,
        count=1,
    )

    # Inject projection in timeframe dicts after last_timestamp_utc field.
    text = re.sub(
        r'("last_timestamp_utc"\s*:\s*([^,\n]+),)',
        r'\1\n            "time_projection": _pf_time_projection(\2, broker_offset_hours),',
        text,
    )

p.write_text(text, encoding="utf-8")
print("PATCH_OK | pf_time_profile_window.py broker projection")


# ---------------------------------------------------------------------
# 2) run_* profile wrappers: add --broker-offset-hours 1
# ---------------------------------------------------------------------
for f in ["run_ltf_profile_once.py", "run_mtf_profile_once.py", "run_htf_profile_once.py"]:
    p = Path(f)
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    if "PF_BROKER_TIME_ALIGNMENT_V737E" not in text:
        text = "# PF_BROKER_TIME_ALIGNMENT_V737E\n" + text

        # Add wrapper parser argument if parser exists.
        text = re.sub(
            r"(parser\s*=\s*argparse\.ArgumentParser\([^\n]*\)\s*)",
            r"\1\n    parser.add_argument('--broker-offset-hours', type=float, default=1.0)",
            text,
            count=1,
        )

        # Insert command args before --output where pf_time_profile_window.py is called.
        text = text.replace(
            '"--output",',
            '"--broker-offset-hours", str(getattr(args, "broker_offset_hours", 1.0)),\n        "--output",',
            1,
        )

    p.write_text(text, encoding="utf-8")
    print(f"PATCH_OK | {f} broker-offset pass-through")


# ---------------------------------------------------------------------
# 3) dashboard_normalize_time_profiles.py: expose compact time projection
# ---------------------------------------------------------------------
p = Path("dashboard_normalize_time_profiles.py")
text = p.read_text(encoding="utf-8")

if "PF_BROKER_TIME_ALIGNMENT_V737E" not in text:
    text = "# PF_BROKER_TIME_ALIGNMENT_V737E\n" + text

    # Add a small helper.
    helper = r'''

def _pf_compact_tf_time(tf_data):
    proj = {}
    if isinstance(tf_data, dict):
        proj = tf_data.get("time_projection") or {}
    return {
        "broker": proj.get("timestamp_broker") or tf_data.get("last_timestamp_utc") if isinstance(tf_data, dict) else None,
        "local_reference": proj.get("timestamp_local_reference"),
        "broker_offset_hours": proj.get("broker_offset_hours"),
        "freshness_seconds_local": proj.get("freshness_seconds_local"),
    }
'''
    insert_pos = 0
    lines = text.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_pos = i + 1
    lines.insert(insert_pos, helper + "\n")
    text = "".join(lines)

    # Add time_view to normalized timeframe dict if possible.
    text = re.sub(
        r'("important_event"\s*:\s*tf\.get\("important_event"\),)',
        r'\1\n                "time_view": _pf_compact_tf_time(tf),',
        text,
    )

p.write_text(text, encoding="utf-8")
print("PATCH_OK | dashboard_normalize_time_profiles.py time_view")


# ---------------------------------------------------------------------
# 4) HTML dashboards: display broker/local if present.
# ---------------------------------------------------------------------
for f in ["dashboard_ltf_profile.html", "dashboard_mtf_profile.html", "dashboard_htf_profile.html"]:
    p = Path(f)
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")

    if "PF_BROKER_TIME_ALIGNMENT_V737E" not in text:
        text = "<!-- PF_BROKER_TIME_ALIGNMENT_V737E -->\n" + text

        # Add JS helper after first <script> if exists.
        helper_js = r'''
function pfTimeView(tf) {
  const tv = tf.time_view || {};
  const broker = tv.broker || tf.last_timestamp_utc || 'n/a';
  const local = tv.local_reference || 'n/a';
  const off = tv.broker_offset_hours ?? 'n/a';
  return `<div class="muted">Broker: ${broker}</div><div class="muted">Local ref: ${local} | offset H+${off}</div>`;
}
'''
        text = text.replace("<script>", "<script>\n" + helper_js, 1)

        # If last_timestamp_utc displayed directly, append projection.
        text = text.replace(
            "${tf.last_timestamp_utc || 'n/a'}",
            "${tf.last_timestamp_utc || 'n/a'}",
        )

        # Add a generic injection near freshness or timestamp blocks.
        text = text.replace(
            "${tf.important_event || 'NONE'}",
            "${tf.important_event || 'NONE'} ${pfTimeView(tf)}",
        )

    p.write_text(text, encoding="utf-8")
    print(f"PATCH_OK | {f} broker/local display")

print("PATCH_DONE | V7.3.7e broker time alignment")
