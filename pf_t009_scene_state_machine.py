
"""T0153 - B9 Scene State Machine V0.

Read-only state machine for enriched B9/T009 moments.
It does not trade, predict, write DB, trigger dashboard, or send Telegram.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0153_B9_SCENE_STATE_MACHINE_V0"
FORBIDDEN_TERMS = ["BUY", "SELL", "TAKE PROFIT", "STOP LOSS", "WIN RATE", "SUCCESS RATE", "PROBABILITY OF SUCCESS"]

REQUIRED_FIELDS = [
    "b9_scene_state_machine_version",
    "b9_scene_state",
    "b9_scene_transition_from",
    "b9_scene_transition_to",
    "b9_scene_state_flags",
    "b9_scene_state_reason_fr",
    "b9_next_observation_focus_fr",
    "b9_state_machine_limits",
]

STATE_ORDER = [
    "SCENE_BUILDING",
    "SCENE_TESTING",
    "SCENE_ACCEPTED",
    "SCENE_REJECTED",
    "SCENE_DECONSTRUCTING",
    "SCENE_REBUILDING",
    "SCENE_MEMORY_SHIFTED",
    "SCENE_BLOCKED_RAW_UNAVAILABLE",
    "SCENE_REVIEW_REQUIRED",
]


def _txt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_txt(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_txt(v)}" for k, v in value.items())
    return str(value)


def _upper(value: Any) -> str:
    return _txt(value).upper()


def _contains_any(haystack: str, needles: Iterable[str]) -> bool:
    h = haystack.upper()
    return any(n.upper() in h for n in needles)


def _get(moment: Dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in moment and moment.get(name) not in (None, ""):
            return moment.get(name)
    return default


def _stable_id(moment: Dict[str, Any], idx: int) -> str:
    base = "|".join([
        _txt(_get(moment, "date", default="")),
        _txt(_get(moment, "time_start", "time_start_real", "start_time", default="")),
        _txt(_get(moment, "time_end", "time_end_real", "end_time", default="")),
        _txt(_get(moment, "label_fr", "moment_type", default="")),
        str(idx),
    ])
    return "B9SS_" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:12].upper()


def _source_raw_unavailable(moment: Dict[str, Any]) -> bool:
    blob = _upper({k: v for k, v in moment.items() if "source" in k.lower() or "raw" in k.lower() or "quality" in k.lower() or "visibility" in k.lower()})
    return "RAW_UNAVAILABLE" in blob or "SOURCE_RAW_UNAVAILABLE_REJECTED" in blob or "MEMORY_REJECTED_RAW_UNAVAILABLE" in blob


def classify_scene_state(moment: Dict[str, Any], previous_state: str = "SCENE_START") -> Tuple[str, List[str], str, str]:
    """Return state, flags, reason_fr, next_focus_fr."""
    blob = _upper(moment)
    role = _upper(_get(moment, "b9_scene_role", "scene_role", "role", default=""))
    verdict = _upper(_get(moment, "b9_price_verdict_state", "price_verdict", default=""))
    node = _upper(_get(moment, "node_role", "b9_terrain_node_role", default=""))
    retest = _upper(_get(moment, "retest_result", "b9_native_retest_judgment", "b9_retest_result", default=""))
    memory = _upper(_get(moment, "b9_memory_confidence_ladder_state", "b9_memory_confidence_state", "memory_confidence_state", "memory_confidence_ladder", default=""))
    fp_state = _upper(_get(moment, "b9_memory_false_positive_state", "false_positive_context_state", "b6_false_positive_context_state", default=""))

    flags: List[str] = []
    if _source_raw_unavailable(moment):
        flags.extend(["RAW_UNAVAILABLE", "MEMORY_NOT_ACTIVE"])
        return (
            "SCENE_BLOCKED_RAW_UNAVAILABLE",
            flags,
            "La scène porte une source RAW_UNAVAILABLE ou une mémoire rejetée ; B9 la garde en trace d'audit mais ne l'active pas comme scène comparable.",
            "Chercher une scène avec raw visible, source quality lisible ou proxy explicitement qualifié.",
        )

    # Explicit accepted / rejected verdicts first.
    if "FAILED_REINTEGRATION" in verdict or "FAILED_REINTEGRATION" in role or "FAILED_REINTEGRATION" in node:
        flags.append("FAILED_REINTEGRATION")
        return (
            "SCENE_REJECTED",
            flags,
            "La réintégration échoue : la zone est testée mais ne récupère pas son ancien rôle. B9 lit un rejet de scène, pas une direction à exécuter.",
            "Surveiller si le rejet produit un déplacement durable de mémoire ou seulement une respiration.",
        )

    if "REJECTED" in verdict or "RETEST_FAILED" in role or "RETEST_FAILED" in node or "RETEST_FAILED" in retest or "HIGH_REJECTION" in role:
        flags.append("RETEST_OR_REJECTION")
        return (
            "SCENE_REJECTED",
            flags,
            "Le retest ou le rejet juge défavorablement la zone. La scène bascule vers une lecture de refus / non-acceptation.",
            "Observer si le centre quitte la zone ou si le prix reconstruit une base de réaction.",
        )

    if "ACCEPTED" in verdict or "RETEST_ACCEPTED" in retest or "LOWER_ZONE_DEFENDED" in verdict or "LOW_ZONE_DEFENDED" in role or "PULLBACK_ABSORBED" in verdict or "PULLBACK_ABSORBED" in role:
        if "PULLBACK_ABSORBED" in blob or "LOWER_ZONE_DEFENDED" in blob or "LOW_ZONE_DEFENDED" in blob:
            flags.append("ZONE_DEFENDED_OR_PULLBACK_ABSORBED")
            return (
                "SCENE_ACCEPTED",
                flags,
                "La zone répond au test : le pullback est absorbé ou la zone basse reste défendue. B9 marque une acceptation comportementale.",
                "Vérifier si l'acceptation déplace réellement la mémoire ou reste locale.",
            )
        flags.append("ACCEPTED_BY_PRICE_OR_RETEST")
        return (
            "SCENE_ACCEPTED",
            flags,
            "Le prix ou le retest accepte la zone. La scène devient lisible, sous réserve de source quality et de mémoire comparable.",
            "Comparer avec B6 sans transformer l'acceptation en répétition certaine.",
        )

    # Movement and memory shift.
    if "CENTER_MIGRATION" in role or "CENTER_MIGRATION" in node or "MEMORY_SHIFT" in role or "MEMORY_SHIFT" in blob:
        flags.append("CENTER_OR_MEMORY_SHIFT")
        return (
            "SCENE_MEMORY_SHIFTED",
            flags,
            "Le centre de gravité ou la mémoire active se déplace. B9 lit une scène de migration plutôt qu'un simple mouvement directionnel.",
            "Contrôler si la zone déplacée est retestée, défendue ou consommée.",
        )

    if "PROGRESSIVE" in role or "PROGRESSIVE" in node or "PROGRESSIVE_WAVE" in blob:
        flags.append("PROGRESSIVE_WAVE")
        return (
            "SCENE_REBUILDING" if previous_state in {"SCENE_REJECTED", "SCENE_DECONSTRUCTING"} else "SCENE_BUILDING",
            flags,
            "Le flux construit une vague progressive. B9 lit une construction/reconstruction de scène si le progrès déplace la mémoire.",
            "Vérifier le retest, le chemin interne du centre et la similarité B6 alignée sur cette scène.",
        )

    if "CORRECTIVE" in role or "BREATH" in role or "NO_PROGRESS" in role:
        flags.append("CORRECTIVE_BREATH")
        return (
            "SCENE_DECONSTRUCTING",
            flags,
            "Le flux respire ou revient sans progrès durable. B9 lit une déconstruction locale ou une correction, pas une nouvelle acceptation.",
            "Observer si la respiration devient pullback absorbé ou réintégration échouée.",
        )

    if "ABSORPTION" in role or "SHELF" in role or "EFFORT_WITHOUT_RESULT" in role or "FRICTION" in role:
        flags.append("FRICTION_OR_ABSORPTION")
        return (
            "SCENE_TESTING",
            flags,
            "La scène travaille une friction : effort visible, résultat limité ou palier d'absorption. Le marché teste la zone.",
            "Distinguer absorption bloquante et absorption qui accompagne une migration de centre.",
        )

    # Memory false-positive HIGH remains comparable, not absent.
    if "B6_FALSE_POSITIVE_CONTEXT_HIGH" in fp_state or "MEMORY_FP_HIGH" in fp_state or "HIGH" in fp_state:
        flags.append("MEMORY_COMPARABLE_WITH_HIGH_FALSE_POSITIVE_CONTEXT")
        return (
            "SCENE_REVIEW_REQUIRED",
            flags,
            "Une mémoire proche existe mais le piège de similarité est fort. B9 garde la comparaison, sans la traiter comme répétition.",
            "Afficher les différences : source, session, retest, chemin interne et famille mémoire.",
        )

    if "PENDING" in verdict or "PENDING" in retest:
        flags.append("PENDING_VERDICT")
        return (
            "SCENE_TESTING",
            flags,
            "La scène reste en attente de jugement. Le prix n'a pas encore donné de verdict exploitable.",
            "Attendre le retest ou la réaction de zone sans censurer l'alerte précoce.",
        )

    flags.append("INSUFFICIENT_SCENE_EVIDENCE")
    return (
        "SCENE_REVIEW_REQUIRED",
        flags,
        "Les preuves disponibles ne suffisent pas à cristalliser un état de scène robuste. B9 garde la scène en revue technique.",
        "Compléter avec source quality, retest, verdict prix, node terrain et mémoire B6 alignée.",
    )


def enrich_sequence_summary_with_scene_state_machine(summary: Dict[str, Any]) -> Dict[str, Any]:
    enriched = deepcopy(summary)
    moments = enriched.get("moments") or enriched.get("sequence_moments") or enriched.get("items") or []
    if not isinstance(moments, list):
        moments = []
    previous_state = "SCENE_START"
    transitions: List[Dict[str, Any]] = []
    state_counts: Dict[str, int] = {}
    for idx, moment in enumerate(moments):
        if not isinstance(moment, dict):
            continue
        state, flags, reason_fr, focus_fr = classify_scene_state(moment, previous_state)
        transition_from = previous_state
        transition_to = state
        scene_id = _get(moment, "scene_id", "moment_id", "candidate_id", default="") or _stable_id(moment, idx)
        moment.update({
            "b9_scene_state_machine_version": VERSION,
            "b9_scene_state": state,
            "b9_scene_transition_from": transition_from,
            "b9_scene_transition_to": transition_to,
            "b9_scene_state_flags": flags,
            "b9_scene_state_reason_fr": reason_fr,
            "b9_next_observation_focus_fr": focus_fr,
            "b9_state_machine_limits": [
                "Etat de scène read-only, pas une décision d'exécution.",
                "Une scène proxy reste proxy et doit garder sa source quality visible.",
                "Une mémoire B6 comparable n'est pas une répétition certaine.",
            ],
        })
        transitions.append({
            "index": idx,
            "scene_id": scene_id,
            "from": transition_from,
            "to": transition_to,
            "flags": flags,
        })
        state_counts[state] = state_counts.get(state, 0) + 1
        previous_state = state
    enriched["moments"] = moments
    enriched["b9_scene_state_machine_summary"] = {
        "version": VERSION,
        "moments": len([m for m in moments if isinstance(m, dict)]),
        "state_counts": state_counts,
        "transition_count": len(transitions),
        "transitions": transitions,
        "read_only": True,
        "no_db_write": True,
        "no_dashboard": True,
        "no_telegram": True,
        "no_trade_decision": True,
    }
    return enriched


def validate_enriched_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    moments = summary.get("moments") or []
    missing: Dict[str, int] = {}
    forbidden_hits: List[Dict[str, str]] = []
    raw_unavailable_allowed = 0
    state_counts: Dict[str, int] = {}
    for idx, moment in enumerate(moments):
        if not isinstance(moment, dict):
            continue
        for field in REQUIRED_FIELDS:
            if field not in moment:
                missing[field] = missing.get(field, 0) + 1
        state = _txt(moment.get("b9_scene_state", ""))
        if state:
            state_counts[state] = state_counts.get(state, 0) + 1
        blob = _txt(moment)
        for term in FORBIDDEN_TERMS:
            if term in blob.upper():
                forbidden_hits.append({"index": str(idx), "term": term})
        if _source_raw_unavailable(moment) and state != "SCENE_BLOCKED_RAW_UNAVAILABLE":
            raw_unavailable_allowed += 1
    return {
        "moments": len([m for m in moments if isinstance(m, dict)]),
        "state_counts": state_counts,
        "missing_required_field_counts": missing,
        "forbidden_language_hits": forbidden_hits,
        "raw_unavailable_allowed_count": raw_unavailable_allowed,
    }


def write_outputs(enriched: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = validate_enriched_summary(enriched)
    summary = enriched.get("b9_scene_state_machine_summary", {})
    result = {
        "version": VERSION,
        **validation,
        "transition_count": summary.get("transition_count", 0),
        "read_only": True,
    }
    json_path = output_dir / "B9_SCENE_STATE_MACHINE_V0.json"
    enriched_path = output_dir / "B9_SCENE_STATE_MACHINE_ENRICHED_SUMMARY_V0.json"
    csv_path = output_dir / "B9_SCENE_STATE_MACHINE_ROWS_V0.csv"
    counts_path = output_dir / "B9_SCENE_STATE_MACHINE_COUNTS_V0.csv"
    md_path = output_dir / "B9_SCENE_STATE_MACHINE_V0.md"
    manifest_path = output_dir / "B9_SCENE_STATE_MACHINE_MANIFEST.json"

    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    enriched_path.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for i, m in enumerate(enriched.get("moments", [])):
        if not isinstance(m, dict):
            continue
        rows.append({
            "index": i,
            "time_start": _get(m, "time_start", "time_start_real", default=""),
            "time_end": _get(m, "time_end", "time_end_real", default=""),
            "label_fr": _get(m, "label_fr", default=""),
            "scene_role": _get(m, "b9_scene_role", "scene_role", default=""),
            "price_verdict": _get(m, "b9_price_verdict_state", "price_verdict", default=""),
            "scene_state": m.get("b9_scene_state", ""),
            "transition_from": m.get("b9_scene_transition_from", ""),
            "transition_to": m.get("b9_scene_transition_to", ""),
            "flags": ";".join(m.get("b9_scene_state_flags", [])),
            "reason_fr": m.get("b9_scene_state_reason_fr", ""),
        })
    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["index"])
        writer.writeheader()
        writer.writerows(rows)
    with counts_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scene_state", "count"])
        writer.writeheader()
        for k, v in sorted(result["state_counts"].items()):
            writer.writerow({"scene_state": k, "count": v})

    md = [
        "# B9 Scene State Machine V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal. B9 cherche la trace laissée par l'effort.",
        "La machine d'état qualifie où se trouve la scène : construction, test, acceptation, rejet, déconstruction, reconstruction ou mémoire déplacée.",
        "",
        "## Counts",
        "",
        f"- Moments : {result['moments']}",
        f"- Transitions : {result['transition_count']}",
        f"- Forbidden language hits : {len(result['forbidden_language_hits'])}",
        f"- RAW_UNAVAILABLE allowed count : {result['raw_unavailable_allowed_count']}",
        "",
        "## États",
        "",
    ]
    for k, v in sorted(result["state_counts"].items()):
        md.append(f"- `{k}` : {v}")
    md.extend(["", "## Moments", ""])
    for r in rows:
        md.extend([
            f"### {r['time_start']} → {r['time_end']} — {r['label_fr']}",
            "",
            f"- État : `{r['scene_state']}`",
            f"- Transition : `{r['transition_from']}` → `{r['transition_to']}`",
            f"- Rôle : `{r['scene_role']}`",
            f"- Verdict prix : `{r['price_verdict']}`",
            f"- Lecture : {r['reason_fr']}",
            "",
        ])
    md.extend([
        "## Limites techniques",
        "",
        "- Read-only.",
        "- Aucune écriture powerflow.db.",
        "- Aucune écriture tick_archive.db.",
        "- Aucun dashboard.",
        "- Aucun Telegram.",
        "- Aucun ordre directionnel.",
        "- Aucun taux de réussite.",
        "- Une mémoire B6 comparable n'est pas une répétition certaine.",
    ])
    md_path.write_text("\n".join(md), encoding="utf-8")
    manifest = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": [p.name for p in [md_path, json_path, enriched_path, csv_path, counts_path]],
        "read_only": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    zip_path = output_dir / "B9_SCENE_STATE_MACHINE_V0.zip"
    with __import__('zipfile').ZipFile(zip_path, "w", __import__('zipfile').ZIP_DEFLATED) as z:
        for p in [md_path, json_path, enriched_path, csv_path, counts_path, manifest_path]:
            z.write(p, p.name)
    result["zip"] = str(zip_path)
    return result
