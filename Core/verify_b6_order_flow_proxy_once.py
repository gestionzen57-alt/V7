#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path


MISSION = Path("output/missions/B6_ORDER_FLOW_PROXY_LITE")
SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def db_health():
    db = Path("powerflow.db")
    out = {"exists": db.exists(), "path": str(db.resolve()) if db.exists() else None}
    if not db.exists():
        return out
    con = sqlite3.connect(db)
    cur = con.cursor()
    tables = {}
    for t in ["force_snapshots_v2", "force_snapshots", "signals"]:
        try:
            n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            tables[t] = {"exists": True, "rows": n}
        except Exception as e:
            tables[t] = {"exists": False, "error": str(e)}
    out["tables"] = tables

    coverage = {}
    for s in SYMBOLS:
        coverage[s] = {}
        for tf in [1,5,15,30,60,240]:
            try:
                n, latest = cur.execute("""
                    SELECT COUNT(*), MAX(created_at)
                    FROM force_snapshots_v2
                    WHERE symbol=? AND timeframe=?
                """, (s, tf)).fetchone()
                coverage[s][str(tf)] = {"rows": n, "latest": latest}
            except Exception as e:
                coverage[s][str(tf)] = {"error": str(e)}
    con.close()
    out["coverage_force_snapshots_v2"] = coverage
    return out


def main() -> int:
    MISSION.mkdir(parents=True, exist_ok=True)

    aggregate = read_json(Path("output/dashboard_surface/microstructure_states.json")) or {}
    per_symbol = {}
    for s in SYMBOLS:
        per_symbol[s] = read_json(Path("output/dashboard_surface") / s / "microstructure_state.json")

    report = {
        "created_at": utc_now(),
        "mission": "B6_ORDER_FLOW_PROXY_LITE",
        "status": "EXECUTED",
        "db_health": db_health(),
        "aggregate": aggregate,
        "per_symbol": per_symbol,
        "files_written": [
            "pf_order_flow_proxy_lite.py",
            "run_order_flow_proxy_once.py",
            "run_order_flow_proxy_all_once.py",
            "verify_b6_order_flow_proxy_once.py",
            "output/dashboard_surface/<SYMBOL>/microstructure_state.json",
            "output/dashboard_surface/<SYMBOL>/microstructure_state.txt",
            "output/dashboard_surface/microstructure_states.json",
        ],
        "technical_risks": [
            "B6_LITE_IS_PROXY_NOT_TRUE_ORDER_FLOW",
            "NEEDS_CAPTURE_BRIDGE_EXTENSION_FOR_TRUE_TICK_IMBALANCE",
            "M1_OHLC_PROXY_CAN_OVERSTATE_ABSORPTION_OR_TENSION",
        ],
    }

    (MISSION / "B6_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Mission B6 — Order Flow Proxy Lite")
    lines.append("")
    lines.append(f"- Created: `{report['created_at']}`")
    lines.append("- Mode: `READ_ONLY_DB_PROXY`")
    lines.append("- Objectif: produire une première couche B6 exploitable sans attendre Level 2 / bid_volume natif.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("`B6_LITE_EXECUTED`")
    lines.append("")
    lines.append("## Ce que fait B6 Lite")
    lines.append("")
    lines.append("- Lit `force_snapshots_v2` en priorité.")
    lines.append("- Utilise OHLC M1 comme proxy de pression microstructure.")
    lines.append("- Calcule `proxy_delta`, absorption, imbalance ratio, tension score.")
    lines.append("- Écrit `microstructure_state.json` par symbole.")
    lines.append("- Ne modifie pas la DB.")
    lines.append("")
    lines.append("## Résultats par symbole")
    lines.append("")
    lines.append("| Symbol | State | Tension | Delta | Absorption | Alerts |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in (aggregate.get("reports") or []):
        lines.append(
            f"| {r.get('symbol')} | {r.get('state')} | {r.get('tension_score')} | "
            f"{r.get('delta_cumulative')} | {r.get('absorption_rate')} | {r.get('alerts')} |"
        )
    lines.append("")
    lines.append("## Fichiers créés")
    lines.append("")
    for f in report["files_written"]:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("## Risques techniques")
    lines.append("")
    for r in report["technical_risks"]:
        lines.append(f"- `{r}`")
    lines.append("")
    lines.append("## Suite logique")
    lines.append("")
    lines.append("1. Injecter `microstructure_state.json` dans `pf_powerflow_live_brief_once.py`.")
    lines.append("2. Créer une carte cockpit `MICROSTRUCTURE TENSION`.")
    lines.append("3. Ajouter une gate Telegram B6 uniquement si `state=LOADED` et `level=HOT`.")
    lines.append("4. Plus tard: vraie table `tick_imbalance` si capture_bridge reçoit des ticks enrichis.")
    lines.append("")
    (MISSION / "B6_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    checkpoint = """# CHECKPOINT B6 — Order Flow Proxy Lite

## État
B6 Lite installé et testé.

## Modules ajoutés
- pf_order_flow_proxy_lite.py
- run_order_flow_proxy_once.py
- run_order_flow_proxy_all_once.py
- verify_b6_order_flow_proxy_once.py

## Sorties
- output/dashboard_surface/GBPUSD/microstructure_state.json
- output/dashboard_surface/EURUSD/microstructure_state.json
- output/dashboard_surface/USDJPY/microstructure_state.json
- output/dashboard_surface/microstructure_states.json

## Principe
Ce n'est pas du vrai Level 2.
C'est un proxy OHLC M1 pour détecter tension, absorption, release et chargement.

## Prochaine mission recommandée
B6.1 = fusion dans live brief + cockpit status + Telegram gate.
"""
    (MISSION / "CHECKPOINT_B6.md").write_text(checkpoint, encoding="utf-8")

    lexique = """# LEXIQUE PATCH B6 — Order Flow Proxy Lite

## MICROSTRUCTURE_PROXY_TENSION
Tension estimée depuis OHLC M1, pas depuis carnet réel.

## proxy_delta
Score signé représentant pression estimée de la bougie M1.
Positif = buy proxy.
Négatif = sell proxy.

## absorption_rate
Mesure de flux opposé dans la fenêtre.
Faible = déséquilibre persistant.
Fort = absorption/réintégration possible.

## LOADING
Tension en chargement, pas encore extrême.

## LOADED
Tension forte, déséquilibre peu absorbé.
Alerte précoce possible.

## RELEASING
Le flux opposé réapparaît.
Risque technique: réintégration ou piège inverse.

## ORDER_FLOW_PROXY_NOT_TRUE_LEVEL2
Rappel analytique: le signal ne lit pas encore bid_volume/ask_volume natif.
"""
    (MISSION / "LEXIQUE_PATCH_B6.md").write_text(lexique, encoding="utf-8")

    files_changed = "\n".join([
        "pf_order_flow_proxy_lite.py",
        "run_order_flow_proxy_once.py",
        "run_order_flow_proxy_all_once.py",
        "verify_b6_order_flow_proxy_once.py",
        "output/dashboard_surface/microstructure_states.json",
        "output/dashboard_surface/GBPUSD/microstructure_state.json",
        "output/dashboard_surface/EURUSD/microstructure_state.json",
        "output/dashboard_surface/USDJPY/microstructure_state.json",
        str(MISSION / "B6_REPORT.md"),
        str(MISSION / "CHECKPOINT_B6.md"),
        str(MISSION / "LEXIQUE_PATCH_B6.md"),
    ])
    (MISSION / "FILES_CHANGED.txt").write_text(files_changed, encoding="utf-8")

    zip_path = MISSION / "B6_ORDER_FLOW_PROXY_LITE_BUNDLE.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [
            Path("pf_order_flow_proxy_lite.py"),
            Path("run_order_flow_proxy_once.py"),
            Path("run_order_flow_proxy_all_once.py"),
            Path("verify_b6_order_flow_proxy_once.py"),
            Path("output/dashboard_surface/microstructure_states.json"),
            Path("output/dashboard_surface/GBPUSD/microstructure_state.json"),
            Path("output/dashboard_surface/EURUSD/microstructure_state.json"),
            Path("output/dashboard_surface/USDJPY/microstructure_state.json"),
            MISSION / "B6_REPORT.md",
            MISSION / "CHECKPOINT_B6.md",
            MISSION / "LEXIQUE_PATCH_B6.md",
            MISSION / "B6_REPORT.json",
            MISSION / "FILES_CHANGED.txt",
        ]:
            if p.exists():
                z.write(p, p.as_posix())

    print("B6_VERIFY_OK")
    print("report=", MISSION / "B6_REPORT.md")
    print("checkpoint=", MISSION / "CHECKPOINT_B6.md")
    print("lexique=", MISSION / "LEXIQUE_PATCH_B6.md")
    print("zip=", zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
