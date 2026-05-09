# RUN_POWERFLOW_RUNTIME_VALIDATION_KINEMATICS_GRAVITY.ps1
# PowerFlow V6 — Runtime validation Kinematics / Energy / Relational Gravity
# Safe mode: read-only DB commands. No patch, no DB write, no Telegram, no dashboard.

param(
    [string]$Db = "powerflow.db",
    [string]$Symbol = "GBPUSD",
    [int]$RecentMinutes = 180,
    [string]$Timeframes = "1,5,15,30,60",
    [string]$Start = "2026-05-06T08:00:00",
    [string]$End = "2026-05-06T13:30:00"
)

$ErrorActionPreference = "Continue"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path "output" "runtime_validation_kinematics_gravity_$stamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$log = Join-Path $outDir "runtime_validation_console.log"
$summary = Join-Path $outDir "runtime_validation_summary.json"

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host "================================================================================"
    Write-Host $Text
    Write-Host "================================================================================"
    Add-Content -Path $log -Value ""
    Add-Content -Path $log -Value "================================================================================"
    Add-Content -Path $log -Value $Text
    Add-Content -Path $log -Value "================================================================================"
}

function Run-Cmd {
    param([string]$Cmd)
    Write-Host "PS> $Cmd"
    Add-Content -Path $log -Value "PS> $Cmd"
    cmd /c $Cmd 2>&1 | Tee-Object -FilePath $log -Append
}

Write-Step "0. Environment"
Run-Cmd "python --version"
Run-Cmd "git status --short --branch"

Write-Step "1. Kinematics runtime / Temporal Node"
$temporalOut = Join-Path $outDir "temporal_node_state.json"
Run-Cmd "python .\run_temporal_node_state_once.py --db $Db --symbol $Symbol --recent-minutes $RecentMinutes --timeframes $Timeframes --visual-htf-story confirmed --out $temporalOut --pretty"

Write-Step "1b. Temporal Node controls"
Run-Cmd "powershell -NoProfile -Command ""Select-String -Path '$temporalOut' -Pattern 'kinematics_state','first_detachment','release_state','energy_release_alignment','capture_quality','relay_quality'"""

Write-Step "2. Currency Energy TF1 / TF5 / TF15"
$energyM1 = Join-Path $outDir "currency_energy_state_m1.json"
$energyM5 = Join-Path $outDir "currency_energy_state_m5.json"
$energyM15 = Join-Path $outDir "currency_energy_state_m15.json"
Run-Cmd "python .\run_currency_energy_probe_once.py --db $Db --symbol $Symbol --timeframe 1 --bars 50 --htf 5,15,30 --out $energyM1 --pretty --summary"
Run-Cmd "python .\run_currency_energy_probe_once.py --db $Db --symbol $Symbol --timeframe 5 --bars 50 --htf 15,30,60 --out $energyM5 --pretty --summary"
Run-Cmd "python .\run_currency_energy_probe_once.py --db $Db --symbol $Symbol --timeframe 15 --bars 50 --htf 15,30,60 --out $energyM15 --pretty --summary"

Write-Step "3. Relational Gravity standalone M1 / M5 / M15"
$rgM1 = Join-Path $outDir "relational_gravity_m1_v011.json"
$rgM5 = Join-Path $outDir "relational_gravity_m5_v011.json"
$rgM15 = Join-Path $outDir "relational_gravity_m15_v011.json"
Run-Cmd "python .\run_relational_gravity_probe_once.py --db $Db --symbol $Symbol --timeframe 1 --bars 30 --out $rgM1 --pretty --summary"
Run-Cmd "python .\run_relational_gravity_probe_once.py --db $Db --symbol $Symbol --timeframe 5 --bars 30 --out $rgM5 --pretty --summary"
Run-Cmd "python .\run_relational_gravity_probe_once.py --db $Db --symbol $Symbol --timeframe 15 --bars 30 --out $rgM15 --pretty --summary"

Write-Step "4. Cockpit Bridge Relational Gravity"
$cockpitOut = Join-Path $outDir "cockpit_agentic_state_v01.json"
Run-Cmd "python .\run_cockpit_agentic_state_once.py --db $Db --symbol $Symbol --start $Start --end $End --visual-htf-story confirmed --behavioral-queue output\behavioral_alert_queue.json --out $cockpitOut --pretty"

Write-Step "4b. Cockpit Bridge controls"
Run-Cmd "powershell -NoProfile -Command ""Select-String -Path '$cockpitOut' -Pattern 'relational_gravity','RELATIONAL_GRAVITY','dominant_leader','cross_tf_state'"""

Write-Step "5. Extract runtime summary"

$py = @'
import json
import pathlib
import sys

out_dir = pathlib.Path(sys.argv[1])
summary_path = pathlib.Path(sys.argv[2])

def load_json(name):
    path = out_dir / name
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        return {"_load_error": f"{type(exc).__name__}:{exc}", "_path": str(path)}

def energy_cur(state, cur):
    data = (state.get("currencies") or {}).get(cur, {}) or {}
    raw = data.get("raw_signed") or {}
    return {
        "score": data.get("energy_score"),
        "label": data.get("energy_label"),
        "absorption": data.get("absorption_escape_state"),
        "speed_per_min": raw.get("speed_per_min"),
        "angle_deg": raw.get("angle_deg"),
        "z_current": raw.get("z_current"),
        "zone_state": raw.get("zone_state"),
        "role": raw.get("role"),
    }

def rg_light(state):
    return {
        "status": state.get("status"),
        "primary_state": state.get("primary_state") or state.get("state"),
        "group": state.get("group") or state.get("primary_group"),
        "direction": state.get("direction"),
        "leader": state.get("leader") or state.get("dominant_leader"),
        "antagonist": state.get("antagonist") or state.get("dominant_antagonist"),
        "score": state.get("score"),
        "confidence": state.get("confidence"),
        "gap_mode": state.get("gap_mode"),
        "group_purified": state.get("group_purified"),
        "ghost_currencies": state.get("ghost_currencies"),
        "lab_signatures": state.get("lab_signatures"),
        "_load_error": state.get("_load_error"),
    }

temporal = load_json("temporal_node_state.json")
em1 = load_json("currency_energy_state_m1.json")
em5 = load_json("currency_energy_state_m5.json")
em15 = load_json("currency_energy_state_m15.json")
rg1 = load_json("relational_gravity_m1_v011.json")
rg5 = load_json("relational_gravity_m5_v011.json")
rg15 = load_json("relational_gravity_m15_v011.json")
cockpit = load_json("cockpit_agentic_state_v01.json")

kin = temporal.get("kinematics_state") or {}
release = kin.get("release_candidate") or {}
bridge = cockpit.get("relational_gravity") or {}

dominant_leader = bridge.get("dominant_leader")
dominant_antagonist = bridge.get("dominant_antagonist")
if isinstance(dominant_antagonist, list):
    leader_in_antagonist = dominant_leader in dominant_antagonist
else:
    leader_in_antagonist = bool(dominant_leader and dominant_leader == dominant_antagonist)

cross_tf_state = bridge.get("cross_tf_state")
topline_reliable = bridge.get("topline_reliable")

p12_needed = bool(
    cross_tf_state == "RELATIONAL_GRAVITY_MIXED"
    and (
        dominant_leader not in (None, "", "MIXED")
        or leader_in_antagonist
        or topline_reliable is not False
    )
)

summary = {
    "runtime_dir": str(out_dir),
    "global_verdict_preliminary": {
        "kinematics_runtime_present": bool(kin),
        "currency_energy_m1_loaded": "_load_error" not in em1,
        "currency_energy_m5_loaded": "_load_error" not in em5,
        "currency_energy_m15_loaded": "_load_error" not in em15,
        "relational_gravity_m1_loaded": "_load_error" not in rg1,
        "relational_gravity_m5_loaded": "_load_error" not in rg5,
        "relational_gravity_m15_loaded": "_load_error" not in rg15,
        "relational_gravity_bridge_present": bool(bridge),
        "p12_bridge_guard_needed": p12_needed,
        "p2_behavioral_mapper_authorized": bool(bridge) and not p12_needed,
    },
    "kinematics_runtime": {
        "capture_quality": temporal.get("capture_quality"),
        "telegram_gating": temporal.get("telegram_gating"),
        "node_summary": temporal.get("node_summary"),
        "first_detachment": kin.get("first_detachment"),
        "release_candidate": release,
        "energy_release_alignment": temporal.get("energy_release_alignment"),
        "energy_context": temporal.get("energy_context"),
    },
    "currency_energy": {
        "M1": {
            "top_energy": em1.get("top_energy"),
            "summary": em1.get("energy_field_summary"),
            "GBP": energy_cur(em1, "GBP"),
            "USD": energy_cur(em1, "USD"),
        },
        "M5": {
            "top_energy": em5.get("top_energy"),
            "summary": em5.get("energy_field_summary"),
            "GBP": energy_cur(em5, "GBP"),
            "USD": energy_cur(em5, "USD"),
        },
        "M15": {
            "top_energy": em15.get("top_energy"),
            "summary": em15.get("energy_field_summary"),
            "GBP": energy_cur(em15, "GBP"),
            "USD": energy_cur(em15, "USD"),
        },
    },
    "relational_gravity_standalone": {
        "M1": rg_light(rg1),
        "M5": rg_light(rg5),
        "M15": rg_light(rg15),
    },
    "relational_gravity_bridge": bridge,
    "bridge_guard_checks": {
        "cross_tf_state": cross_tf_state,
        "dominant_leader": dominant_leader,
        "dominant_antagonist": dominant_antagonist,
        "leader_in_antagonist": leader_in_antagonist,
        "direction_consistency": bridge.get("direction_consistency"),
        "leader_consistency": bridge.get("leader_consistency"),
        "antagonist_consistency": bridge.get("antagonist_consistency"),
        "topline_reliable": topline_reliable,
    },
}

with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(json.dumps(summary, ensure_ascii=False, indent=2))
'@

$extractor = Join-Path $outDir "extract_runtime_summary.py"
Set-Content -Path $extractor -Value $py -Encoding UTF8
Run-Cmd "python $extractor $outDir $summary"

Write-Step "DONE"
Write-Host ""
Write-Host "Runtime folder:"
Write-Host $outDir
Write-Host ""
Write-Host "Summary:"
Write-Host $summary
Write-Host ""
Write-Host "Send this to GPT:"
Write-Host "Get-Content $summary -Raw"
