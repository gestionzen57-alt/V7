#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — lab_powerflow.py
Runner CLI du lab expérimental.

Règles :
  - Read-only
  - Pas de DB write
  - Pas de Telegram
  - TFs libres : M1 → W1

Queries disponibles :
  kinematics    angle/speed/accel brut multi-TF multi-devise
  zones         zone_state cascade LTF→MTF→HTF
  nodes         fractal nodes + release state (3 horizons)
  turning_points  naissances de mouvement depuis zone
  orchestra     leader/follower/compression multi-TF
  relational    gravity brut SANS filtre P1.2
  fractal       cohérence LTF/MTF/HTF
  full          tout en une passe

Usage :
  python lab_powerflow.py --query kinematics --symbol GBPUSD \\
    --tfs "15,30,60" --start "2026-05-07T07:00:00" --end "2026-05-07T14:00:00"

  python lab_powerflow.py --query full --symbol GBPUSD \\
    --horizons "MTF" --once --pretty

  python lab_powerflow.py --query nodes --symbol GBPUSD \\
    --horizons "LTF,MTF,HTF" --start "..." --end "..." --out lab.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import moteur
try:
    from pf_lab_engine import (
        HORIZON_TFS,
        TF_LABEL,
        get_available_tfs,
        query_full,
        query_full_v2,
        query_full_v3,
        query_coalitions,
        query_tension_signature,
        query_fractal_coherence,
        query_kinematics,
        query_nodes,
        query_orchestra,
        query_relational,
        query_relational_gravity,
        query_temporal_density,
        query_zone_turning_points,
        query_zones,
    )
    ENGINE_OK = True
except ImportError as e:
    ENGINE_OK = False
    _ENGINE_ERROR = str(e)


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def parse_tfs(tfs_str: str) -> List[int]:
    """Parse '1,5,15,30,60' → [1, 5, 15, 30, 60]"""
    return [int(x.strip()) for x in tfs_str.split(",") if x.strip().isdigit()]


def parse_horizons(horizons_str: str) -> List[str]:
    """Parse 'LTF,MTF,HTF' → ['LTF', 'MTF', 'HTF']"""
    valid = {"LTF", "MTF", "HTF"}
    return [h.strip().upper() for h in horizons_str.split(",") if h.strip().upper() in valid]


def tfs_from_horizons(horizons: List[str]) -> List[int]:
    """Résoudre les TFs depuis les horizons demandés (sans doublons)."""
    tfs = []
    for h in horizons:
        for tf in HORIZON_TFS.get(h, []):
            if tf not in tfs:
                tfs.append(tf)
    return sorted(tfs)


def resolve_window(args: argparse.Namespace):
    """
    Résoudre start/end en UTC.
    Si --once : fenêtre glissante depuis NOW UTC (lookback minutes).
    Sinon utilise --start et --end fournis.
    """
    if args.once:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(minutes=args.lookback)
        return (
            start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        )
    if not args.start or not args.end:
        # Fallback : dernières 3h UTC
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(minutes=180)
        return (
            start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        )
    return args.start, args.end


def _json_serializer(obj: Any) -> Any:
    """
    Serializer universel pour json.dumps.
    Gère : dataclasses, enums, sets, objets avec __dict__ ou asdict.
    """
    # dataclass → dict
    try:
        from dataclasses import asdict as _asdict, fields as _fields
        if hasattr(obj, "__dataclass_fields__"):
            return _asdict(obj)
    except Exception:
        pass
    # enum → value
    try:
        import enum
        if isinstance(obj, enum.Enum):
            return obj.value
    except Exception:
        pass
    # set → list
    if isinstance(obj, set):
        return list(obj)
    # objet avec to_dict()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    # objet avec __dict__
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    # fallback str
    return str(obj)


def write_output(data: Dict[str, Any], out_path: Optional[str], pretty: bool) -> None:
    indent = 2 if pretty else None
    text = json.dumps(data, ensure_ascii=False, indent=indent, default=_json_serializer)
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        print(f"[OK] Output → {path}")
    else:
        print(text)


def print_summary(data: Dict[str, Any], query: str) -> None:
    """Affiche un résumé one-liner sur stderr pour suivi rapide."""
    symbol = data.get("symbol", "?")
    start = data.get("start", "?")[-8:] if data.get("start") else "?"
    end = data.get("end", "?")[-8:] if data.get("end") else "?"

    if query == "kinematics":
        summary = data.get("summary", {})
        dets = len(summary.get("detachments_detected", []))
        clusters = len(summary.get("clusters_detected", []))
        tfs_ok = len(summary.get("tfs_computed", []))
        print(f"[LAB] {symbol} kinematics | {start}→{end} | TFs={tfs_ok} | detachments={dets} | clusters={clusters}", file=sys.stderr)

    elif query == "zones":
        tps = len(data.get("turning_points", []))
        cascades = len(data.get("cascade", {}))
        print(f"[LAB] {symbol} zones | {start}→{end} | turning_points={tps} | cascades={cascades}", file=sys.stderr)

    elif query == "nodes":
        ns = data.get("node_summary", {})
        fn = ns.get("fractal_node_count", 0)
        conf = ns.get("confirmed_releases", 0)
        patterns = ns.get("patterns_detected", [])
        print(f"[LAB] {symbol} nodes | {start}→{end} | fractal={fn} | confirmed_releases={conf} | patterns={patterns}", file=sys.stderr)

    elif query == "turning_points":
        s = data.get("summary", {})
        print(f"[LAB] {symbol} turning_points | {start}→{end} | priority={s.get('priority','?')} confirmed={s.get('confirmed_count',0)} births={s.get('birth_count',0)}", file=sys.stderr)

    elif query == "orchestra":
        leader = data.get("leader_currency", "?")
        compression = data.get("compression_detected", False)
        patterns = data.get("patterns", [])
        state = data.get("status", data.get("state", "?"))
        print(f"[LAB] {symbol} orchestra | {start}→{end} | state={state} | leader={leader} | compression={compression} | patterns={len(patterns)}", file=sys.stderr)

    elif query == "relational":
        tfs = list(data.get("timeframes", {}).keys())
        print(f"[LAB] {symbol} relational | {start}→{end} | tfs={tfs}", file=sys.stderr)

    elif query == "fractal":
        s = data.get("summary", {})
        print(f"[LAB] {symbol} fractal | {start}→{end} | main_tf={data.get('main_tf_label','?')} | coherence={s.get('global_coherence','?')} | sync={s.get('global_sync_score','?')}", file=sys.stderr)

    elif query == "full":
        tp = data.get("turning_points", {}).get("summary", {})
        orch = data.get("orchestra", {})
        print(f"[LAB] {symbol} FULL | {start}→{end} | tp_priority={tp.get('priority','?')} | leader={orch.get('leader_currency','?')} | compression={orch.get('compression_detected',False)}", file=sys.stderr)

    elif query == "coalition":
        ct = data.get("cross_tf_summary", {})
        bw = ct.get("battlefield_windows", [])
        dom = ct.get("dominant_coalition", "?")
        ant = ct.get("dominant_antagonist", "?")
        comp = ct.get("compression_detected", False)
        print(f"[LAB] {symbol} coalition | {start}→{end} | battlefield_tfs={bw} | dominant={dom} | antagonist={ant} | compression={comp}", file=sys.stderr)

    elif query == "tension":
        ct = data.get("cross_tf_summary", {})
        top = ct.get("top_elastic_global", "?")
        elastic = ct.get("elastic_currencies", {})
        directional = ct.get("directional_currencies", {})
        print(f"[LAB] {symbol} tension | {start}→{end} | top_elastic={top} | elastic={list(elastic.keys())} | directional={list(directional.keys())}", file=sys.stderr)

    elif query in ("full_v2", "full_v3"):
        tp = data.get("turning_points", {}).get("summary", {})
        orch = data.get("orchestra", {})
        ct = data.get("cross_tf_summary", {}) if query == "full_v3" else {}
        coalition_info = data.get("coalitions", {}).get("cross_tf_summary", {}) if query == "full_v3" else {}
        bw = coalition_info.get("battlefield_windows", [])
        top_e = data.get("tension_signature", {}).get("cross_tf_summary", {}).get("top_elastic_global", "-") if query == "full_v3" else "-"
        print(f"[LAB] {symbol} {query.upper()} | {start}→{end} | tp_priority={tp.get('priority','?')} | leader={orch.get('leader_currency','?')} | battlefield_tfs={bw} | top_elastic={top_e}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# ARGPARSE
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab_powerflow",
        description="PowerFlow V6 — Lab expérimental. Read-only. Pas de Telegram.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :

  # Kinematics MTF brut
  python lab_powerflow.py --query kinematics --symbol GBPUSD \\
    --tfs "15,30,60" --start "2026-05-07T07:00:00" --end "2026-05-07T14:00:00" --pretty

  # Zones cascade 3 horizons
  python lab_powerflow.py --query zones --symbol GBPUSD \\
    --tfs "5,15,30,60,240" --start "2026-05-07T00:00:00" --end "2026-05-07T23:59:59"

  # Nodes sur 3 horizons
  python lab_powerflow.py --query nodes --symbol GBPUSD \\
    --horizons "LTF,MTF,HTF" --once --lookback 240 --pretty

  # Turning points MTF
  python lab_powerflow.py --query turning_points --symbol GBPUSD \\
    --tfs "15,30,60" --once --pretty

  # Fractal coherence H1 vs LTF
  python lab_powerflow.py --query fractal --symbol GBPUSD \\
    --main-tf 60 --sub-tfs "1,5,15,30" --once --pretty

  # Relational brut sans censure P1.2
  python lab_powerflow.py --query relational --symbol GBPUSD \\
    --tfs "1,5,15,60" --show-mixed --once --pretty

  # Full MTF session complète
  python lab_powerflow.py --query full --symbol GBPUSD \\
    --horizons "MTF" --once --lookback 180 --out lab_session.json --pretty

  # Test rapide TFs disponibles
  python lab_powerflow.py --list-tfs --symbol GBPUSD
""",
    )

    # Core
    parser.add_argument("--db", default="powerflow.db", help="Chemin powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbol ex: GBPUSD")
    parser.add_argument(
        "--query",
        choices=["kinematics", "zones", "nodes", "turning_points", "orchestra",
                 "relational", "relational_gravity", "temporal_density", "fractal",
                 "coalition", "tension",
                 "full", "full_v2", "full_v3"],
        default="full_v2",
        help="Type de query (défaut: full_v2)",
    )

    # Fenêtre temporelle
    parser.add_argument("--start", default=None, help="Début ISO ex: 2026-05-07T07:00:00")
    parser.add_argument("--end", default=None, help="Fin ISO ex: 2026-05-07T14:00:00")
    parser.add_argument("--once", action="store_true", help="Fenêtre glissante depuis NOW")
    parser.add_argument("--lookback", type=int, default=180, help="Minutes lookback si --once (défaut 180)")

    # TFs
    parser.add_argument("--tfs", default=None, help="TFs ex: '15,30,60' (défaut selon --horizons)")
    parser.add_argument(
        "--horizons",
        default="MTF",
        help="Horizons LTF/MTF/HTF ex: 'LTF,MTF,HTF' (défaut MTF)",
    )

    # Fractal coherence spécifique
    parser.add_argument("--main-tf", type=int, default=None, help="TF de référence pour fractal (défaut max des tfs)")
    parser.add_argument("--sub-tfs", default=None, help="Sub-TFs pour fractal ex: '1,5,15,30'")

    # Nodes
    parser.add_argument(
        "--devises",
        default="eur,gbp,usd,jpy,cad,chf,aud",
        help="Devises pour fractal nodes",
    )
    parser.add_argument("--max-per-tf", type=int, default=5, help="Max nodes par TF")
    parser.add_argument("--bars", type=int, default=160, help="Barres pour nodes (défaut 160)")

    # Orchestra
    parser.add_argument("--avg-bars", type=int, default=3, help="Barres lissage angle orchestra")
    parser.add_argument("--density-window", type=int, default=20, help="Barres pour temporal density (défaut 20)")
    parser.add_argument("--relational-bars", type=int, default=30, help="Barres pour relational gravity (défaut 30)")

    # Relational
    parser.add_argument("--show-mixed", action="store_true", default=True, help="Exposer états MIXED (défaut True)")
    parser.add_argument("--hide-mixed", action="store_true", help="Filtrer états MIXED")

    # Coalition (layer 10)
    parser.add_argument("--coalition-bars", type=int, default=50, help="Barres pour coalition detection (défaut 50)")
    parser.add_argument("--coalition-cohesion", type=float, default=0.62, help="Cohésion minimale coalition (défaut 0.62)")
    parser.add_argument("--coalition-field-score", type=float, default=0.45, help="Field score minimum active relation (défaut 0.45)")

    # Tension signature (layer 11)
    parser.add_argument("--tension-bars", type=int, default=30, help="Barres pour tension signature (défaut 30)")
    parser.add_argument("--tension-window", type=int, default=5, help="Fenêtre macro variance tension (défaut 5)")

    # Output
    parser.add_argument("--out", default=None, help="Fichier output JSON")
    parser.add_argument("--pretty", action="store_true", help="JSON indenté")
    parser.add_argument("--summary-only", action="store_true", help="Afficher résumé seulement (stderr)")
    parser.add_argument("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR")

    # Utils
    parser.add_argument("--list-tfs", action="store_true", help="Lister TFs disponibles en DB")
    parser.add_argument("--probe-db", action="store_true", help="Diagnostiquer format datetime et couverture DB")

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger("lab_powerflow")

    if not ENGINE_OK:
        print(f"[ERROR] pf_lab_engine non disponible: {_ENGINE_ERROR}", file=sys.stderr)
        return 1

    db_path = args.db

    # ── LIST TFS ──────────────────────────────────────────────────────────────
    if args.list_tfs:
        try:
            available = get_available_tfs(db_path, args.symbol)
            print(f"TFs disponibles pour {args.symbol}: {available}")
            labels = [f"{tf}={TF_LABEL.get(tf, tf)}" for tf in available]
            print("Labels:", ", ".join(labels))
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 1
        return 0

    # ── PROBE DB ──────────────────────────────────────────────────────────────
    if args.probe_db:
        try:
            from pf_lab_engine import connect_readonly
            conn = connect_readonly(db_path)
            print(f"\n=== PROBE DB : {db_path} ===\n")
            # Format datetime réel
            for tf in [1, 5, 15, 30, 60]:
                rows = conn.execute(
                    "SELECT created_at FROM force_snapshots WHERE symbol=? AND timeframe=? ORDER BY created_at DESC LIMIT 3",
                    (args.symbol.upper(), tf),
                ).fetchall()
                if rows:
                    samples = [str(r[0]) for r in rows]
                    print(f"TF={tf:4d} | derniers created_at : {samples}")
                else:
                    print(f"TF={tf:4d} | NO DATA")
            # Plage disponible
            row = conn.execute(
                "SELECT MIN(created_at), MAX(created_at), COUNT(*) FROM force_snapshots WHERE symbol=?",
                (args.symbol.upper(),),
            ).fetchone()
            if row:
                print(f"\nPlage totale : {row[0]} → {row[1]} | {row[2]} rows")
            conn.close()
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 1
        return 0

    # ── RÉSOUDRE TFs ─────────────────────────────────────────────────────────
    horizons = parse_horizons(args.horizons)

    if args.tfs:
        tfs = parse_tfs(args.tfs)
    else:
        tfs = tfs_from_horizons(horizons) if horizons else [15, 30, 60]

    if not tfs:
        print("[ERROR] Aucun TF résolu. Utilise --tfs '15,30,60' ou --horizons 'MTF'", file=sys.stderr)
        return 1

    # ── RÉSOUDRE FENÊTRE ─────────────────────────────────────────────────────
    start, end = resolve_window(args)
    logger.info(f"[{args.symbol}] {args.query} | TFs={tfs} | {start} → {end}")

    show_mixed = not args.hide_mixed  # --hide-mixed override --show-mixed

    # ── DISPATCH QUERIES ─────────────────────────────────────────────────────
    try:
        query = args.query

        if query == "kinematics":
            data = query_kinematics(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
            )

        elif query == "zones":
            data = query_zones(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
            )

        elif query == "nodes":
            data = query_nodes(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                horizons=horizons,
                bars=args.bars,
                devises_arg=args.devises,
                max_per_tf=args.max_per_tf,
            )

        elif query == "turning_points":
            data = query_zone_turning_points(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
            )

        elif query == "orchestra":
            data = query_orchestra(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                avg_bars=args.avg_bars,
            )

        elif query == "relational":
            data = query_relational(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                show_mixed=show_mixed,
            )

        elif query == "relational_gravity":
            data = query_relational_gravity(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                bars=args.relational_bars,
                show_mixed=show_mixed,
            )

        elif query == "temporal_density":
            data = query_temporal_density(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                window=args.density_window,
            )

        elif query == "fractal":
            main_tf = args.main_tf or max(tfs)
            sub_tfs_raw = args.sub_tfs or args.tfs
            sub_tfs = parse_tfs(sub_tfs_raw) if sub_tfs_raw else [tf for tf in tfs if tf != main_tf]
            data = query_fractal_coherence(
                db_path=db_path,
                symbol=args.symbol,
                main_tf=main_tf,
                sub_tfs=sub_tfs,
                start=start,
                end=end,
            )

        elif query == "full":
            main_tf = args.main_tf or max(tfs)
            data = query_full(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                horizons=horizons,
                avg_bars=args.avg_bars,
                show_mixed=show_mixed,
                main_tf_for_fractal=main_tf,
            )

        elif query == "full_v2":
            main_tf = args.main_tf or max(tfs)
            data = query_full_v2(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                horizons=horizons,
                avg_bars=args.avg_bars,
                show_mixed=show_mixed,
                main_tf_for_fractal=main_tf,
                density_window=args.density_window,
                relational_bars=args.relational_bars,
            )

        elif query == "coalition":
            data = query_coalitions(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                bars=args.coalition_bars,
                min_cohesion=args.coalition_cohesion,
                min_field_score=args.coalition_field_score,
            )

        elif query == "tension":
            data = query_tension_signature(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                bars=args.tension_bars,
                window=args.tension_window,
            )

        elif query == "full_v3":
            main_tf = args.main_tf or max(tfs)
            data = query_full_v3(
                db_path=db_path,
                symbol=args.symbol,
                tfs=tfs,
                start=start,
                end=end,
                horizons=horizons,
                avg_bars=args.avg_bars,
                show_mixed=show_mixed,
                main_tf_for_fractal=main_tf,
                density_window=args.density_window,
                relational_bars=args.relational_bars,
                coalition_bars=args.coalition_bars,
                coalition_cohesion=args.coalition_cohesion,
                coalition_field_score=args.coalition_field_score,
                tension_bars=args.tension_bars,
                tension_window=args.tension_window,
            )

        else:
            print(f"[ERROR] Query inconnue: {query}", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        print(f"[ERROR] DB introuvable: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    # ── OUTPUT ────────────────────────────────────────────────────────────────
    # Toujours afficher le résumé
    print_summary(data, query)

    if not args.summary_only:
        write_output(data, args.out, args.pretty)

    return 0


if __name__ == "__main__":
    sys.exit(main())
