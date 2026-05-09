"""
PowerFlow V6 — cockpit_terminal.py
Mission 7A : cockpit Cockpit connecté à PowerFlow.

Role :
- Lire la DB powerflow.db.
- Consommer flow_scene_engine_v5.py, detect_relations_v5.py, detect_zones_v5.py et nodes_v6.
- Afficher une lecture multi-timeframe courte, utile, sans spam.
- Montrer 1 scene par timeframe + 1 scene dominante globale.

Execution Windows :
    python cockpit_terminal.py --db powerflow.db --symbols GBPUSD --timeframes 1,5,15,30 --once
    python cockpit_terminal.py --db powerflow.db --symbols GBPUSD --timeframes 1,5,15,30 --loop-seconds 60

Principe Cockpit :
- Pas de signal automatique.
- Une scene dominante.
- Une action de surveillance claire.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import pf_engine_scenes as scene_engine

DB_PATH = "powerflow.db"

TF_LABELS = {
    1: "M1",
    5: "M5",
    15: "M15",
    30: "M30",
    60: "H1",
    240: "H4",
    1440: "D1",
    10080: "W1",
}

INTEREST_RANK = {
    "IGNORE": 0,
    "WATCH_ZONE": 1,
    "STRUCTURE_BUILDING": 2,
    "TACTICAL_READY": 3,
    "SIGNAL_VALIDATED": 4,
}

SCENE_RANK = {
    "CHAOS_NO_TRADE": 0,
    "CENTER_BATTLE": 1,
    "COMPRESSION_BUILD": 2,
    "EXTREME_REJECTION": 3,
    "NEGATIVE_MIRROR_SYNC": 4,
    "OPPOSITION_REBALANCE": 5,
    "ROTATION_BUILDING": 6,
    "COALITION_PUSH": 7,
    "TREND_CONTINUATION": 8,
    "COMPRESSION_RELEASE": 9,
}

TF_WEIGHT = {
    1: 0,
    5: 6,
    15: 12,
    30: 16,
    60: 22,
    240: 28,
    1440: 34,
    10080: 40,
}


@dataclass
class CockpitTfState:
    symbol: str
    tf: int
    tf_label: str
    timestamp: str
    scene_type: str
    confidence: int
    interest: str
    leader: str
    reaction: str
    zone: str
    zone_weight: int
    nodes: str
    action: str
    cause: str
    response: str
    note: str
    raw: Dict

    @property
    def rank_score(self) -> int:
        return (
            self.confidence
            + INTEREST_RANK.get(self.interest, 0) * 25
            + SCENE_RANK.get(self.scene_type, 0) * 5
            + TF_WEIGHT.get(self.tf, 0)
            + min(20, self.zone_weight)
        )


def tf_label(tf: int) -> str:
    return TF_LABELS.get(tf, f"M{tf}")


def parse_csv_ints(value: str) -> List[int]:
    out: List[int] = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out


def parse_csv_strings(value: str) -> List[str]:
    return [x.strip().upper() for x in str(value).split(",") if x.strip()]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,))
    return cur.fetchone() is not None


def db_snapshot(conn: sqlite3.Connection, symbol: str, timeframes: Sequence[int]) -> List[Tuple[int, int, Optional[str]]]:
    if not table_exists(conn, "force_snapshots"):
        return []
    out: List[Tuple[int, int, Optional[str]]] = []
    for tf in timeframes:
        cur = conn.execute(
            """
            SELECT COUNT(*), MAX(created_at)
            FROM force_snapshots
            WHERE symbol=? AND timeframe=?
            """,
            (symbol.upper(), tf),
        )
        count, max_time = cur.fetchone()
        out.append((tf, int(count or 0), str(max_time) if max_time else None))
    return out


def scene_to_state(scene: Dict) -> CockpitTfState:
    zone_dev = scene.get("zone_devise") or "-"
    zone_type = scene.get("zone_story_type") or "-"
    zone_phase = scene.get("zone_phase") or "-"
    zone_weight = int(scene.get("zone_time_weight") or 0)
    zone = f"{zone_dev}:{zone_type}/{zone_phase}" if zone_type != "-" else "-"
    nodes_list = scene.get("nodes") or []
    nodes = "+".join(nodes_list) if nodes_list else "-"
    return CockpitTfState(
        symbol=str(scene.get("symbol") or "-"),
        tf=int(scene.get("tf") or 0),
        tf_label=str(scene.get("tf_label") or tf_label(int(scene.get("tf") or 0))),
        timestamp=str(scene.get("timestamp") or "-"),
        scene_type=str(scene.get("scene_type") or "NO_SCENE"),
        confidence=int(scene.get("confidence") or 0),
        interest=str(scene.get("interest") or "IGNORE"),
        leader=str(scene.get("leader") or "-"),
        reaction=str(scene.get("reaction") or "-"),
        zone=zone,
        zone_weight=zone_weight,
        nodes=nodes,
        action=str(scene.get("action") or "-"),
        cause=str(scene.get("cause") or "-"),
        response=str(scene.get("response") or "-"),
        note=str(scene.get("note") or "-"),
        raw=scene,
    )


def load_latest_scene(
    symbol: str,
    tf: int,
    db_path: str,
    bars: int,
    devises: str,
    rebuild_nodes: bool,
    session_offset: int,
) -> Optional[CockpitTfState]:
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            scenes = scene_engine.produce_scene_report(
                symbol=symbol,
                tf=tf,
                db_path=db_path,
                bars=bars,
                devises_arg=devises,
                rebuild_nodes=rebuild_nodes,
                only_interest=False,
                verbose=False,
                session_offset=session_offset,
            )
    except Exception as exc:
        return CockpitTfState(
            symbol=symbol.upper(),
            tf=tf,
            tf_label=tf_label(tf),
            timestamp="-",
            scene_type="ERROR",
            confidence=0,
            interest="IGNORE",
            leader="-",
            reaction="-",
            zone="-",
            zone_weight=0,
            nodes="-",
            action=f"Erreur lecture scene: {exc}",
            cause="-",
            response="-",
            note=str(exc),
            raw={"error": str(exc)},
        )
    if not scenes:
        return None
    return scene_to_state(scenes[-1])


def pick_dominant(states: Sequence[CockpitTfState]) -> Optional[CockpitTfState]:
    valid = [s for s in states if s.scene_type not in ("ERROR", "NO_SCENE")]
    if not valid:
        return None
    return max(valid, key=lambda s: s.rank_score)


def interest_icon(interest: str) -> str:
    if interest == "SIGNAL_VALIDATED":
        return "[SIGNAL]"
    if interest == "TACTICAL_READY":
        return "[READY]"
    if interest == "STRUCTURE_BUILDING":
        return "[BUILD]"
    if interest == "WATCH_ZONE":
        return "[WATCH]"
    return "[IGNORE]"


def compact_line(state: CockpitTfState) -> str:
    return (
        f"{state.tf_label:<4} {state.timestamp[11:16] if len(state.timestamp) >= 16 else '--:--'} "
        f"{interest_icon(state.interest):<8} {state.scene_type:<24} "
        f"{state.confidence:>3}/100 | L={state.leader:<3} R={state.reaction:<3} | "
        f"zone={state.zone} w={state.zone_weight} | nodes={state.nodes}"
    )


def cockpit_once(
    db_path: str,
    symbols: Sequence[str],
    timeframes: Sequence[int],
    bars: int,
    devises: str,
    rebuild_nodes: bool,
    session_offset: int,
    show_ignore: bool,
) -> None:
    if not os.path.exists(db_path):
        print(f"DB introuvable: {db_path}")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 110)
    print(f"PowerFlow V6 Cockpit | {now} | db={db_path}")
    print("=" * 110)

    conn = sqlite3.connect(db_path)
    try:
        for symbol in symbols:
            print(f"\n>>> {symbol.upper()} | TF={','.join(tf_label(t) for t in timeframes)} | devises={devises.upper()}")
            snap = db_snapshot(conn, symbol, timeframes)
            snap_txt = " | ".join(f"{tf_label(tf)}:{count} last={last_time[11:16] if last_time and len(last_time)>=16 else '-'}" for tf, count, last_time in snap)
            if snap_txt:
                print(f"DATA  {snap_txt}")
            states: List[CockpitTfState] = []
            for tf in timeframes:
                state = load_latest_scene(
                    symbol=symbol,
                    tf=tf,
                    db_path=db_path,
                    bars=bars,
                    devises=devises,
                    rebuild_nodes=rebuild_nodes,
                    session_offset=session_offset,
                )
                if state is None:
                    print(f"{tf_label(tf):<4} --:-- [NO DATA] Pas assez de donnees pour scène Cockpit")
                    continue
                states.append(state)
                if show_ignore or state.interest != "IGNORE":
                    print(compact_line(state))

            dominant = pick_dominant(states)
            if dominant:
                print("-" * 110)
                print(f"DOMINANTE  {dominant.symbol} {dominant.tf_label} — {dominant.scene_type} {dominant.confidence}/100 | {dominant.interest}")
                print(f"CAUSE      {dominant.cause}")
                print(f"REPONSE    {dominant.response}")
                print(f"ZONE       {dominant.zone} | poids={dominant.zone_weight}")
                print(f"ACTION     {dominant.action}")
            else:
                print("DOMINANTE  Aucune scene exploitable.")
    finally:
        conn.close()

    print("=" * 110)
    print("FIN COCKPIT")
    print("=" * 110)


def run_loop(
    db_path: str,
    symbols: Sequence[str],
    timeframes: Sequence[int],
    bars: int,
    devises: str,
    rebuild_nodes: bool,
    session_offset: int,
    show_ignore: bool,
    loop_seconds: int,
    once: bool,
) -> None:
    first = True
    while True:
        cockpit_once(
            db_path=db_path,
            symbols=symbols,
            timeframes=timeframes,
            bars=bars,
            devises=devises,
            rebuild_nodes=(rebuild_nodes and first),
            session_offset=session_offset,
            show_ignore=show_ignore,
        )
        first = False
        if once:
            return
        time.sleep(max(5, int(loop_seconds)))


def main() -> None:
    parser = argparse.ArgumentParser(description="PowerFlow V6 Cockpit")
    parser.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")
    parser.add_argument("--symbols", default="GBPUSD", help="Ex: GBPUSD,EURUSD")
    parser.add_argument("--timeframes", default="1,5,15,30", help="Ex: 1,5,15,30,60,240")
    parser.add_argument("--bars", type=int, default=40, help="Nombre de bougies lues par TF")
    parser.add_argument("--devises", default="eur,gbp,usd", help="Ex: eur,gbp,usd ou all")
    parser.add_argument("--rebuild-nodes", action="store_true", help="Reconstruire nodes_v6 au premier passage")
    parser.add_argument("--session-offset", type=int, default=0, help="Decalage horaire session/broker")
    parser.add_argument("--show-ignore", action="store_true", help="Afficher aussi les lignes IGNORE")
    parser.add_argument("--loop-seconds", type=int, default=60, help="Intervalle boucle live")
    parser.add_argument("--once", action="store_true", help="Un seul passage")
    args = parser.parse_args()

    run_loop(
        db_path=args.db,
        symbols=parse_csv_strings(args.symbols),
        timeframes=parse_csv_ints(args.timeframes),
        bars=args.bars,
        devises=args.devises,
        rebuild_nodes=args.rebuild_nodes,
        session_offset=args.session_offset,
        show_ignore=args.show_ignore,
        loop_seconds=args.loop_seconds,
        once=args.once,
    )


if __name__ == "__main__":
    main()
