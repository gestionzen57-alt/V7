from pathlib import Path
from datetime import datetime

path = Path("pf_time_profile_window.py")
text = path.read_text(encoding="utf-8")

backup = Path(f"pf_time_profile_window.py.bak_state_grammar_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

old_ltf = '''    if profile == "LTF":
        main = "LTF_QUIET"
        m1 = tf_states.get("M1", {})
        m5 = tf_states.get("M5", {})
        m15 = tf_states.get("M15", {})
        if "IGNITION" in str(m1.get("phase")) and str(m5.get("bias")) == str(m1.get("bias")):
            main = "M1_IGNITION_WITH_M5_RELAY"
        elif "IGNITION" in str(m1.get("phase")):
            main = "M1_IGNITION_RELAY_WAIT"
        elif "COMPRESSION" in " ".join(phases):
            main = "LTF_COMPRESSION_BUILDING"
        elif "FAKEOUT" in " ".join(phases):
            main = "LTF_FAKEOUT_RISK"
        elif str(m15.get("phase")) in ("STRUCTURE_SHIFT", "ABSORPTION_OR_REJECTION"):
            main = "M15_BATTLE_WINDOW"
'''

new_ltf = '''    if profile == "LTF":
        main = "LTF_QUIET"
        m1 = tf_states.get("M1", {})
        m5 = tf_states.get("M5", {})
        m15 = tf_states.get("M15", {})
        release_count = sum(1 for p in phases if "RELEASE" in p)
        active_biases = [b for b in biases if b in ("PAIR_UP", "PAIR_DOWN")]
        divergent_release = release_count >= 2 and len(set(active_biases)) > 1

        if divergent_release:
            main = "LTF_DIVERGENT_RELEASE"
        elif release_count >= 2:
            main = "LTF_RELEASE_ACTIVE"
        elif release_count == 1:
            main = "LTF_PARTIAL_RELEASE"
        elif "IGNITION" in str(m1.get("phase")) and str(m5.get("bias")) == str(m1.get("bias")):
            main = "M1_IGNITION_WITH_M5_RELAY"
        elif "IGNITION" in str(m1.get("phase")):
            main = "M1_IGNITION_RELAY_WAIT"
        elif "COMPRESSION" in " ".join(phases):
            main = "LTF_COMPRESSION_BUILDING"
        elif "FAKEOUT" in " ".join(phases):
            main = "LTF_FAKEOUT_RISK"
        elif str(m15.get("phase")) in ("STRUCTURE_SHIFT", "ABSORPTION_OR_REJECTION"):
            main = "M15_BATTLE_WINDOW"
'''

old_mtf = '''    elif profile == "MTF":
        main = "MTF_QUIET"
        if "COMPRESSION" in " ".join(phases):
            main = "MTF_INTRADAY_COMPRESSION"
        if "STRUCTURE_SHIFT" in " ".join(phases):
            main = "MTF_STRUCTURE_SHIFT"
        if "ABSORPTION_OR_REJECTION" in " ".join(phases):
            main = "MTF_REACTION_OR_REJECTION"
'''

new_mtf = '''    elif profile == "MTF":
        main = "MTF_QUIET"
        release_count = sum(1 for p in phases if "RELEASE" in p)
        if release_count >= 2:
            main = "MTF_RELEASE_ACTIVE"
        elif release_count == 1:
            main = "MTF_PARTIAL_RELEASE"
        if "COMPRESSION" in " ".join(phases):
            main = "MTF_INTRADAY_COMPRESSION"
        if "STRUCTURE_SHIFT" in " ".join(phases):
            main = "MTF_STRUCTURE_SHIFT"
        if "ABSORPTION_OR_REJECTION" in " ".join(phases):
            main = "MTF_REACTION_OR_REJECTION"
'''

old_htf = '''    else:
        main = "HTF_QUIET"
        if "COMPRESSION" in " ".join(phases):
            main = "HTF_COMPRESSION_OR_INSIDE_RANGE"
        if "STRUCTURE_SHIFT" in " ".join(phases):
            main = "HTF_STRUCTURE_SHIFT"
        if "ABSORPTION_OR_REJECTION" in " ".join(phases):
            main = "HTF_REACTION_ZONE"
'''

new_htf = '''    else:
        main = "HTF_QUIET"
        release_count = sum(1 for p in phases if "RELEASE" in p)
        if release_count >= 2:
            main = "HTF_RELEASE_ACTIVE"
        elif release_count == 1:
            main = "HTF_PARTIAL_RELEASE"
        if "COMPRESSION" in " ".join(phases):
            main = "HTF_COMPRESSION_OR_INSIDE_RANGE"
        if "STRUCTURE_SHIFT" in " ".join(phases):
            main = "HTF_STRUCTURE_SHIFT"
        if "ABSORPTION_OR_REJECTION" in " ".join(phases):
            main = "HTF_REACTION_ZONE"
'''

for old, new, label in [
    (old_ltf, new_ltf, "LTF"),
    (old_mtf, new_mtf, "MTF"),
    (old_htf, new_htf, "HTF"),
]:
    if old not in text:
        raise SystemExit(f"PATCH_FAIL missing block {label}")
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | state grammar fixed | backup={backup}")
