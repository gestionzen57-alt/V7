"""
T0166 — B9 Live Data Freshness Guard V0.

Read-only freshness qualifier for PowerFlow B9 live inputs.
It never writes to powerflow.db or tick_archive.db and never emits trading instructions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import csv
import datetime as dt
import json
import sqlite3
import zipfile

VERSION = "T0166_B9_LIVE_DATA_FRESHNESS_GUARD_V0"

FORBIDDEN_TERMS = ["BUY", "SELL", "ACHAT", "VENTE", "PROBABILIT", "TAUX DE RÉUSSITE", "TAUX DE REUSSITE"]

LIVE_FRESH = "LIVE_FRESH"
LIVE_STALE = "LIVE_STALE"
DB_EMPTY = "DB_EMPTY"
DB_MISSING = "DB_MISSING"
TABLE_MISSING = "TABLE_MISSING"
PROXY_ONLY = "PROXY_ONLY"
RAW_TEXTURE_MISSING = "RAW_TEXTURE_MISSING"
SOURCE_LIVE_UNQUALIFIED = "SOURCE_LIVE_UNQUALIFIED"
LIVE_FRESH_WITH_LIMITS = "LIVE_FRESH_WITH_LIMITS"
LIVE_STALE_WITH_MEMORY_CONTEXT = "LIVE_STALE_WITH_MEMORY_CONTEXT"

TIMESTAMP_COLUMNS = (
    "time_msc", "timestamp", "ts", "time", "created_at", "datetime", "server_time", "last_ts"
)

@dataclass
class SourceCheck:
    source_name: str
    db_path: str
    table_name: str
    db_exists: bool
    table_exists: bool
    row_count: int
    latest_timestamp_raw: str
    latest_timestamp_iso: str
    age_seconds: Optional[float]
    freshness_state: str
    source_mode: str
    technical_limits: str

@dataclass
class GuardResult:
    version: str
    generated_at: str
    guard_state: str
    core_root: str
    freshness_seconds: int
    powerflow_db_path: str
    tick_archive_db_path: str
    live_candidate_path: str
    live_candidate_state: str
    live_candidate_source_quality_state: str
    live_candidate_raw_texture_state: str
    force_snapshots_v2_rows: int
    tick_stream_rows: int
    latest_force_snapshot_ts: str
    latest_tick_ts: str
    source_checks: List[Dict[str, Any]]
    technical_limits: List[str]
    forbidden_language_hits: List[str]
    no_decision_guard: bool


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_timestamp(value: Any) -> Tuple[str, str, Optional[dt.datetime]]:
    if value is None or value == "":
        return "", "", None
    raw = str(value)
    try:
        if isinstance(value, (int, float)) or raw.isdigit():
            n = int(float(raw))
            if n > 10_000_000_000_000:  # microseconds-ish
                d = dt.datetime.fromtimestamp(n / 1_000_000, tz=dt.timezone.utc)
            elif n > 10_000_000_000:  # milliseconds
                d = dt.datetime.fromtimestamp(n / 1000, tz=dt.timezone.utc)
            elif n > 1_000_000_000:  # seconds
                d = dt.datetime.fromtimestamp(n, tz=dt.timezone.utc)
            else:
                return raw, "", None
            return raw, d.replace(microsecond=0).isoformat(), d
        normalized = raw.replace("Z", "+00:00")
        d = dt.datetime.fromisoformat(normalized)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        d = d.astimezone(dt.timezone.utc)
        return raw, d.replace(microsecond=0).isoformat(), d
    except Exception:
        return raw, "", None


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    # URI read-only avoids accidental creation/write.
    uri = "file:" + str(db_path.resolve()).replace("\\", "/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _best_timestamp_column(columns: Iterable[str]) -> str:
    cols = list(columns)
    lower_map = {c.lower(): c for c in cols}
    for name in TIMESTAMP_COLUMNS:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    for c in cols:
        lc = c.lower()
        if "time" in lc or "date" in lc or lc.endswith("ts"):
            return c
    return ""


def inspect_sqlite_source(db_path: Path, table: str, source_name: str, freshness_seconds: int, now: Optional[dt.datetime] = None) -> SourceCheck:
    now = now or dt.datetime.now(dt.timezone.utc)
    if not db_path.exists():
        return SourceCheck(source_name, str(db_path), table, False, False, 0, "", "", None, DB_MISSING, "DB_MISSING", "Base absente : source live non vérifiable.")
    try:
        with _connect_readonly(db_path) as conn:
            if not _table_exists(conn, table):
                return SourceCheck(source_name, str(db_path), table, True, False, 0, "", "", None, TABLE_MISSING, "TABLE_MISSING", f"Table {table} absente : source non disponible.")
            count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)
            if count <= 0:
                return SourceCheck(source_name, str(db_path), table, True, True, 0, "", "", None, DB_EMPTY, "DB_EMPTY", f"Table {table} vide : pas de fraîcheur live mesurable.")
            cols = _table_columns(conn, table)
            ts_col = _best_timestamp_column(cols)
            if not ts_col:
                return SourceCheck(source_name, str(db_path), table, True, True, count, "", "", None, SOURCE_LIVE_UNQUALIFIED, "TIMESTAMP_UNKNOWN", "Aucune colonne timestamp détectée : freshness non qualifiable.")
            latest_raw = conn.execute(f"SELECT {ts_col} FROM {table} ORDER BY {ts_col} DESC LIMIT 1").fetchone()[0]
            raw, iso, parsed = parse_timestamp(latest_raw)
            if parsed is None:
                return SourceCheck(source_name, str(db_path), table, True, True, count, raw, "", None, SOURCE_LIVE_UNQUALIFIED, "TIMESTAMP_UNPARSEABLE", f"Timestamp non parsable via {ts_col}.")
            age = max(0.0, (now - parsed.astimezone(dt.timezone.utc)).total_seconds())
            state = LIVE_FRESH if age <= freshness_seconds else LIVE_STALE
            mode = "LIVE_SQLITE_TABLE"
            limit = "Source fraîche." if state == LIVE_FRESH else f"Source stale : âge {int(age)}s > seuil {freshness_seconds}s."
            return SourceCheck(source_name, str(db_path), table, True, True, count, raw, iso, age, state, mode, limit)
    except Exception as exc:
        return SourceCheck(source_name, str(db_path), table, True, False, 0, "", "", None, SOURCE_LIVE_UNQUALIFIED, "SQLITE_READ_ERROR", f"Erreur lecture SQLite read-only : {type(exc).__name__}: {exc}")


def load_json(path: Path) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _first_present(d: Dict[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def inspect_live_candidate(path: Path) -> Tuple[str, str, str, List[str]]:
    if not path or not path.exists():
        return "LIVE_CANDIDATE_MISSING", "SOURCE_LIVE_UNQUALIFIED", "RAW_TEXTURE_MISSING", ["Latest scene candidate absent : live scene non qualifiée."]
    try:
        data = load_json(path)
    except Exception as exc:
        return "LIVE_CANDIDATE_UNREADABLE", "SOURCE_LIVE_UNQUALIFIED", "RAW_TEXTURE_MISSING", [f"Latest scene candidate illisible : {type(exc).__name__}."]
    candidate = data.get("latest_candidate") or data.get("candidate") or data.get("scene") or data
    source_state = str(_first_present(candidate, ["source_quality_gate_state", "b9_source_quality_gate_state", "source_quality_state"], "SOURCE_LIVE_UNQUALIFIED"))
    raw_texture = str(_first_present(candidate, ["raw_texture_state", "b9_raw_texture_state", "raw_texture_role"], "RAW_TEXTURE_MISSING"))
    state = "LIVE_CANDIDATE_PRESENT"
    limits: List[str] = []
    if source_state in ("", "SOURCE_LIVE_UNQUALIFIED", "SOURCE_UNKNOWN_LIMITED"):
        limits.append("Candidate live présente mais source_quality non qualifiée.")
    if "RAW" not in raw_texture.upper() or raw_texture.upper() in ("RAW_TEXTURE_MISSING", "RAW_UNAVAILABLE"):
        limits.append("Texture raw absente ou non qualifiée côté candidate live.")
    if not limits:
        limits.append("Candidate live présente avec source/texture qualifiées.")
    return state, source_state, raw_texture, limits


def forbidden_language_scan_text(text: str) -> List[str]:
    upper = text.upper()
    hits = []
    for term in FORBIDDEN_TERMS:
        if term in upper:
            hits.append(term)
    return sorted(set(hits))


def determine_guard_state(force_check: SourceCheck, tick_check: SourceCheck, candidate_source: str, candidate_raw: str) -> str:
    if force_check.freshness_state == LIVE_FRESH or tick_check.freshness_state == LIVE_FRESH:
        if candidate_source in ("SOURCE_LIVE_UNQUALIFIED", "SOURCE_UNKNOWN_LIMITED", "") or candidate_raw in ("RAW_TEXTURE_MISSING", "RAW_UNAVAILABLE", ""):
            return LIVE_FRESH_WITH_LIMITS
        return LIVE_FRESH
    if force_check.freshness_state == DB_EMPTY and tick_check.freshness_state in (DB_EMPTY, DB_MISSING, TABLE_MISSING):
        return DB_EMPTY
    if force_check.freshness_state == DB_MISSING and tick_check.freshness_state == DB_MISSING:
        return DB_MISSING
    if force_check.freshness_state == TABLE_MISSING and tick_check.freshness_state in (TABLE_MISSING, DB_MISSING):
        return TABLE_MISSING
    if force_check.freshness_state == LIVE_STALE or tick_check.freshness_state == LIVE_STALE:
        return LIVE_STALE_WITH_MEMORY_CONTEXT
    if candidate_source in ("SOURCE_LIVE_UNQUALIFIED", "SOURCE_UNKNOWN_LIMITED", ""):
        return SOURCE_LIVE_UNQUALIFIED
    if candidate_raw in ("RAW_TEXTURE_MISSING", "RAW_UNAVAILABLE", ""):
        return RAW_TEXTURE_MISSING
    return PROXY_ONLY


def build_guard(
    core_root: Path,
    powerflow_db: Optional[Path] = None,
    tick_archive_db: Optional[Path] = None,
    live_candidate_json: Optional[Path] = None,
    freshness_seconds: int = 300,
    now_iso: Optional[str] = None,
) -> GuardResult:
    core_root = Path(core_root)
    powerflow_db = Path(powerflow_db) if powerflow_db else core_root / "powerflow.db"
    tick_archive_db = Path(tick_archive_db) if tick_archive_db else core_root / "tick_archive.db"
    live_candidate_json = Path(live_candidate_json) if live_candidate_json else core_root / "outputs" / "b9_live_scene_candidate_queue_v0" / "B9_LATEST_SCENE_CANDIDATE_V0.json"
    now = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00")) if now_iso else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    force = inspect_sqlite_source(powerflow_db, "force_snapshots_v2", "powerflow.force_snapshots_v2", freshness_seconds, now)
    ticks = inspect_sqlite_source(tick_archive_db, "tick_stream", "tick_archive.tick_stream", freshness_seconds, now)
    cand_state, cand_source, cand_raw, cand_limits = inspect_live_candidate(live_candidate_json)
    guard_state = determine_guard_state(force, ticks, cand_source, cand_raw)
    limits = [force.technical_limits, ticks.technical_limits] + cand_limits
    if force.row_count == 0:
        limits.append("force_snapshots_v2 = 0 ligne ou non disponible : la scène live ne doit pas être durcie en vérité raw.")
    if ticks.row_count == 0:
        limits.append("tick_stream = 0 ligne ou non disponible : texture tick raw non vérifiée.")
    if guard_state in (LIVE_STALE_WITH_MEMORY_CONTEXT, SOURCE_LIVE_UNQUALIFIED, RAW_TEXTURE_MISSING, DB_EMPTY, DB_MISSING, TABLE_MISSING):
        limits.append("Guard freshness dégradé : affichage possible uniquement avec limites techniques visibles.")
    result = GuardResult(
        version=VERSION,
        generated_at=now.replace(microsecond=0).isoformat(),
        guard_state=guard_state,
        core_root=str(core_root),
        freshness_seconds=freshness_seconds,
        powerflow_db_path=str(powerflow_db),
        tick_archive_db_path=str(tick_archive_db),
        live_candidate_path=str(live_candidate_json),
        live_candidate_state=cand_state,
        live_candidate_source_quality_state=cand_source,
        live_candidate_raw_texture_state=cand_raw,
        force_snapshots_v2_rows=force.row_count,
        tick_stream_rows=ticks.row_count,
        latest_force_snapshot_ts=force.latest_timestamp_iso,
        latest_tick_ts=ticks.latest_timestamp_iso,
        source_checks=[asdict(force), asdict(ticks)],
        technical_limits=sorted(set([x for x in limits if x])),
        forbidden_language_hits=[],
        no_decision_guard=True,
    )
    # Scan only user-facing generated text, not internal constant names.
    user_text = "\n".join([
        result.guard_state,
        result.live_candidate_state,
        "\n".join(result.technical_limits),
    ])
    result.forbidden_language_hits = forbidden_language_scan_text(user_text)
    return result


def result_to_markdown(result: GuardResult) -> str:
    lines = [
        "# B9 Live Data Freshness Guard V0",
        "",
        "## Résumé exécutif",
        f"- État freshness : `{result.guard_state}`",
        f"- force_snapshots_v2 rows : `{result.force_snapshots_v2_rows}`",
        f"- tick_stream rows : `{result.tick_stream_rows}`",
        f"- Candidate live : `{result.live_candidate_state}`",
        f"- Source quality candidate : `{result.live_candidate_source_quality_state}`",
        f"- Raw texture candidate : `{result.live_candidate_raw_texture_state}`",
        "",
        "## Lecture PowerFlow",
        "B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.",
        "Ce guard qualifie la fraîcheur technique de la source avant affichage dashboard ou Telegram preview.",
        "",
        "## Sources inspectées",
    ]
    for s in result.source_checks:
        lines += [
            f"### {s['source_name']}",
            f"- DB : `{s['db_path']}`",
            f"- Table : `{s['table_name']}`",
            f"- État : `{s['freshness_state']}`",
            f"- Rows : `{s['row_count']}`",
            f"- Latest timestamp : `{s['latest_timestamp_iso']}`",
            f"- Age seconds : `{s['age_seconds']}`",
            f"- Limite : {s['technical_limits']}",
            "",
        ]
    lines += [
        "## Limites techniques",
    ]
    for lim in result.technical_limits:
        lines.append(f"- {lim}")
    lines += [
        "",
        "## Ce que B9 peut faire",
        "- Afficher la scène avec un niveau de fraîcheur source visible.",
        "- Signaler DB vide, source stale, proxy-only ou raw texture manquante.",
        "- Empêcher qu’une scène live soit durcie en vérité raw sans preuve.",
        "",
        "## Ce que B9 ne doit pas conclure",
        "- Aucun ordre directionnel.",
        "- Aucun taux de réussite.",
        "- Aucune décision d’exécution.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(result: GuardResult, output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "B9_LIVE_DATA_FRESHNESS_GUARD_V0.json"
    md_path = output_dir / "B9_LIVE_DATA_FRESHNESS_GUARD_V0.md"
    rows_path = output_dir / "B9_LIVE_DATA_FRESHNESS_ROWS_V0.csv"
    manifest_path = output_dir / "B9_LIVE_DATA_FRESHNESS_GUARD_MANIFEST.json"
    zip_path = output_dir / "B9_LIVE_DATA_FRESHNESS_GUARD_V0.zip"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(result_to_markdown(result), encoding="utf-8")
    with rows_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(result.source_checks[0].keys()) if result.source_checks else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in result.source_checks:
            writer.writerow(row)
    manifest = {
        "version": VERSION,
        "generated_at": result.generated_at,
        "guard_state": result.guard_state,
        "files": [json_path.name, md_path.name, rows_path.name, manifest_path.name, zip_path.name],
        "read_only": True,
        "db_write": False,
        "dashboard_live": False,
        "telegram_send": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in (json_path, md_path, rows_path, manifest_path):
            z.write(p, p.name)
    return {"json": str(json_path), "md": str(md_path), "csv": str(rows_path), "manifest": str(manifest_path), "zip": str(zip_path)}


def build_and_write(
    core_root: Path,
    output_dir: Path,
    powerflow_db: Optional[Path] = None,
    tick_archive_db: Optional[Path] = None,
    live_candidate_json: Optional[Path] = None,
    freshness_seconds: int = 300,
    now_iso: Optional[str] = None,
) -> Tuple[GuardResult, Dict[str, str]]:
    result = build_guard(core_root, powerflow_db, tick_archive_db, live_candidate_json, freshness_seconds, now_iso)
    paths = write_outputs(result, output_dir)
    return result, paths
