#!/usr/bin/env python3
"""
PowerFlow V7.2 — Lab TF Profiles V0.3

Adds timeframe profiles and M1 modes on top of Lab Engine V7.2.

Profiles
--------
HTF  = W/D/H4       = 10080,1440,240
MTF  = H1/M30/M15   = 60,30,15
LTF  = M15/M5/M1    = 15,5,1
FULL = all major TFs

M1 modes
--------
off  = remove M1 from main replay
full = include M1 in main replay
zoom = keep M1 out of main replay, then generate small M1 zoom windows around key moments

Doctrine
--------
M1 is not noise by default.
M1 is the microscope.
But the microscope must not replace the battlefield map.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


VERSION = "LabTFProfilesV72.0.3"
METHOD = "lab_v72_tf_profiles_m1_modes"


TF_PROFILES = {
    "HTF": [10080, 1440, 240],
    "MTF": [60, 30, 15],
    "LTF": [15, 5, 1],
    "LTF_NO_M1": [15, 5],
    "FULL": [10080, 1440, 240, 60, 30, 15, 5, 1],
}

TF_LABELS = {
    10080: "W",
    1440: "D",
    240: "H4",
    60: "H1",
    30: "M30",
    15: "M15",
    5: "M5",
    1: "M1",
}


@dataclass
class ProfileLabConfig:
    db_path: Path
    symbol: str
    start_dt: datetime
    end_dt: datetime
    tf_profile: str = "MTF"
    m1_mode: str = "off"  # off|zoom|full
    custom_tfs: Optional[List[int]] = None
    out_root: Path = Path("output")
    outcome_window: int = 30
    hypothesis: str = "all"
    max_m1_zooms: int = 5
    zoom_before_minutes: int = 5
    zoom_after_minutes: int = 10
    selector_min_confidence: float = 0.60
    selector_warmup_index: int = 15


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc)


def format_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def profile_tfs(profile: str, custom_tfs: Optional[Sequence[int]] = None) -> List[int]:
    p = str(profile or "MTF").upper()
    if p == "CUSTOM":
        if not custom_tfs:
            raise ValueError("CUSTOM profile requires custom_tfs")
        return list(dict.fromkeys(int(x) for x in custom_tfs))
    if p not in TF_PROFILES:
        raise ValueError(f"Unknown tf_profile={profile}. Available: {', '.join(sorted(TF_PROFILES))}, CUSTOM")
    return list(TF_PROFILES[p])


def apply_m1_mode(tfs: Sequence[int], m1_mode: str) -> List[int]:
    mode = str(m1_mode or "off").lower()
    base = list(dict.fromkeys(int(x) for x in tfs))
    if mode in {"off", "zoom"}:
        return [tf for tf in base if tf != 1]
    if mode == "full":
        return base
    raise ValueError("m1_mode must be off, zoom, or full")


def tf_labels(tfs: Sequence[int]) -> List[str]:
    return [TF_LABELS.get(int(tf), str(tf)) for tf in tfs]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def try_run_selector(lab_run_dir: Path, min_confidence: float, warmup_index: int) -> Optional[Dict[str, Any]]:
    try:
        from pf_lab_event_selector_v72 import run_selector  # type: ignore
    except Exception as exc:
        return {
            "valid": False,
            "reason": "SELECTOR_NOT_AVAILABLE",
            "error": str(exc),
        }

    try:
        return run_selector(
            lab_run=lab_run_dir,
            warmup_index=warmup_index,
            min_confidence=min_confidence,
            include_every_scene_change=True,
        )
    except Exception as exc:
        return {
            "valid": False,
            "reason": "SELECTOR_FAILED",
            "error": str(exc),
        }


def choose_zoom_events(lab_run_dir: Path, max_zooms: int) -> List[Dict[str, Any]]:
    key_events_path = lab_run_dir / "key_events.json"
    if key_events_path.exists():
        events = load_json(key_events_path)
    else:
        cause_path = lab_run_dir / "cause_consequence.json"
        cause = load_json(cause_path) if cause_path.exists() else {"events": []}
        events = []
        for ev in cause.get("events", []):
            at = ev.get("at_event", {})
            sc = at.get("scene_context", {})
            fp = at.get("structural_footprint", {})
            events.append({
                "t0": ev.get("t0"),
                "index": ev.get("index"),
                "scene_id": ev.get("scene_id") or sc.get("scene_id"),
                "compression": ev.get("compression_qualification"),
                "footprint": fp.get("footprint_state"),
                "outcome": ev.get("observed_outcome", {}).get("outcome"),
                "scene_confidence": sc.get("scene_confidence_non_blocking", 0.0),
            })

    priority_scenes = {
        "FIRST_DETACHMENT_MICRO": 100,
        "PRICE_LAG_CATCH_UP": 95,
        "PULLBACK_ABSORBED": 90,
        "COUNTER_BREATH": 85,
        "SECOND_LEG_BIRTH": 80,
        "ZONE_BREATH_COMPRESSION": 70,
        "LEADER_FOLLOWER_IMBALANCE": 60,
        "REPULSION_CLEAN": 60,
    }

    def score(e: Dict[str, Any]) -> float:
        s = priority_scenes.get(e.get("scene_id"), 20)
        if e.get("compression") == "COMPRESSION_REAL_CANDIDATE":
            s += 30
        if e.get("compression") == "COMPRESSION_FAKE_RISK":
            s += 15
        fp = str(e.get("footprint", ""))
        if "FOOTPRINT_CANDIDATE" in fp:
            s += 25
        outcome = e.get("outcome")
        if outcome in {"REJECTION", "SECOND_LEG_CONFIRMED", "DELAYED_RELEASE"}:
            s += 20
        if outcome == "RELEASE_CONFIRMED":
            s += 10
        try:
            s += float(e.get("scene_confidence") or 0) * 10
        except Exception:
            pass
        return s

    unique: Dict[str, Dict[str, Any]] = {}
    for e in sorted(events, key=score, reverse=True):
        t0 = e.get("t0")
        if not t0 or t0 in unique:
            continue
        unique[t0] = e
        if len(unique) >= max_zooms:
            break

    return list(unique.values())


def write_m1_zoom_film(main_run_dir: Path, zoom_index: List[Dict[str, Any]]) -> None:
    lines = [
        "# PowerFlow V7.2 — M1 Zoom Film",
        "",
        f"**Generated at:** {utc_now()}",
        "",
        "## Doctrine",
        "",
        "M1 est le microscope. Il est isolé autour des moments clés détectés par le film principal.",
        "Le film principal reste sans M1 si `m1_mode=zoom`.",
        "",
    ]

    if not zoom_index:
        lines.append("Aucun zoom M1 généré.")
    else:
        for z in zoom_index:
            lines += [
                f"## Zoom {z.get('rank')} — {z.get('anchor_t0')} — {z.get('scene_id')}",
                "",
                f"- Window: `{z.get('start')}` → `{z.get('end')}`",
                f"- Compression: `{z.get('compression')}`",
                f"- Footprint: `{z.get('footprint')}`",
                f"- Outcome: `{z.get('outcome')}`",
                f"- Run dir: `{z.get('run_dir')}`",
                "",
                "À ouvrir :",
                "",
                f"- `{z.get('run_dir')}\\lab_report.html`",
                f"- `{z.get('run_dir')}\\film_behavioral.md`",
                "",
            ]

    (main_run_dir / "film_m1_zoom.md").write_text("\n".join(lines), encoding="utf-8")


def run_profile_lab(config: ProfileLabConfig) -> Dict[str, Any]:
    from pf_lab_engine_v72 import LabConfig, run_lab  # type: ignore

    raw_tfs = profile_tfs(config.tf_profile, config.custom_tfs)
    main_tfs = apply_m1_mode(raw_tfs, config.m1_mode)

    if not main_tfs:
        raise ValueError("No timeframe left after applying m1_mode.")

    main_config = LabConfig(
        db_path=config.db_path,
        symbol=config.symbol,
        start_dt=config.start_dt,
        end_dt=config.end_dt,
        tfs=main_tfs,
        out_root=config.out_root,
        outcome_window=config.outcome_window,
        hypothesis=config.hypothesis,
    )

    main_result = run_lab(main_config)
    main_run_dir = Path(main_result["out_dir"])

    selector_result = try_run_selector(
        main_run_dir,
        min_confidence=config.selector_min_confidence,
        warmup_index=config.selector_warmup_index,
    )

    zoom_index: List[Dict[str, Any]] = []
    if config.m1_mode.lower() == "zoom":
        zoom_events = choose_zoom_events(main_run_dir, config.max_m1_zooms)
        zoom_root = main_run_dir / "m1_zoom_runs"
        zoom_root.mkdir(parents=True, exist_ok=True)

        for rank, event in enumerate(zoom_events, start=1):
            try:
                anchor = parse_dt(event["t0"])
            except Exception:
                continue

            z_start = anchor - timedelta(minutes=config.zoom_before_minutes)
            z_end = anchor + timedelta(minutes=config.zoom_after_minutes)

            zoom_config = LabConfig(
                db_path=config.db_path,
                symbol=config.symbol,
                start_dt=z_start,
                end_dt=z_end,
                tfs=[15, 5, 1],
                out_root=zoom_root,
                outcome_window=max(10, min(config.outcome_window, 20)),
                hypothesis=config.hypothesis,
            )

            z_result = run_lab(zoom_config)
            z_run_dir = Path(z_result["out_dir"])
            try_run_selector(z_run_dir, min_confidence=config.selector_min_confidence, warmup_index=0)

            zoom_index.append({
                "rank": rank,
                "anchor_t0": event.get("t0"),
                "scene_id": event.get("scene_id"),
                "compression": event.get("compression"),
                "footprint": event.get("footprint"),
                "outcome": event.get("outcome"),
                "start": format_dt(z_start),
                "end": format_dt(z_end),
                "tfs": [15, 5, 1],
                "tf_labels": tf_labels([15, 5, 1]),
                "run_dir": str(z_run_dir),
                "summary": z_result.get("summary", {}),
            })

        write_json(main_run_dir / "m1_zoom_index.json", zoom_index)
        write_m1_zoom_film(main_run_dir, zoom_index)

    summary = {
        "valid": True,
        "method": METHOD,
        "version": VERSION,
        "generated_at": utc_now(),
        "main_run_dir": str(main_run_dir),
        "tf_profile": config.tf_profile.upper(),
        "m1_mode": config.m1_mode.lower(),
        "profile_tfs_raw": raw_tfs,
        "profile_tf_labels_raw": tf_labels(raw_tfs),
        "main_tfs": main_tfs,
        "main_tf_labels": tf_labels(main_tfs),
        "main_result": main_result,
        "selector_result": selector_result,
        "m1_zoom_count": len(zoom_index),
        "m1_zoom_index": zoom_index,
        "files": {
            "main_lab_report_html": str(main_run_dir / "lab_report.html"),
            "main_film_behavioral": str(main_run_dir / "film_behavioral.md"),
            "key_events_html": str(main_run_dir / "lab_report_key_events.html"),
            "key_events_csv": str(main_run_dir / "key_events.csv"),
            "m1_zoom_index": str(main_run_dir / "m1_zoom_index.json") if zoom_index else None,
            "m1_zoom_film": str(main_run_dir / "film_m1_zoom.md") if zoom_index else None,
        },
        "doctrine": {
            "m1_is_microscope": True,
            "no_trade_decision": True,
            "no_filtering": True,
            "db_readonly": True,
        },
    }

    write_json(main_run_dir / "lab_profile_summary.json", summary)
    return summary
