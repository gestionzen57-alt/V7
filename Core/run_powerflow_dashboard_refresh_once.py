"""
run_powerflow_dashboard_refresh_once.py
PowerFlow V6 — Dashboard Full Refresh Runner V0.1.1

Exécute la chaîne complète dans l'ordre obligatoire :

  1. Behavioral Alert Mapper
       temporal_node_state.json + currency_energy_state.json (optionnel)
       + relational_gravity depuis cockpit JSON si présent
       → output/behavioral_alert_queue.json

  2a. Cockpit Agentic State  (si --skip-cockpit absent)
       powerflow.db + behavioral_alert_queue.json
       → output/cockpit_agentic_state_v01.json

  2b. Refresh Cockpit From Queue  (si --refresh-cockpit-from-queue)
       Injecte behavioral_alert_queue.json dans cockpit existant
       sans recalculer depuis DB
       → output/cockpit_agentic_state_v01.json (mis à jour en place)

  3. Dashboard Sync Agent
       cockpit_agentic_state_v01.json + dashboard_data.json existant
       → dashboard_data.json (contient behavioral_flow)

Règles :
  - Aucune écriture DB
  - Pas de Telegram
  - Ne modifie pas pf_*, dashboard_live.html
  - dashboard_sync_agent est toujours la dernière étape
  - Si une étape échoue, les étapes suivantes sont bloquées (fail-fast)

Critère de succès :
  dashboard_data.json contient behavioral_flow après exécution.

Exemples :
    # Refresh complet depuis DB :
    python run_powerflow_dashboard_refresh_once.py \\
        --db powerflow.db --symbol GBPUSD \\
        --start 2026-05-06T09:00:00 --end 2026-05-06T10:30:00 \\
        --visual-htf-story confirmed --pretty --summary

    # Refresh rapide sans recalcul cockpit :
    python run_powerflow_dashboard_refresh_once.py \\
        --skip-cockpit --refresh-cockpit-from-queue --pretty --summary
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Defaults — cohérents avec les runners individuels
# ---------------------------------------------------------------------------

DEFAULT_DB = "powerflow.db"
DEFAULT_SYMBOL = "GBPUSD"
DEFAULT_RECENT_MINUTES = 180
DEFAULT_TELEGRAM_MODE = "SCALPING"

DEFAULT_TEMPORAL = Path("output") / "temporal_node_state.json"
DEFAULT_BEHAVIORAL_QUEUE = Path("output") / "behavioral_alert_queue.json"
DEFAULT_COCKPIT = Path("output") / "cockpit_agentic_state_v01.json"
DEFAULT_DASHBOARD = Path("dashboard_data.json")

ENERGY_CANDIDATES = [
    Path("output") / "currency_energy_state.json",
    Path("output") / "currency_energy_state_m1.json",
    Path("output") / "currency_energy_state_m1_after_v08b.json",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, data: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )


def _resolve_energy(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for p in ENERGY_CANDIDATES:
        if p.exists():
            return p
    return None


def _banner(step: int, total: int, label: str) -> None:
    print(f"\n[{step}/{total}] {label}")
    print("-" * 60)


def _ok(label: str, elapsed: float) -> None:
    print(f"  OK  {label}  ({elapsed:.2f}s)")


def _fail(label: str, exc: Exception) -> None:
    print(f"  FAIL  {label}")
    print(f"  ERROR: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Step 1 — Behavioral Alert Mapper
# ---------------------------------------------------------------------------

def step_behavioral_mapper(
    temporal_path: Path,
    energy_path: Path | None,
    out_path: Path,
    pretty: bool,
    cockpit_path: Path | None = None,
) -> dict[str, Any]:
    """
    Charge temporal_node_state + currency_energy_state (optionnel).
    Charge relational_gravity depuis cockpit_agentic_state_v01.json si disponible.
    Produit behavioral_alert_queue.json.
    Ne recalcule rien — lit les JSON existants.
    """
    from pf_behavioral_alert_mapper import map_behavioral_alerts

    if not temporal_path.exists():
        raise FileNotFoundError(
            f"temporal_node_state introuvable : {temporal_path}\n"
            f"  → Lancer d'abord : python run_temporal_node_state_once.py --db {DEFAULT_DB}"
        )

    with temporal_path.open("r", encoding="utf-8") as f:
        tns = json.load(f)

    energy: dict[str, Any] | None = None
    if energy_path and energy_path.exists():
        with energy_path.open("r", encoding="utf-8") as f:
            energy = json.load(f)

    # ── Relational Gravity — lecture optionnelle depuis cockpit JSON ──
    # Si cockpit absent ou vide : rg_block=None → mapper silencieux sur RG
    rg_block: dict[str, Any] | None = None
    _ck = cockpit_path or DEFAULT_COCKPIT
    if _ck.exists():
        try:
            cockpit_data = json.loads(_ck.read_text(encoding="utf-8"))
            if isinstance(cockpit_data, dict):
                rg_block = cockpit_data.get("relational_gravity") or None
        except Exception:
            rg_block = None
    # ─────────────────────────────────────────────────────────────────

    result = map_behavioral_alerts(
        temporal_node_state=tns,
        currency_energy_state=energy,
        relational_gravity=rg_block,
    )

    _write_json(out_path, result, pretty=pretty)
    return result


# ---------------------------------------------------------------------------
# Step 2 — Cockpit Agentic State
# ---------------------------------------------------------------------------

def step_cockpit(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    visual_htf_story: str,
    behavioral_queue_path: Path,
    out_path: Path,
    pretty: bool,
) -> dict[str, Any]:
    """
    Construit cockpit_agentic_state_v01.json en injectant behavioral_alert_queue.
    """
    from cockpit_agentic_state_v01 import build_cockpit_agentic_state

    state = build_cockpit_agentic_state(
        db_path=db_path,
        symbol=symbol,
        start=start,
        end=end,
        visual_htf_story=visual_htf_story,
        behavioral_queue_path=behavioral_queue_path,
    )

    _write_json(out_path, state, pretty=pretty)
    return state


# ---------------------------------------------------------------------------
# Step 3 — Dashboard Sync Agent
# ---------------------------------------------------------------------------

def step_dashboard_sync(
    cockpit_path: Path,
    dashboard_path: Path,
    out_path: Path,
    pretty: bool,
) -> dict[str, Any]:
    """
    Fusionne cockpit_agentic_state + dashboard_data existant.
    Produit dashboard_data.json avec behavioral_flow.
    Dernière étape — obligatoire.
    """
    from dashboard_sync_agent_v01 import sync_dashboard_data

    cockpit = _load_json(cockpit_path)
    if not cockpit:
        raise FileNotFoundError(f"cockpit_agentic_state introuvable ou vide : {cockpit_path}")

    existing = _load_json(dashboard_path)

    synced = sync_dashboard_data(cockpit, existing)

    _write_json(out_path, synced, pretty=pretty)
    return synced


# ---------------------------------------------------------------------------
# Step 2b — Refresh Cockpit From Queue
# ---------------------------------------------------------------------------

_LEVEL_PRIORITY: dict[str, int] = {"HOT": 4, "DEGRADED": 3, "WATCH": 2, "INFO": 1}


def _build_behavioral_summary_from_queue(queue: dict[str, Any]) -> dict[str, Any]:
    """
    Reconstruit behavioral_summary depuis behavioral_alert_queue.
    Règle priorité : HOT > DEGRADED > WATCH > INFO.
    Identique à la logique de cockpit_agentic_state_v01.py — sans import.
    """
    behavioral = queue.get("behavioral_alerts", [])
    degraded   = queue.get("degraded_alerts", [])
    all_alerts = behavioral + degraded

    if not all_alerts:
        return {
            "behavioral_count": 0,
            "degraded_count": 0,
            "top_alert": None,
            "top_level": None,
            "has_degraded": False,
            "has_hot_behavioral": False,
        }

    top = max(
        all_alerts,
        key=lambda a: _LEVEL_PRIORITY.get(a.get("level", ""), 0),
    )
    return {
        "behavioral_count": len(behavioral),
        "degraded_count": len(degraded),
        "top_alert": top.get("name"),
        "top_level": top.get("level"),
        "has_degraded": bool(degraded),
        "has_hot_behavioral": any(a.get("level") == "HOT" for a in all_alerts),
    }


def step_refresh_cockpit_from_queue(
    cockpit_path: Path,
    queue_path: Path,
    pretty: bool,
) -> dict[str, Any]:
    """
    Injecte behavioral_alert_queue.json dans cockpit_agentic_state_v01.json existant.
    Ne recalcule rien depuis DB. Écrit cockpit_path en place.

    Champs injectés / mis à jour :
      behavioral_alerts, degraded_alerts, film_steps,
      next_watch_enriched, behavioral_summary

    Erreurs claires si fichiers absents.
    """
    if not cockpit_path.exists():
        raise FileNotFoundError(
            f"cockpit_agentic_state introuvable : {cockpit_path}\n"
            f"  → Lancer d'abord sans --skip-cockpit, ou vérifier le chemin."
        )
    if not queue_path.exists():
        raise FileNotFoundError(
            f"behavioral_alert_queue introuvable : {queue_path}\n"
            f"  → L'étape Behavioral Alert Mapper doit tourner en premier."
        )

    cockpit = json.loads(cockpit_path.read_text(encoding="utf-8"))
    if not isinstance(cockpit, dict):
        raise ValueError(f"cockpit_agentic_state malformé : {cockpit_path}")

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    if not isinstance(queue, dict):
        raise ValueError(f"behavioral_alert_queue malformé : {queue_path}")

    # next_watch_enriched : fusion original fractal/scene + enrichissement queue
    _original_nw: list[str] = []
    fractal = cockpit.get("fractal") or {}
    scene   = cockpit.get("scene")   or {}
    _fnw = fractal.get("next_watch") if isinstance(fractal, dict) else None
    _snw = scene.get("next_watch")   if isinstance(scene, dict)   else None
    if _fnw:
        _original_nw.append(_fnw)
    if _snw and _snw != _fnw:
        _original_nw.append(_snw)
    _queue_nw: list[str] = queue.get("next_watch_enriched", [])
    _seen: set[str] = set()
    merged_nw: list[str] = []
    for _nw in _original_nw + _queue_nw:
        if _nw not in _seen:
            _seen.add(_nw)
            merged_nw.append(_nw)

    # Injecter les 5 champs behavioral
    cockpit["behavioral_alerts"]   = queue.get("behavioral_alerts", [])
    cockpit["degraded_alerts"]     = queue.get("degraded_alerts", [])
    cockpit["film_steps"]          = queue.get("film_steps", [])
    cockpit["next_watch_enriched"] = merged_nw
    cockpit["behavioral_summary"]  = _build_behavioral_summary_from_queue(queue)

    _write_json(cockpit_path, cockpit, pretty=pretty)
    return cockpit


# ---------------------------------------------------------------------------
# Validation finale
# ---------------------------------------------------------------------------

def _validate_behavioral_flow(dashboard_path: Path) -> bool:
    """Vérifie que behavioral_flow est présent dans dashboard_data.json."""
    data = _load_json(dashboard_path)
    return bool(data.get("behavioral_flow"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="PowerFlow V6 — Dashboard Full Refresh Runner V0.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # DB / symbol (pour cockpit)
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--start", default=None,
                        help="Fenêtre cockpit start (ex: 2026-05-06T09:00:00)")
    parser.add_argument("--end", default=None,
                        help="Fenêtre cockpit end (ex: 2026-05-06T10:30:00)")
    parser.add_argument("--visual-htf-story", default="unknown",
                        choices=["unknown", "confirmed", "rejected"])

    # Paths
    parser.add_argument("--temporal", default=str(DEFAULT_TEMPORAL),
                        help="Path to temporal_node_state.json")
    parser.add_argument("--energy", default=None,
                        help="Path to currency_energy_state.json (auto-détecté si absent)")
    parser.add_argument("--behavioral-queue", default=str(DEFAULT_BEHAVIORAL_QUEUE),
                        help="Output path for behavioral_alert_queue.json")
    parser.add_argument("--cockpit-out", default=str(DEFAULT_COCKPIT),
                        help="Output path for cockpit_agentic_state_v01.json")
    parser.add_argument("--dashboard", default=str(DEFAULT_DASHBOARD),
                        help="Path to existing dashboard_data.json (lu + écrasé)")
    parser.add_argument("--dashboard-out", default=None,
                        help="Output path pour dashboard_data.json (défaut = --dashboard)")

    # Options
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print tous les JSON de sortie")
    parser.add_argument("--summary", action="store_true",
                        help="Afficher un résumé compact après exécution")
    parser.add_argument("--skip-cockpit", action="store_true",
                        help="Sauter l'étape cockpit (utiliser le JSON existant)")
    parser.add_argument("--refresh-cockpit-from-queue", action="store_true",
                        help=(
                            "Injecter behavioral_alert_queue dans cockpit existant "
                            "sans recalculer depuis DB. "
                            "Requiert --skip-cockpit et cockpit_agentic_state_v01.json existant."
                        ))

    args = parser.parse_args()

    temporal_path = Path(args.temporal)
    behavioral_queue_path = Path(args.behavioral_queue)
    cockpit_path = Path(args.cockpit_out)
    dashboard_path = Path(args.dashboard)
    dashboard_out = Path(args.dashboard_out) if args.dashboard_out else dashboard_path
    energy_path = _resolve_energy(args.energy)

    # start/end obligatoires si cockpit non skippé
    if not args.skip_cockpit:
        if not args.start or not args.end:
            print("ERREUR : --start et --end sont requis pour l'étape cockpit.")
            print("  Exemple : --start 2026-05-06T09:00:00 --end 2026-05-06T10:30:00")
            print("  Ou utiliser --skip-cockpit pour sauter cette étape.")
            return 1

    TOTAL = 2 if args.skip_cockpit else 3
    if args.skip_cockpit and args.refresh_cockpit_from_queue:
        TOTAL = 3  # mapper + refresh + dashboard
    step = 0
    t_global = time.perf_counter()

    print("=" * 60)
    print("POWERFLOW V6 — DASHBOARD FULL REFRESH")
    print(f"symbol={args.symbol} | db={args.db}")
    print(f"temporal={temporal_path}")
    print(f"energy={energy_path or 'NONE (auto)'}")
    if args.refresh_cockpit_from_queue:
        print("mode=REFRESH_COCKPIT_FROM_QUEUE")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Étape 1 — Behavioral Alert Mapper
    # ------------------------------------------------------------------
    step += 1
    _banner(step, TOTAL, "Behavioral Alert Mapper")
    t0 = time.perf_counter()
    try:
        bf_result = step_behavioral_mapper(
            temporal_path=temporal_path,
            energy_path=energy_path,
            out_path=behavioral_queue_path,
            pretty=args.pretty,
            cockpit_path=cockpit_path,
        )
        elapsed = time.perf_counter() - t0
        _ok(f"out={behavioral_queue_path}", elapsed)
        print(f"  behavioral_count={len(bf_result.get('behavioral_alerts', []))}")
        print(f"  degraded_count={len(bf_result.get('degraded_alerts', []))}")
        print(f"  film_steps_count={len(bf_result.get('film_steps', []))}")
    except Exception as exc:
        _fail("Behavioral Alert Mapper", exc)
        return 1

    # ------------------------------------------------------------------
    # Étape 2 — Cockpit Agentic State (optionnelle avec --skip-cockpit)
    # ------------------------------------------------------------------
    if not args.skip_cockpit:
        step += 1
        _banner(step, TOTAL, "Cockpit Agentic State")
        t0 = time.perf_counter()
        try:
            cockpit_result = step_cockpit(
                db_path=args.db,
                symbol=args.symbol,
                start=args.start,
                end=args.end,
                visual_htf_story=args.visual_htf_story,
                behavioral_queue_path=behavioral_queue_path,
                out_path=cockpit_path,
                pretty=args.pretty,
            )
            elapsed = time.perf_counter() - t0
            _ok(f"out={cockpit_path}", elapsed)
            print(f"  cockpit_status={cockpit_result.get('cockpit_status')}")
            print(f"  headline={cockpit_result.get('headline', '')[:80]}")
            bs = cockpit_result.get("behavioral_summary", {}) or {}
            print(f"  top_alert={bs.get('top_alert')}")
        except Exception as exc:
            _fail("Cockpit Agentic State", exc)
            return 1

    elif args.refresh_cockpit_from_queue:
        # ── Mode rapide : injecter queue dans cockpit existant sans DB ──
        step += 1
        _banner(step, TOTAL, "Refresh Cockpit From Queue")
        t0 = time.perf_counter()
        try:
            cockpit_result = step_refresh_cockpit_from_queue(
                cockpit_path=cockpit_path,
                queue_path=behavioral_queue_path,
                pretty=args.pretty,
            )
            elapsed = time.perf_counter() - t0
            _ok(f"out={cockpit_path}", elapsed)
            bs = cockpit_result.get("behavioral_summary", {}) or {}
            print(f"  cockpit_behavioral_count={bs.get('behavioral_count', 0)}")
            print(f"  top_alert={bs.get('top_alert')}")
            print(f"  top_level={bs.get('top_level')}")
            print(f"  has_hot={bs.get('has_hot_behavioral', False)}")
        except Exception as exc:
            _fail("Refresh Cockpit From Queue", exc)
            return 1

    else:
        print(f"\n[--] Cockpit skippé — utilisation de {cockpit_path}")

    # ------------------------------------------------------------------
    # Étape 3 — Dashboard Sync Agent (toujours en dernier)
    # ------------------------------------------------------------------
    step += 1
    _banner(step, TOTAL, "Dashboard Sync Agent")
    t0 = time.perf_counter()
    try:
        dashboard_result = step_dashboard_sync(
            cockpit_path=cockpit_path,
            dashboard_path=dashboard_path,
            out_path=dashboard_out,
            pretty=args.pretty,
        )
        elapsed = time.perf_counter() - t0
        _ok(f"out={dashboard_out}", elapsed)
        bf = dashboard_result.get("behavioral_flow", {}) or {}
        print(f"  behavioral_flow.status={bf.get('status')}")
        print(f"  behavioral_flow.top_alert={bf.get('top_alert')}")
        print(f"  behavioral_flow.alerts_count={len(bf.get('alerts', []))}")
    except Exception as exc:
        _fail("Dashboard Sync Agent", exc)
        return 1

    # ------------------------------------------------------------------
    # Validation finale
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    t_total = time.perf_counter() - t_global

    if _validate_behavioral_flow(dashboard_out):
        print(f"DASHBOARD_FULL_REFRESH_OK  ({t_total:.2f}s)")
        print(f"dashboard_out={dashboard_out}")
        print("behavioral_flow=PRESENT")
    else:
        print("DASHBOARD_FULL_REFRESH_WARN")
        print(f"dashboard_out={dashboard_out}")
        print("behavioral_flow=ABSENT — vérifier cockpit_agentic_state_v01.json")

    if args.summary:
        print()
        print("--- SUMMARY ---")
        bs = dashboard_result.get("behavioral_summary", {}) or {}
        bf = dashboard_result.get("behavioral_flow", {}) or {}
        print(f"behavioral_count={bs.get('behavioral_count', 0)}")
        print(f"degraded_count={bs.get('degraded_count', 0)}")
        print(f"top_alert={bs.get('top_alert')}")
        print(f"top_level={bs.get('top_level')}")
        print(f"has_hot={bs.get('has_hot_behavioral', False)}")
        print(f"behavioral_flow_status={bf.get('status')}")
        print(f"film_steps={len(dashboard_result.get('film_steps', []))}")
        print(f"next_watch={len(dashboard_result.get('next_watch_enriched', []))}")

        print()
        for a in dashboard_result.get("behavioral_alerts", []):
            print(f"  [{a.get('level')}] {a.get('name')}")
        for a in dashboard_result.get("degraded_alerts", []):
            print(f"  [{a.get('level')}] {a.get('name')}")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
