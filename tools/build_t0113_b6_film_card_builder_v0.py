#!/usr/bin/env python3
"""
T0113 — B6 Film Card Builder V0

Read-only builder that converts B6 Memory Candidate Board rows into B6 film cards.

Doctrine:
- B9 reads the scene.
- T0112 qualifies proxy/raw agreement and source quality.
- B6 does not predict; B6 compares films.
- No BUY/SELL, no probability of success, no dashboard, no Telegram, no DB write.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ACTIVE_STATES = {"B6_KEEP_CANDIDATE", "B6_REVIEW_CANDIDATE"}
LOW_TRUST_STATE = "B6_LOW_TRUST_CANDIDATE"
REJECT_STATES = {"B6_REJECT_RAW_UNAVAILABLE", "RAW_UNAVAILABLE"}
RAW_UNAVAILABLE = "RAW_UNAVAILABLE"

OUTPUT_COLUMNS = [
    "film_id",
    "date",
    "time_start",
    "time_end",
    "session",
    "source_family",
    "summary_recovery_type",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "moment_type",
    "label_fr",
    "base",
    "reaction",
    "projection",
    "judgment",
    "raw_agreement",
    "proxy_vs_raw_verdict",
    "proxy_raw_agreement_state",
    "source_quality_score",
    "source_quality",
    "source_quality_state",
    "b6_memory_candidate_score",
    "b6_memory_candidate_state",
    "raw_texture_role",
    "raw_delta_pips",
    "raw_range_pips",
    "raw_tick_count",
    "memory_family",
    "pattern_key",
    "why_keep_for_memory",
    "memory_use_case",
    "similarity_features",
    "limits",
]

MANDATORY_INPUT_COLUMNS = [
    "date",
    "time_start",
    "time_end",
    "source_family",
    "summary_recovery_type",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "proxy_raw_agreement_state",
    "source_quality_score",
    "source_quality_state",
    "b6_memory_candidate_score",
    "b6_memory_candidate_state",
    "raw_texture_role",
    "raw_delta_pips",
    "raw_range_pips",
    "raw_tick_count",
    "moment_type",
    "label_fr",
    "memory_candidate_reason",
    "technical_limits",
]


def _clean_key(k: str) -> str:
    return (k or "").lstrip("\ufeff").strip()


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _float(v: Any, default: float = 0.0) -> float:
    try:
        s = _norm(v).replace(",", ".")
        if not s:
            return default
        return float(s)
    except Exception:
        return default


def _int(v: Any, default: int = 0) -> int:
    try:
        s = _norm(v)
        if not s:
            return default
        return int(float(s))
    except Exception:
        return default


def load_board(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"B6 board CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            row = {_clean_key(k): _norm(v) for k, v in raw.items()}
            if not row.get("date") and row.get("time_start"):
                row["date"] = row["time_start"][:10]
            rows.append(row)
    missing = [c for c in MANDATORY_INPUT_COLUMNS if c not in rows[0]] if rows else MANDATORY_INPUT_COLUMNS
    if missing:
        raise ValueError(f"Missing mandatory B6 board columns: {missing}")
    return rows


def session_from_time(time_start: str) -> str:
    try:
        hour = int(time_start[11:13])
    except Exception:
        return "SESSION_UNKNOWN"
    if 0 <= hour <= 6:
        return "ASIAN_SESSION"
    if hour == 7:
        return "ASIA_LONDON_HANDOVER"
    if 8 <= hour <= 10:
        return "LONDON_IGNITION"
    if 11 <= hour <= 12:
        return "LONDON_MIDDAY_TRANSITION"
    if 13 <= hour <= 15:
        return "LONDON_NY_OVERLAP"
    if 16 <= hour <= 20:
        return "NY_AFTERNOON"
    return "LATE_US_ASIA_HANDOVER"


def memory_family(moment_type: str, raw_texture_role: str, label_fr: str) -> str:
    mt = moment_type.upper()
    rt = raw_texture_role.upper()
    label = label_fr.lower()
    if "UNAVAILABLE" in rt:
        return "RAW_UNAVAILABLE_REJECT"
    if "FRICTION" in rt or "ABSORPTION" in mt or "absorption" in label or "friction" in label:
        return "FRICTION_ABSORPTION_MEMORY"
    if "PROGRESS" in rt or "DIRECTIONAL" in mt or "deplacement" in label or "déplacement" in label:
        return "DIRECTIONAL_PROGRESS_MEMORY"
    if "ROTATION" in rt or "ROTATIONAL" in mt or "rotation" in label or "respiration" in label:
        return "ROTATION_BREATH_MEMORY"
    if "BALANCED" in mt or "auction" in label:
        return "BALANCED_AUCTION_MEMORY"
    return "MIXED_CONTEXT_MEMORY"


def base_reading(row: Dict[str, str]) -> str:
    label = row.get("label_fr") or row.get("moment_type") or "Scene B9"
    mt = row.get("moment_type", "")
    return f"Base scene: {label} ({mt})."


def reaction_reading(row: Dict[str, str]) -> str:
    raw_role = row.get("raw_texture_role", "")
    delta = _float(row.get("raw_delta_pips"))
    rng = _float(row.get("raw_range_pips"))
    ticks = _int(row.get("raw_tick_count"))
    if row.get("proxy_vs_raw_verdict") == RAW_UNAVAILABLE or raw_role == RAW_UNAVAILABLE:
        return "Reaction raw indisponible: scene rejetee de la memoire active."
    if raw_role == "RAW_PROGRESS_CONFIRMED":
        return f"Reaction raw progressive: delta {delta:g} pips, range {rng:g} pips, {ticks} ticks."
    if raw_role == "RAW_FRICTION_CONFIRMED":
        return f"Reaction raw frictionnelle: activite lisible avec deplacement contraint, delta {delta:g} pips, range {rng:g} pips, {ticks} ticks."
    if raw_role == "RAW_ROTATION_CONFIRMED":
        return f"Reaction raw rotationnelle: respiration/rotation de zone, delta {delta:g} pips, range {rng:g} pips, {ticks} ticks."
    return f"Reaction raw mixte: {raw_role}, delta {delta:g} pips, range {rng:g} pips, {ticks} ticks."


def projection_reading(row: Dict[str, str]) -> str:
    delta = abs(_float(row.get("raw_delta_pips")))
    rng = _float(row.get("raw_range_pips"))
    if row.get("proxy_vs_raw_verdict") == RAW_UNAVAILABLE:
        return "Projection non exploitable: raw unavailable."
    if rng <= 0:
        return "Projection non mesurable: range raw nul ou absent."
    ratio = delta / rng
    if ratio >= 0.65:
        return f"Projection directionnelle lisible: delta/range={ratio:.2f}."
    if ratio >= 0.25:
        return f"Projection partielle: mouvement utile mais encore nuance par la texture, delta/range={ratio:.2f}."
    return f"Projection faible: effort/rotation absorbe le deplacement, delta/range={ratio:.2f}."


def judgment_reading(row: Dict[str, str]) -> str:
    state = row.get("b6_memory_candidate_state", "")
    verdict = row.get("proxy_vs_raw_verdict", "")
    sq = row.get("source_quality_state", "")
    if verdict == RAW_UNAVAILABLE or state in REJECT_STATES:
        return "REJECT: raw indisponible, conserve seulement comme trace de couverture."
    if state == "B6_KEEP_CANDIDATE" and verdict == "CONFIRMED_BY_RAW" and sq == "SOURCE_QUALITY_STRONG":
        return "KEEP fort: accord raw confirme et source quality forte."
    if state == "B6_KEEP_CANDIDATE" and verdict == "NUANCED_BY_RAW":
        return "KEEP nuance: scene utile, raw nuance la lecture sans la durcir en confirmation."
    if state == "B6_REVIEW_CANDIDATE":
        return "REVIEW: scene lisible mais doit rester en revue avant indexation forte."
    if state == "B6_LOW_TRUST_CANDIDATE":
        return "LOW TRUST: audit seulement, pas de memoire active par defaut."
    return f"Judgment technique: {state}, {verdict}, {sq}."


def pattern_key(row: Dict[str, str]) -> str:
    parts = [
        memory_family(row.get("moment_type", ""), row.get("raw_texture_role", ""), row.get("label_fr", "")),
        row.get("source_family", ""),
        row.get("source_mode", ""),
        row.get("proxy_vs_raw_verdict", ""),
        row.get("raw_texture_role", ""),
        row.get("source_quality_state", ""),
    ]
    safe = "|".join(parts)
    return re.sub(r"[^A-Z0-9_\-|]", "_", safe.upper())


def film_id(row: Dict[str, str]) -> str:
    seed = "|".join([
        row.get("date", ""),
        row.get("time_start", ""),
        row.get("time_end", ""),
        row.get("source_family", ""),
        row.get("moment_type", ""),
        row.get("raw_texture_role", ""),
    ])
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8].upper()
    day = (row.get("date") or "0000-00-00").replace("-", "")
    hm = "0000"
    ts = row.get("time_start", "")
    if len(ts) >= 16:
        hm = ts[11:16].replace(":", "")
    return f"B6FC_{day}_{hm}_{digest}"


def similarity_features(row: Dict[str, str]) -> str:
    features = [
        f"family={memory_family(row.get('moment_type',''), row.get('raw_texture_role',''), row.get('label_fr',''))}",
        f"session={session_from_time(row.get('time_start',''))}",
        f"raw_texture={row.get('raw_texture_role','')}",
        f"raw_agreement={row.get('proxy_vs_raw_verdict','')}",
        f"source_quality={row.get('source_quality_state','')}",
        f"source_family={row.get('source_family','')}",
        f"source_mode={row.get('source_mode','')}",
    ]
    return "; ".join(features)


def why_keep(row: Dict[str, str]) -> str:
    state = row.get("b6_memory_candidate_state", "")
    family = memory_family(row.get("moment_type", ""), row.get("raw_texture_role", ""), row.get("label_fr", ""))
    reason = row.get("memory_candidate_reason", "")
    if state == "B6_KEEP_CANDIDATE":
        return f"KEEP memoire: {family}; {reason}"
    if state == "B6_REVIEW_CANDIDATE":
        return f"REVIEW memoire: {family}; scene comparable mais a relire; {reason}"
    if state == "B6_LOW_TRUST_CANDIDATE":
        return f"LOW TRUST audit: {family}; pas de memoire active par defaut; {reason}"
    return f"Rejected or trace only: {reason}"


def memory_use_case(row: Dict[str, str]) -> str:
    family = memory_family(row.get("moment_type", ""), row.get("raw_texture_role", ""), row.get("label_fr", ""))
    if family == "FRICTION_ABSORPTION_MEMORY":
        return "Comparer les scenes d'effort visible sans resultat directionnel propre, absorption ou friction locale."
    if family == "DIRECTIONAL_PROGRESS_MEMORY":
        return "Comparer les scenes de progression / deplacement directionnel avec role raw explicite."
    if family == "ROTATION_BREATH_MEMORY":
        return "Comparer les respirations de zone, rotations et transitions sans durcir en prediction."
    if family == "BALANCED_AUCTION_MEMORY":
        return "Comparer les auctions equilibrees et zones de decision lentes."
    return "Comparer comme contexte mixte, utile pour faux positifs et differences de texture."


def build_card(row: Dict[str, str]) -> Dict[str, str]:
    return {
        "film_id": film_id(row),
        "date": row.get("date", "") or row.get("time_start", "")[:10],
        "time_start": row.get("time_start", ""),
        "time_end": row.get("time_end", ""),
        "session": session_from_time(row.get("time_start", "")),
        "source_family": row.get("source_family", ""),
        "summary_recovery_type": row.get("summary_recovery_type", ""),
        "source_mode": row.get("source_mode", ""),
        "data_visibility": row.get("data_visibility", ""),
        "confidence_cap": row.get("confidence_cap", ""),
        "moment_type": row.get("moment_type", ""),
        "label_fr": row.get("label_fr", ""),
        "base": base_reading(row),
        "reaction": reaction_reading(row),
        "projection": projection_reading(row),
        "judgment": judgment_reading(row),
        "raw_agreement": row.get("proxy_vs_raw_verdict", ""),
        "proxy_vs_raw_verdict": row.get("proxy_vs_raw_verdict", ""),
        "proxy_raw_agreement_state": row.get("proxy_raw_agreement_state", ""),
        "source_quality_score": row.get("source_quality_score", ""),
        "source_quality": row.get("source_quality_state", ""),
        "source_quality_state": row.get("source_quality_state", ""),
        "b6_memory_candidate_score": row.get("b6_memory_candidate_score", ""),
        "b6_memory_candidate_state": row.get("b6_memory_candidate_state", ""),
        "raw_texture_role": row.get("raw_texture_role", ""),
        "raw_delta_pips": row.get("raw_delta_pips", ""),
        "raw_range_pips": row.get("raw_range_pips", ""),
        "raw_tick_count": row.get("raw_tick_count", ""),
        "memory_family": memory_family(row.get("moment_type", ""), row.get("raw_texture_role", ""), row.get("label_fr", "")),
        "pattern_key": pattern_key(row),
        "why_keep_for_memory": why_keep(row),
        "memory_use_case": memory_use_case(row),
        "similarity_features": similarity_features(row),
        "limits": row.get("technical_limits", "") + "; T0113 film card is comparative memory only; no prediction; no BUY/SELL; no probability of success",
    }


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _md_table(rows: List[Dict[str, str]], columns: List[str], max_rows: int = 30) -> str:
    out = []
    out.append("| " + " | ".join(columns) + " |")
    out.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows[:max_rows]:
        vals = []
        for c in columns:
            v = str(row.get(c, "")).replace("|", "/").replace("\n", " ")
            if len(v) > 100:
                v = v[:97] + "..."
            vals.append(v)
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def write_markdown(path: Path, cards: List[Dict[str, str]], low_trust: List[Dict[str, str]], rejected: List[Dict[str, str]], manifest: Dict[str, Any]) -> None:
    by_family = Counter(c["memory_family"] for c in cards)
    by_date = Counter(c["date"] for c in cards)
    by_session = Counter(c["session"] for c in cards)
    by_state = Counter(c["b6_memory_candidate_state"] for c in cards)
    priority = sorted(cards, key=lambda c: (
        0 if c["proxy_vs_raw_verdict"] == "CONFIRMED_BY_RAW" else 1,
        0 if c["source_quality_state"] == "SOURCE_QUALITY_STRONG" else 1,
        -_float(c.get("b6_memory_candidate_score")),
    ))[:20]
    lines = []
    lines.append("# T0113 — B6 Film Card Builder V0")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("T0113 transforme le B6 Memory Candidate Board V0 en cartes film comparables. Le board sélectionne; la carte film structure la mémoire.")
    lines.append("")
    lines.append("> B6 ne prédit pas. B6 compare des films. Une carte film conserve une scène passée avec sa provenance, son accord raw et ses limites.")
    lines.append("")
    lines.append("## Sources et provenance")
    lines.append("")
    lines.append("- Entrée: `B6_MEMORY_CANDIDATE_BOARD_V0.csv`")
    lines.append("- Sortie active: KEEP + REVIEW uniquement")
    lines.append("- LOW_TRUST conservé en audit séparé")
    lines.append("- RAW_UNAVAILABLE rejeté de la mémoire active")
    lines.append("- Aucune écriture `powerflow.db`, aucune écriture `tick_archive.db`")
    lines.append("")
    lines.append("## Counts globaux")
    lines.append("")
    lines.append(f"- Board rows input: {manifest['input_rows']}")
    lines.append(f"- Film cards active: {manifest['active_film_cards']}")
    lines.append(f"- Low trust audit rows: {manifest['low_trust_rows']}")
    lines.append(f"- Rejected raw unavailable rows: {manifest['rejected_rows']}")
    lines.append("")
    lines.append("## Counts par état B6")
    lines.append("")
    for k, v in sorted(manifest["counts_by_candidate_state"].items()):
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Counts par famille mémoire")
    lines.append("")
    for k, v in by_family.most_common():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Counts par session")
    lines.append("")
    for k, v in by_session.most_common():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Counts par date")
    lines.append("")
    for k, v in sorted(by_date.items()):
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Cartes film prioritaires")
    lines.append("")
    lines.append(_md_table(priority, ["film_id", "date", "time_start", "session", "memory_family", "proxy_vs_raw_verdict", "source_quality_state", "raw_texture_role"], max_rows=20))
    lines.append("")
    lines.append("## Ce que T0113 construit")
    lines.append("")
    lines.append("Chaque carte film expose:")
    lines.append("")
    lines.append("- `base`: scène B9 initiale;")
    lines.append("- `reaction`: texture raw et réaction mesurée;")
    lines.append("- `projection`: qualité du déplacement dans le range;")
    lines.append("- `judgment`: statut mémoire technique;")
    lines.append("- `pattern_key`: clé stable pour futur T0114 Similarity Index;")
    lines.append("- `similarity_features`: traits comparables sans prédiction.")
    lines.append("")
    lines.append("## Ce que B6 peut comparer")
    lines.append("")
    lines.append("- famille mémoire;")
    lines.append("- session;")
    lines.append("- source family / source mode;")
    lines.append("- accord proxy/raw;")
    lines.append("- source quality;")
    lines.append("- rôle de texture raw;")
    lines.append("- amplitude delta/range;")
    lines.append("- limites techniques visibles.")
    lines.append("")
    lines.append("## Ce que B6 ne doit pas conclure")
    lines.append("")
    lines.append("- aucune probabilité de succès;")
    lines.append("- aucune direction future;")
    lines.append("- aucun BUY/SELL;")
    lines.append("- aucune vérité raw si la scène est seulement `NUANCED_BY_RAW`;")
    lines.append("- aucune fusion dure entre `FORCE_SNAPSHOT_DERIVED` et `RECOVERED_EXISTING_B9_SUMMARY`.")
    lines.append("")
    lines.append("## Limites techniques")
    lines.append("")
    lines.append("- Les cartes héritent des limites du board B6 et de T0112.")
    lines.append("- Les champs `base/reaction/projection/judgment` sont une normalisation de lecture, pas une nouvelle preuve raw.")
    lines.append("- `FORCE_SNAPSHOT_DERIVED` reste une reconstruction proxy et ne devient jamais un recovered existing summary.")
    lines.append("- `NUANCED_BY_RAW` reste nuancé, jamais durci en confirmation.")
    lines.append("- `LOW_TRUST` est conservé pour audit, hors mémoire active par défaut.")
    lines.append("- `RAW_UNAVAILABLE` est rejeté de la mémoire active.")
    lines.append("")
    lines.append("## Prochaine brique recommandée")
    lines.append("")
    lines.append("T0114 — B6 Similarity Index V0: comparer une scène actuelle aux cartes film, afficher similarités, différences et risques techniques de faux positif, sans prédiction.")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_zip(zip_path: Path, files: List[Path], base_dir: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if file.exists() and file.is_file():
                zf.write(file, file.relative_to(base_dir).as_posix())


def build(input_csv: Path, output_dir: Path) -> Dict[str, Any]:
    rows = load_board(input_csv)
    active_rows = [r for r in rows if r.get("b6_memory_candidate_state") in ACTIVE_STATES and r.get("proxy_vs_raw_verdict") != RAW_UNAVAILABLE]
    low_trust_rows = [r for r in rows if r.get("b6_memory_candidate_state") == LOW_TRUST_STATE]
    rejected_rows = [r for r in rows if r.get("b6_memory_candidate_state") in REJECT_STATES or r.get("proxy_vs_raw_verdict") == RAW_UNAVAILABLE]
    cards = [build_card(r) for r in active_rows]
    low_cards = [build_card(r) for r in low_trust_rows]
    rejected_cards = [build_card(r) for r in rejected_rows]

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "B6_FILM_CARDS_V0.csv"
    json_path = output_dir / "B6_FILM_CARDS_V0.json"
    md_path = output_dir / "B6_FILM_CARDS_V0.md"
    low_path = output_dir / "B6_FILM_CARD_LOW_TRUST_AUDIT_V0.csv"
    rej_path = output_dir / "B6_FILM_CARD_REJECTED_RAW_UNAVAILABLE_V0.csv"
    manifest_path = output_dir / "B6_FILM_LIBRARY_V0_MANIFEST.json"
    zip_path = output_dir / "B6_FILM_LIBRARY_V0.zip"

    manifest = {
        "artifact": "T0113_B6_FILM_CARD_BUILDER_V0",
        "input_csv": str(input_csv),
        "input_rows": len(rows),
        "active_film_cards": len(cards),
        "low_trust_rows": len(low_cards),
        "rejected_rows": len(rejected_cards),
        "counts_by_candidate_state": dict(Counter(r.get("b6_memory_candidate_state", "") for r in rows)),
        "counts_by_source_family_active": dict(Counter(c.get("source_family", "") for c in cards)),
        "counts_by_raw_agreement_active": dict(Counter(c.get("proxy_vs_raw_verdict", "") for c in cards)),
        "counts_by_memory_family_active": dict(Counter(c.get("memory_family", "") for c in cards)),
        "policy": {
            "no_db_write": True,
            "no_dashboard": True,
            "no_telegram": True,
            "no_buy_sell": True,
            "no_probability_of_success": True,
            "force_snapshot_derived_not_recovered_existing_summary": True,
            "nuanced_by_raw_not_hardened_to_confirmed": True,
        },
    }

    write_csv(csv_path, cards, OUTPUT_COLUMNS)
    write_json(json_path, {"film_cards": cards})
    write_csv(low_path, low_cards, OUTPUT_COLUMNS)
    write_csv(rej_path, rejected_cards, OUTPUT_COLUMNS)
    write_json(manifest_path, manifest)
    write_markdown(md_path, cards, low_cards, rejected_cards, manifest)
    make_zip(zip_path, [csv_path, json_path, md_path, low_path, rej_path, manifest_path], output_dir)
    return manifest


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build B6 Film Cards V0 from B6 Memory Candidate Board V0 CSV.")
    parser.add_argument("--input-csv", required=True, help="Path to B6_MEMORY_CANDIDATE_BOARD_V0.csv")
    parser.add_argument("--output-dir", required=True, help="Output directory for B6 film library files")
    args = parser.parse_args(argv)
    manifest = build(Path(args.input_csv), Path(args.output_dir))
    print(json.dumps({
        "status": "OK",
        "artifact": manifest["artifact"],
        "input_rows": manifest["input_rows"],
        "active_film_cards": manifest["active_film_cards"],
        "low_trust_rows": manifest["low_trust_rows"],
        "rejected_rows": manifest["rejected_rows"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
