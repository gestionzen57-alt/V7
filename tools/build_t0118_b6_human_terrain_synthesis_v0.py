#!/usr/bin/env python3
"""T0118 — B6 Human Terrain Synthesis V0.

Read-only analytical layer that summarizes B6 film cards into a human terrain
synthesis. It does not predict, does not emit BUY/SELL, and does not write DBs.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0118_B6_HUMAN_TERRAIN_SYNTHESIS_V0"
DOCTRINE = [
    "B9 lit la scene.",
    "B6 compare des films.",
    "T0118 synthetise les familles de terrain.",
    "PowerFlow doit apprendre des transitions de scene, pas des directions isolees.",
    "Aucune prediction, aucun BUY/SELL, aucune probabilite de succes, aucune ecriture DB.",
]

REQUIRED_CARD_FIELDS = [
    "film_id", "date", "session", "source_family", "summary_recovery_type",
    "source_mode", "data_visibility", "memory_family", "raw_agreement",
    "source_quality_state", "b6_memory_candidate_state", "raw_texture_role",
    "base", "reaction", "projection", "judgment", "limits",
]


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cards(path: Path) -> List[Dict[str, Any]]:
    data = load_json(path)
    if isinstance(data, dict):
        cards = data.get("film_cards", [])
    elif isinstance(data, list):
        cards = data
    else:
        raise ValueError(f"Unsupported film cards JSON shape: {type(data)!r}")
    if not isinstance(cards, list):
        raise ValueError("film_cards must be a list")
    normalized = []
    for raw in cards:
        if not isinstance(raw, dict):
            continue
        card = {field: str(raw.get(field, "") or "") for field in REQUIRED_CARD_FIELDS}
        # keep numeric and auxiliary fields
        for k, v in raw.items():
            if k not in card:
                card[k] = v
        state = card.get("b6_memory_candidate_state", "")
        verdict = card.get("raw_agreement", card.get("proxy_vs_raw_verdict", ""))
        if "LOW_TRUST" in state or "RAW_UNAVAILABLE" in state or verdict == "RAW_UNAVAILABLE":
            # T0113 active film library should already exclude these, but keep contract hard.
            continue
        normalized.append(card)
    return normalized


def load_false_positive(path: Path | None) -> Dict[str, Any] | None:
    if not path or not path.exists():
        return None
    data = load_json(path)
    if not isinstance(data, dict):
        return None
    return data


def count_by(cards: Iterable[Dict[str, Any]], key: str) -> Counter:
    c = Counter()
    for card in cards:
        val = str(card.get(key, "") or "UNKNOWN")
        c[val] += 1
    return c


def counter_rows(counter: Counter, label: str) -> List[Dict[str, Any]]:
    total = sum(counter.values()) or 1
    return [
        {label: k, "count": v, "share": round(v / total, 4)}
        for k, v in counter.most_common()
    ]


def compute_date_rows(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for card in cards:
        grouped[str(card.get("date", "UNKNOWN") or "UNKNOWN")].append(card)
    rows = []
    for date, items in sorted(grouped.items()):
        total = len(items)
        confirmed = sum(1 for x in items if x.get("raw_agreement") == "CONFIRMED_BY_RAW")
        nuanced = sum(1 for x in items if x.get("raw_agreement") == "NUANCED_BY_RAW")
        usable = sum(1 for x in items if "USABLE" in str(x.get("source_quality_state", "")))
        keep = sum(1 for x in items if x.get("b6_memory_candidate_state") == "B6_KEEP_CANDIDATE")
        families = Counter(str(x.get("memory_family", "UNKNOWN") or "UNKNOWN") for x in items)
        rows.append({
            "date": date,
            "film_cards": total,
            "confirmed_by_raw": confirmed,
            "nuanced_by_raw": nuanced,
            "source_quality_usable": usable,
            "keep_candidates": keep,
            "confirmed_share": round(confirmed / total, 4) if total else 0,
            "usable_share": round(usable / total, 4) if total else 0,
            "dominant_memory_family": families.most_common(1)[0][0] if families else "UNKNOWN",
        })
    return rows


def priority_score(card: Dict[str, Any]) -> float:
    score = safe_float(card.get("b6_memory_candidate_score"), 0.0)
    source_q = safe_float(card.get("source_quality_score"), 0.0)
    raw_bonus = 0.12 if card.get("raw_agreement") == "CONFIRMED_BY_RAW" else 0.04
    keep_bonus = 0.08 if card.get("b6_memory_candidate_state") == "B6_KEEP_CANDIDATE" else 0.02
    range_bonus = min(abs(safe_float(card.get("raw_range_pips"), 0.0)) / 30.0, 0.08)
    tick_bonus = min(safe_float(card.get("raw_tick_count"), 0.0) / 5000.0, 0.05)
    return round(score * 0.52 + source_q * 0.23 + raw_bonus + keep_bonus + range_bonus + tick_bonus, 6)


def top_memory_scenes(cards: List[Dict[str, Any]], limit: int = 25) -> List[Dict[str, Any]]:
    ranked = sorted(cards, key=priority_score, reverse=True)
    rows = []
    for card in ranked[:limit]:
        rows.append({
            "film_id": card.get("film_id", ""),
            "date": card.get("date", ""),
            "session": card.get("session", ""),
            "memory_family": card.get("memory_family", ""),
            "moment_type": card.get("moment_type", ""),
            "label_fr": card.get("label_fr", ""),
            "raw_agreement": card.get("raw_agreement", ""),
            "source_quality_state": card.get("source_quality_state", ""),
            "raw_texture_role": card.get("raw_texture_role", ""),
            "priority_score": priority_score(card),
            "why_keep_for_memory": card.get("why_keep_for_memory", ""),
            "technical_limits": card.get("limits", ""),
        })
    return rows


def technical_limit_rows(cards: List[Dict[str, Any]], limit: int = 80) -> List[Dict[str, Any]]:
    rows = []
    for card in cards:
        limits = str(card.get("limits", ""))
        state = str(card.get("source_quality_state", ""))
        verdict = str(card.get("raw_agreement", ""))
        source_mode = str(card.get("source_mode", ""))
        cap = safe_float(card.get("confidence_cap"), 0.0)
        flags = []
        if verdict == "NUANCED_BY_RAW": flags.append("RAW_NUANCES_PROXY")
        if "WEAK" in state or "LOW" in state: flags.append("SOURCE_QUALITY_WEAK")
        if "PROXY" in source_mode or "proxy" in limits.lower(): flags.append("PROXY_READING")
        if cap and cap <= 0.25: flags.append("LOW_CONFIDENCE_CAP")
        all_text = " ".join(str(card.get(k, "")) for k in ["base", "reaction", "projection", "judgment", "limits"]).lower()
        if "retest" not in all_text: flags.append("RETEST_NOT_EXPLICIT_IN_FILM_CARD")
        if "not full footprint" in all_text or "footprint" in all_text: flags.append("NOT_FULL_FOOTPRINT")
        if flags:
            rows.append({
                "film_id": card.get("film_id", ""),
                "date": card.get("date", ""),
                "session": card.get("session", ""),
                "memory_family": card.get("memory_family", ""),
                "raw_agreement": verdict,
                "source_quality_state": state,
                "source_mode": source_mode,
                "confidence_cap": card.get("confidence_cap", ""),
                "technical_flags": ";".join(flags),
                "limits": limits,
            })
    return rows[:limit]


def false_positive_summary(fp: Dict[str, Any] | None) -> Dict[str, Any]:
    if not fp:
        return {
            "available": False,
            "matches_reviewed": 0,
            "state_counts": {},
            "flag_counts": {},
            "primary_message_fr": "T0117 context not provided.",
        }
    summary = fp.get("false_positive_context_summary", {}) or {}
    return {
        "available": True,
        "input_query_id": fp.get("input_query_id", ""),
        "matches_reviewed": summary.get("matches_reviewed", 0),
        "state_counts": summary.get("state_counts", {}),
        "flag_counts": summary.get("flag_counts", {}),
        "primary_message_fr": summary.get("primary_message_fr", ""),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: List[Dict[str, Any]], columns: List[str], max_rows: int = 12) -> str:
    if not rows:
        return "Aucune ligne."
    selected = rows[:max_rows]
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, sep]
    for row in selected:
        vals = []
        for col in columns:
            val = str(row.get(col, ""))
            val = val.replace("\n", " ").replace("|", "/")
            if len(val) > 90:
                val = val[:87] + "..."
            vals.append(val)
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def generate_markdown(summary: Dict[str, Any]) -> str:
    family_rows = summary["family_rows"]
    date_rows = summary["date_rows"]
    priority_rows = summary["priority_scenes"]
    tech_rows = summary["technical_limits"]
    fp = summary["false_positive_summary"]
    lines = []
    lines.append("# T0118 — B6 Human Terrain Synthesis V0")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("B6 ne prédit pas. B6 compare des films. T0118 synthétise ce que la bibliothèque montre comme terrain humain exploitable.")
    lines.append("")
    lines.append("Phrase de cap : **PowerFlow doit apprendre des transitions de scène, pas des directions isolées.**")
    lines.append("")
    lines.append(f"- Cartes film actives lues : **{summary['total_cards']}**")
    lines.append(f"- Familles mémoire actives : **{len(family_rows)}**")
    lines.append(f"- Jours couverts : **{len(date_rows)}**")
    lines.append(f"- Contextes de faux positif T0117 disponibles : **{fp.get('available')}**")
    lines.append("")
    lines.append("## Sources et provenance")
    lines.append("")
    lines.append("Lecture read-only depuis `B6_FILM_CARDS_V0.json`, avec contexte T0117 optionnel depuis `B6_FALSE_POSITIVE_CONTEXT_V0.json`.")
    lines.append("Aucune écriture `powerflow.db`. Aucune écriture `tick_archive.db`. Aucun dashboard. Aucun Telegram.")
    lines.append("")
    lines.append("## Counts globaux")
    lines.append("")
    lines.append("### Familles mémoire")
    lines.append(md_table(family_rows, ["memory_family", "count", "share"]))
    lines.append("")
    lines.append("### Accord raw")
    lines.append(md_table(summary["raw_agreement_rows"], ["raw_agreement", "count", "share"]))
    lines.append("")
    lines.append("### Source quality")
    lines.append(md_table(summary["source_quality_rows"], ["source_quality_state", "count", "share"]))
    lines.append("")
    lines.append("## Counts par date")
    lines.append("")
    lines.append(md_table(date_rows, ["date", "film_cards", "confirmed_by_raw", "nuanced_by_raw", "source_quality_usable", "dominant_memory_family"], 20))
    lines.append("")
    lines.append("## Films les plus utiles pour B6")
    lines.append("")
    lines.append(md_table(priority_rows, ["film_id", "date", "session", "memory_family", "label_fr", "raw_agreement", "source_quality_state", "priority_score"], 20))
    lines.append("")
    lines.append("## Ce qui revient dans le terrain")
    lines.append("")
    for fam in family_rows:
        lines.append(f"- **{fam['memory_family']}** : {fam['count']} cartes, part {fam['share']}. Lecture : famille suffisamment représentée pour comparaison B6, pas pour prédiction.")
    lines.append("")
    lines.append("## Où raw nuance fortement")
    lines.append("")
    nuanced = [r for r in tech_rows if "RAW_NUANCES_PROXY" in r.get("technical_flags", "")]
    lines.append(md_table(nuanced, ["film_id", "date", "session", "memory_family", "raw_agreement", "technical_flags"], 15))
    lines.append("")
    lines.append("## Où le proxy reste faible ou partiel")
    lines.append("")
    proxy = [r for r in tech_rows if "PROXY_READING" in r.get("technical_flags", "") or "LOW_CONFIDENCE_CAP" in r.get("technical_flags", "") or "NOT_FULL_FOOTPRINT" in r.get("technical_flags", "")]
    lines.append(md_table(proxy, ["film_id", "date", "session", "memory_family", "source_mode", "confidence_cap", "technical_flags"], 15))
    lines.append("")
    lines.append("## Où le retest reste invisible")
    lines.append("")
    retest = [r for r in tech_rows if "RETEST_NOT_EXPLICIT_IN_FILM_CARD" in r.get("technical_flags", "")]
    lines.append(md_table(retest, ["film_id", "date", "session", "memory_family", "technical_flags"], 15))
    lines.append("")
    lines.append("## Lecture T0117 — pièges de similarité")
    lines.append("")
    if fp.get("available"):
        lines.append(f"- Query analysée : `{fp.get('input_query_id')}`")
        lines.append(f"- Matches relus : **{fp.get('matches_reviewed')}**")
        lines.append(f"- États : `{fp.get('state_counts')}`")
        lines.append(f"- Flags : `{fp.get('flag_counts')}`")
        lines.append(f"- Message : {fp.get('primary_message_fr')}")
    else:
        lines.append("Aucun contexte T0117 fourni.")
    lines.append("")
    lines.append("## Ce que B6 peut comparer")
    lines.append("")
    lines.append("B6 peut comparer : famille mémoire, session, source_family, source_mode, data_visibility, raw agreement, source quality, texture raw, base/reaction/projection/judgment et limites techniques.")
    lines.append("")
    lines.append("## Ce que B6 ne doit pas conclure")
    lines.append("")
    lines.append("B6 ne doit pas conclure qu’un film proche va se répéter. Un score de similarité n’est pas une probabilité. Une famille mémoire n’est pas un ordre. Une nuance raw n’est pas une confirmation.")
    lines.append("")
    lines.append("## Prochaine brique recommandée")
    lines.append("")
    lines.append("T0119 — B6 Memory Brief V0 : transformer T0115 + T0117 + T0118 en brief trader lisible, encore read-only, sans dashboard/Telegram, avant intégration Reality Board.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build T0118 B6 Human Terrain Synthesis V0")
    parser.add_argument("--film-cards-json", required=True, type=Path)
    parser.add_argument("--false-positive-json", type=Path, default=None)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    cards = load_cards(args.film_cards_json)
    if not cards:
        raise SystemExit("No active film cards loaded")
    fp = load_false_positive(args.false_positive_json)

    family_rows = counter_rows(count_by(cards, "memory_family"), "memory_family")
    raw_rows = counter_rows(count_by(cards, "raw_agreement"), "raw_agreement")
    quality_rows = counter_rows(count_by(cards, "source_quality_state"), "source_quality_state")
    session_rows = counter_rows(count_by(cards, "session"), "session")
    source_rows = counter_rows(count_by(cards, "source_family"), "source_family")
    date_rows = compute_date_rows(cards)
    priority_rows = top_memory_scenes(cards)
    tech_rows = technical_limit_rows(cards)
    fp_summary = false_positive_summary(fp)

    summary = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "policy": "HUMAN_TERRAIN_SYNTHESIS_READ_ONLY_NO_PREDICTION_V0",
        "doctrine": DOCTRINE,
        "input_film_cards_json": str(args.film_cards_json),
        "input_false_positive_json": str(args.false_positive_json) if args.false_positive_json else "",
        "total_cards": len(cards),
        "family_rows": family_rows,
        "raw_agreement_rows": raw_rows,
        "source_quality_rows": quality_rows,
        "session_rows": session_rows,
        "source_family_rows": source_rows,
        "date_rows": date_rows,
        "priority_scenes": priority_rows,
        "technical_limits": tech_rows,
        "false_positive_summary": fp_summary,
        "integrity": {
            "low_trust_in_active_cards": any("LOW_TRUST" in str(c.get("b6_memory_candidate_state", "")) for c in cards),
            "raw_unavailable_in_active_cards": any(str(c.get("raw_agreement", "")) == "RAW_UNAVAILABLE" for c in cards),
            "db_write": False,
            "dashboard": False,
            "telegram": False,
            "buy_sell": False,
            "probability_of_success": False,
        },
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "B6_HUMAN_TERRAIN_SYNTHESIS_V0.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "B6_HUMAN_TERRAIN_SYNTHESIS_V0.md").write_text(generate_markdown(summary), encoding="utf-8")
    write_csv(out / "B6_HUMAN_TERRAIN_FAMILY_COUNTS_V0.csv", family_rows)
    write_csv(out / "B6_HUMAN_TERRAIN_DATE_COUNTS_V0.csv", date_rows)
    write_csv(out / "B6_HUMAN_TERRAIN_PRIORITY_SCENES_V0.csv", priority_rows)
    write_csv(out / "B6_HUMAN_TERRAIN_TECHNICAL_LIMITS_V0.csv", tech_rows)
    fp_rows = []
    for key, val in fp_summary.get("flag_counts", {}).items():
        fp_rows.append({"flag": key, "count": val})
    write_csv(out / "B6_HUMAN_TERRAIN_FALSE_POSITIVE_FLAGS_V0.csv", fp_rows)

    manifest = {
        "version": VERSION,
        "generated_at_utc": summary["generated_at_utc"],
        "input_cards": len(cards),
        "outputs": [
            "B6_HUMAN_TERRAIN_SYNTHESIS_V0.json",
            "B6_HUMAN_TERRAIN_SYNTHESIS_V0.md",
            "B6_HUMAN_TERRAIN_FAMILY_COUNTS_V0.csv",
            "B6_HUMAN_TERRAIN_DATE_COUNTS_V0.csv",
            "B6_HUMAN_TERRAIN_PRIORITY_SCENES_V0.csv",
            "B6_HUMAN_TERRAIN_TECHNICAL_LIMITS_V0.csv",
            "B6_HUMAN_TERRAIN_FALSE_POSITIVE_FLAGS_V0.csv",
            "B6_HUMAN_TERRAIN_SYNTHESIS_V0_MANIFEST.json",
            "B6_HUMAN_TERRAIN_SYNTHESIS_V0.zip",
        ],
        "integrity": summary["integrity"],
    }
    (out / "B6_HUMAN_TERRAIN_SYNTHESIS_V0_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = out / "B6_HUMAN_TERRAIN_SYNTHESIS_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in manifest["outputs"]:
            if name == "B6_HUMAN_TERRAIN_SYNTHESIS_V0.zip":
                continue
            z.write(out / name, arcname=name)

    print(json.dumps({
        "version": VERSION,
        "input_cards": len(cards),
        "families": {r["memory_family"]: r["count"] for r in family_rows},
        "days": len(date_rows),
        "priority_scenes": len(priority_rows),
        "technical_limit_rows": len(tech_rows),
        "false_positive_context_available": fp_summary.get("available"),
        "output_dir": str(out),
        "zip": str(zip_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
