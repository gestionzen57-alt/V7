#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T0159 — B9 French Event Display Contract V0.

Read-only builder for the French trader display contract.

Purpose:
- The engine speaks enums.
- The trader reads French.
- Translation clarifies B9/B6/raw states without creating decisions or signals.

Outputs:
- outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json
- outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.md
- outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.csv
- outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_EXAMPLES_V0.json
- outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_MANIFEST.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bachat\b",
    r"\bvente\b",
    r"\bentre\s+maintenant\b",
    r"\bprobabilit[ée]\s+de\s+r[ée]ussite\b",
    r"\bsignal\s+gagnant\b",
    r"\bconseil\s+financier\b",
]

DOCTRINE = (
    "Le moteur parle enum. Le trader lit français. "
    "La traduction clarifie la lecture, elle ne déclenche aucune décision."
)


def entry(enum: str, category: str, short_fr: str, display_fr: str, limit_fr: str = "", severity: str = "INFO") -> dict[str, Any]:
    return {
        "enum": enum,
        "category": category,
        "short_fr": short_fr,
        "display_fr": display_fr,
        "limit_fr": limit_fr,
        "severity": severity,
        "decision_language_allowed": False,
    }


def build_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    # B9 flow states
    entries.extend([
        entry("FLOW_DIRECTIONAL_DISPLACEMENT", "b9_flow_state", "Déplacement directionnel", "Le flux montre un déplacement directionnel lisible.", "Lecture descriptive uniquement, sans ordre d’action."),
        entry("FLOW_ROTATIONAL", "b9_flow_state", "Rotation", "Le marché tourne autour d’une zone sans décision nette.", "La rotation peut masquer un piège de surinterprétation."),
        entry("FLOW_BALANCED_AUCTION", "b9_flow_state", "Enchère équilibrée", "L’enchère reste équilibrée, sans pression dominante nette.", "La scène demande patience et observation."),
        entry("FLOW_MIXED", "b9_flow_state", "Flux mixte", "Le flux mélange plusieurs comportements et ne donne pas une lecture unique.", "Ne pas durcir la lecture en vérité directionnelle."),
        entry("FLOW_UNSTABLE_QUOTE_TEXTURE", "b9_flow_state", "Texture instable", "La texture de cotation est instable et limite la lecture.", "La qualité de donnée réduit le poids de l’interprétation.", "WARN"),
        entry("FLOW_GAPPY_LIMIT", "b9_flow_state", "Limite par gaps", "Des gaps ou discontinuités limitent la lecture B9.", "Ne pas interpréter la scène comme propre.", "WARN"),
        entry("FLOW_NOT_VISIBLE", "b9_flow_state", "Flux non visible", "Le flux n’est pas suffisamment visible dans la source.", "Absence de preuve, pas preuve d’absence.", "WARN"),
    ])

    # Retest source states
    entries.extend([
        entry("RETEST_OUTCOME_ACCEPTED", "b9_retest_source_state", "Retest accepté", "Le retest semble accepté par la zone observée.", "Lecture conditionnée par la source et le contexte."),
        entry("RETEST_OUTCOME_REJECTED", "b9_retest_source_state", "Retest rejeté", "Le retest semble rejeté par la zone observée.", "Ne pas transformer ce rejet en instruction d’action."),
        entry("RETEST_OUTCOME_PENDING", "b9_retest_source_state", "Retest en attente", "Le retest reste en attente de confirmation comportementale.", "La scène n’est pas terminée."),
        entry("RETEST_OUTCOME_NOT_VISIBLE", "b9_retest_source_state", "Retest non visible", "La source ne permet pas de lire le résultat du retest.", "Ne pas inventer de conclusion retest.", "WARN"),
        entry("RETEST_SOURCE_FIELDS_EXPLICIT", "b9_retest_source_state", "Source retest explicite", "Les champs retest sont explicitement visibles dans la source.", "Le contexte reste nécessaire."),
        entry("RETEST_SOURCE_FIELDS_PARTIAL", "b9_retest_source_state", "Source retest partielle", "Les champs retest sont partiellement visibles.", "Lecture utile mais incomplète.", "WARN"),
        entry("RETEST_SOURCE_FIELDS_INFERRED", "b9_retest_source_state", "Source retest inférée", "Le retest est inféré depuis des indices indirects.", "À traiter comme hypothèse, pas comme preuve directe.", "WARN"),
        entry("RETEST_SOURCE_FIELDS_NOT_VISIBLE", "b9_retest_source_state", "Source retest non visible", "Aucune preuve retest exploitable n’est visible.", "La lecture retest doit rester ouverte.", "WARN"),
    ])

    # Raw texture states
    entries.extend([
        entry("RAW_PROGRESS_CONFIRMED", "raw_texture_state", "Progression raw confirmée", "La texture raw confirme une progression.", "La confirmation reste descriptive, pas décisionnelle."),
        entry("RAW_ROTATION_CONFIRMED", "raw_texture_state", "Rotation raw confirmée", "La texture raw confirme une rotation.", "La rotation peut invalider une lecture trop directionnelle."),
        entry("RAW_FRICTION_CONFIRMED", "raw_texture_state", "Friction raw confirmée", "La texture raw confirme une friction locale.", "La friction ne suffit pas à conclure seule."),
        entry("RAW_UNAVAILABLE", "raw_texture_state", "Raw indisponible", "La source raw n’est pas disponible pour cette scène.", "Ne pas utiliser comme preuve positive.", "WARN"),
        entry("RAW_PARTIAL", "raw_texture_state", "Raw partiel", "La couverture raw est partielle.", "Lecture possible mais limitée.", "WARN"),
        entry("RAW_FULL", "raw_texture_state", "Raw complet", "La couverture raw est disponible sur toute la fenêtre.", "La provenance reste à conserver."),
        entry("CONFIRMED_BY_RAW", "raw_texture_state", "Confirmé par raw", "La scène proxy est confirmée par la texture raw.", "Confirmation d’observation, pas signal."),
        entry("NUANCED_BY_RAW", "raw_texture_state", "Nuancé par raw", "La texture raw nuance la scène proxy.", "La nuance doit rester visible dans l’affichage.", "WARN"),
    ])

    # Source quality states
    entries.extend([
        entry("SOURCE_QUALITY_STRONG_FOR_PROXY", "source_quality_state", "Source forte pour proxy", "La source proxy est robuste pour cette lecture.", "La source reste proxy et doit être affichée comme telle."),
        entry("SOURCE_QUALITY_USABLE_WITH_LIMITS", "source_quality_state", "Source utilisable avec limites", "La source est exploitable mais avec limites techniques.", "Les limites doivent rester visibles.", "WARN"),
        entry("SOURCE_QUALITY_WEAK_REVIEW", "source_quality_state", "Source faible à revoir", "La source est faible et demande revue.", "Ne pas exploiter comme mémoire forte.", "WARN"),
        entry("SOURCE_QUALITY_RAW_MISSING", "source_quality_state", "Raw manquant", "La qualité source est limitée par l’absence de raw.", "Exclure de la mémoire active si raw indisponible.", "WARN"),
        entry("PROXY_RAW_CONFIRMED_PROGRESS", "source_quality_state", "Proxy/raw progression alignée", "Le proxy et le raw s’accordent sur une progression.", "Observation seulement."),
        entry("PROXY_RAW_NUANCED_ROTATION", "source_quality_state", "Proxy nuancé par rotation raw", "Le raw nuance le proxy par une lecture rotationnelle.", "Attention aux faux positifs directionnels.", "WARN"),
        entry("PROXY_DIRECTIONAL_NUANCED_BY_RAW_ROTATION", "source_quality_state", "Directionnel nuancé par rotation", "Une lecture directionnelle proxy est nuancée par une rotation raw.", "Ne pas durcir en lecture directionnelle.", "WARN"),
        entry("PROXY_RAW_UNAVAILABLE", "source_quality_state", "Proxy sans raw", "La scène proxy n’a pas de validation raw disponible.", "À exclure des candidats mémoire actifs.", "WARN"),
    ])

    # B6 memory candidate states
    entries.extend([
        entry("B6_KEEP_CANDIDATE", "b6_memory_state", "Candidat mémoire fort", "Cette scène peut être conservée comme candidate mémoire B6.", "B6 compare, il ne prédit pas."),
        entry("B6_REVIEW_CANDIDATE", "b6_memory_state", "Candidat mémoire à revoir", "Cette scène mérite une revue avant entrée mémoire.", "Garder la nuance et les limites."),
        entry("B6_LOW_TRUST_CANDIDATE", "b6_memory_state", "Candidat faible confiance", "Cette scène peut être gardée pour audit, pas pour mémoire active.", "Ne pas utiliser comme référence forte.", "WARN"),
        entry("B6_REJECT_RAW_UNAVAILABLE", "b6_memory_state", "Rejet mémoire raw absent", "La scène est rejetée pour mémoire active car le raw est indisponible.", "Rejet technique, pas jugement de marché.", "WARN"),
        entry("B6_REJECT_LOW_TRUST", "b6_memory_state", "Rejet mémoire faible confiance", "La scène est rejetée pour mémoire active par manque de confiance source.", "Conserver uniquement si audit nécessaire.", "WARN"),
    ])

    # Telegram / attention states
    entries.extend([
        entry("READY_FOR_HUMAN_REVIEW_NO_SEND", "telegram_attention_state", "Prêt pour revue humaine", "Le message est prêt pour validation humaine, sans envoi.", "Aucun envoi automatique."),
        entry("PENDING_HUMAN_REVIEW", "telegram_attention_state", "Validation humaine requise", "Le message attend une revue humaine.", "La décision reste humaine."),
        entry("DRY_RUN_PASS", "telegram_attention_state", "Dry-run validé", "Le dry-run est valide et aucun envoi n’a été tenté.", "Aucune activation Telegram réelle."),
        entry("DRY_RUN_BLOCKED", "telegram_attention_state", "Dry-run bloqué", "Le dry-run bloque le message avant toute sortie Telegram.", "Lire la raison du blocage.", "WARN"),
        entry("BLOCKED_FORBIDDEN_LANGUAGE", "telegram_attention_state", "Langage interdit bloqué", "Le message contient un langage interdit et doit être bloqué.", "Ne pas corriger par envoi manuel.", "ERROR"),
        entry("BLOCKED_MISSING_SECTIONS", "telegram_attention_state", "Sections manquantes", "Le message manque des sections obligatoires.", "Compléter la surface avant validation.", "WARN"),
    ])

    # Technical limits / unavailable data
    entries.extend([
        entry("RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED", "technical_limit_state", "Source reconstruite force snapshot", "La scène vient d’une reconstruction force_snapshots_v2.", "Ne pas présenter comme summary B9 récupéré."),
        entry("FORCE_SNAPSHOT_DERIVED", "technical_limit_state", "Scène proxy force snapshot", "La scène est dérivée d’un proxy force_snapshots_v2.", "Proxy explicite, pas footprint exact."),
        entry("RECOVERED_EXISTING_B9_SUMMARY", "technical_limit_state", "Summary B9 récupéré", "La scène provient d’un summary B9 existant récupéré.", "Conserver la provenance."),
        entry("ORIGINAL_AVAILABLE_SUMMARY", "technical_limit_state", "Summary original disponible", "La scène provient d’un summary original disponible.", "Conserver la source."),
        entry("DATA_VISIBILITY_LIMITED", "technical_limit_state", "Visibilité limitée", "La visibilité des données limite la lecture.", "Réduire le poids de la conclusion.", "WARN"),
        entry("SOURCE_TIMEFRAME_FALLBACK", "technical_limit_state", "Fallback timeframe", "La source utilise un timeframe de repli.", "La précision microfilm est réduite.", "WARN"),
        entry("COARSE_PROXY_TIMEFRAME", "technical_limit_state", "Proxy timeframe grossier", "Le proxy utilise un timeframe trop large pour une lecture fine.", "À éviter pour mémoire active fine.", "WARN"),
        entry("LIVE_SOURCE_UNQUALIFIED", "technical_limit_state", "Live non qualifié", "La source live n’est pas encore qualifiée par la texture raw.", "Ne pas envoyer en surface live décisionnelle.", "WARN"),
    ])

    return entries


def forbidden_hits(text: str) -> list[str]:
    hits = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text or "", flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def validate_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    hits = []
    for e in entries:
        joined = " ".join(str(e.get(k, "")) for k in ("enum", "short_fr", "display_fr", "limit_fr"))
        found = forbidden_hits(joined)
        if found:
            hits.append({"enum": e["enum"], "hits": found})
    categories = sorted(set(e["category"] for e in entries))
    return {
        "entry_count": len(entries),
        "category_count": len(categories),
        "categories": categories,
        "forbidden_language_hits": hits,
        "status": "READY" if not hits else "BLOCKED_FORBIDDEN_LANGUAGE",
    }


def write_csv(path: Path, entries: list[dict[str, Any]]) -> None:
    fields = ["enum", "category", "short_fr", "display_fr", "limit_fr", "severity", "decision_language_allowed"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)


def md_table(entries: list[dict[str, Any]]) -> str:
    fields = ["enum", "category", "short_fr", "display_fr", "limit_fr", "severity"]
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for e in entries:
        vals = []
        for f in fields:
            vals.append(str(e.get(f, "")).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    validation = payload["validation"]
    text = f"""# B9 French Event Display Contract V0

```text
version = {payload['version']}
status = {validation['status']}
entry_count = {validation['entry_count']}
category_count = {validation['category_count']}
```

## Doctrine

{payload['doctrine']}

## Catégories couvertes

{chr(10).join('- ' + c for c in validation['categories'])}

## Contrôle langage interdit

```text
forbidden_language_hits = {validation['forbidden_language_hits']}
```

## Contrat

{md_table(payload['entries'])}
"""
    path.write_text(text, encoding="utf-8")


def build_examples(entries: list[dict[str, Any]]) -> dict[str, Any]:
    examples = []
    for e in entries[:12]:
        examples.append({
            "input_enum": e["enum"],
            "display_fr": e["display_fr"],
            "limit_fr": e["limit_fr"],
        })
    return {
        "version": "B9_FRENCH_EVENT_DISPLAY_EXAMPLES_V0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "examples": examples,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build T0159 B9 French Event Display Contract")
    parser.add_argument("--output-dir", default="outputs/b9_french_event_display_contract_v0")
    parser.add_argument("--strict-exit", action="store_true")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    entries = build_entries()
    validation = validate_entries(entries)
    payload = {
        "version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "doctrine": DOCTRINE,
        "entries": entries,
        "validation": validation,
    }
    manifest = {
        "version": "B9_FRENCH_EVENT_DISPLAY_CONTRACT_MANIFEST",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json",
            "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.md",
            "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.csv",
            "B9_FRENCH_EVENT_DISPLAY_EXAMPLES_V0.json",
            "B9_FRENCH_EVENT_DISPLAY_CONTRACT_MANIFEST.json",
        ],
        "status": validation["status"],
        "entry_count": validation["entry_count"],
        "categories": validation["categories"],
    }

    json_path = out / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json"
    md_path = out / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.md"
    csv_path = out / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.csv"
    examples_path = out / "B9_FRENCH_EVENT_DISPLAY_EXAMPLES_V0.json"
    manifest_path = out / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_MANIFEST.json"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(md_path, payload)
    write_csv(csv_path, entries)
    examples_path.write_text(json.dumps(build_examples(entries), ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {examples_path}")
    print(f"Wrote: {manifest_path}")
    print(f"Status: {validation['status']}")
    print(f"Entries: {validation['entry_count']}")

    if args.strict_exit and validation["status"] != "READY":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
