from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

VERSION = "T0159_B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0"

POLICY = {
    "read_only": True,
    "db_write": False,
    "dashboard_live_mutation": False,
    "telegram_send": False,
    "execution_decision": False,
    "outcome_probability": False,
    "technical_keys_language": "english_enums",
    "display_language": "fr_trader",
}

FORBIDDEN_DISPLAY_SUBSTRINGS = (
    " buy",
    "buy ",
    " sell",
    "sell ",
    "achat forcé",
    "vente forcée",
    "probabilité de succès",
    "garanti",
    "ordre automatique",
)


@dataclass(frozen=True)
class FrenchEventDisplay:
    category: str
    key: str
    label_fr: str
    short_fr: str
    explanation_fr: str
    attention_level: str = "INFO"
    trader_usage_fr: str = "Affichage seulement : perception à lire, décision trader."
    technical_limit_fr: str = "Contrat de traduction ; ne modifie aucune logique moteur."

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _event(
    category: str,
    key: str,
    label_fr: str,
    short_fr: str,
    explanation_fr: str,
    attention_level: str = "INFO",
    trader_usage_fr: str = "Affichage seulement : perception à lire, décision trader.",
    technical_limit_fr: str = "Contrat de traduction ; ne modifie aucune logique moteur.",
) -> FrenchEventDisplay:
    return FrenchEventDisplay(
        category=category,
        key=key,
        label_fr=label_fr,
        short_fr=short_fr,
        explanation_fr=explanation_fr,
        attention_level=attention_level,
        trader_usage_fr=trader_usage_fr,
        technical_limit_fr=technical_limit_fr,
    )


CONTRACT: Dict[str, Dict[str, FrenchEventDisplay]] = {
    "scene_state": {
        "SCENE_CANDIDATE": _event("scene_state", "SCENE_CANDIDATE", "Scène candidate", "Scène candidate", "B9 voit une scène exploitable en lecture, encore à qualifier.", "WATCH"),
        "SCENE_ACCEPTED": _event("scene_state", "SCENE_ACCEPTED", "Scène acceptée par le prix", "Scène acceptée", "Le prix confirme que la scène a obtenu une acceptation visible.", "ATTENTION"),
        "SCENE_REJECTED": _event("scene_state", "SCENE_REJECTED", "Scène rejetée par le prix", "Scène rejetée", "Le prix refuse la scène ou invalide son déplacement.", "ATTENTION"),
        "SCENE_PENDING": _event("scene_state", "SCENE_PENDING", "Scène en attente de jugement", "En attente", "La scène existe, mais le retest ou l’acceptation reste à venir.", "WATCH"),
        "SCENE_PARTIAL": _event("scene_state", "SCENE_PARTIAL", "Scène partielle", "Partielle", "La scène est visible, mais la source ou les champs restent incomplets.", "WATCH"),
        "SCENE_CONSUMED": _event("scene_state", "SCENE_CONSUMED", "Scène consommée", "Consommée", "L’effort a déjà produit son effet principal ; lecture tardive possible.", "INFO"),
        "SCENE_EXHAUSTED": _event("scene_state", "SCENE_EXHAUSTED", "Scène essoufflée", "Essoufflée", "La progression perd de l’efficacité ou ne déplace plus la mémoire.", "WATCH"),
        "SCENE_UNKNOWN": _event("scene_state", "SCENE_UNKNOWN", "Scène non qualifiée", "Non qualifiée", "B9 ne dispose pas d’assez de champs pour qualifier la scène.", "INFO"),
        "B9_LIVE_BRIEF_READY": _event("scene_state", "B9_LIVE_BRIEF_READY", "Brief live B9 prêt", "Brief prêt", "Le brief peut afficher la scène, la mémoire proche et les limites techniques.", "ATTENTION"),
        "BLOCKED_MISSING_INPUTS": _event("scene_state", "BLOCKED_MISSING_INPUTS", "Brief bloqué : entrées manquantes", "Entrées manquantes", "Un ou plusieurs fichiers attendus sont absents.", "BLOCKER"),
    },
    "scene_transition": {
        "PULLBACK_ABSORBED": _event("scene_transition", "PULLBACK_ABSORBED", "Pullback absorbé", "Pullback absorbé", "Le retour contre le mouvement ne reprend pas la mémoire précédente.", "ATTENTION"),
        "FAILED_REINTEGRATION": _event("scene_transition", "FAILED_REINTEGRATION", "Réintégration échouée", "Réintégration échouée", "Le prix tente de revenir dans une zone mais n’y conserve pas de centre stable.", "ATTENTION"),
        "CENTER_MIGRATION_UP": _event("scene_transition", "CENTER_MIGRATION_UP", "Centre qui migre vers le haut", "Centre montant", "La mémoire interne se déplace par paliers vers une zone supérieure.", "ATTENTION"),
        "CENTER_MIGRATION_DOWN": _event("scene_transition", "CENTER_MIGRATION_DOWN", "Centre qui migre vers le bas", "Centre descendant", "La mémoire interne se déplace par paliers vers une zone inférieure.", "ATTENTION"),
        "MEMORY_SHIFT_UP": _event("scene_transition", "MEMORY_SHIFT_UP", "Mémoire déplacée vers le haut", "Mémoire haute", "Le flux imprime une nouvelle mémoire au-dessus de la zone précédente.", "ATTENTION"),
        "MEMORY_SHIFT_DOWN": _event("scene_transition", "MEMORY_SHIFT_DOWN", "Mémoire déplacée vers le bas", "Mémoire basse", "Le flux imprime une nouvelle mémoire sous la zone précédente.", "ATTENTION"),
        "PROGRESSIVE_WAVE": _event("scene_transition", "PROGRESSIVE_WAVE", "Vague progressive réelle", "Vague progressive", "L’effort produit du résultat et déplace la mémoire.", "ATTENTION"),
        "CORRECTIVE_BOUNCE": _event("scene_transition", "CORRECTIVE_BOUNCE", "Rebond correctif", "Rebond correctif", "Le prix respire mais ne prouve pas encore un progrès durable.", "WATCH"),
        "CORRECTIVE_BOUNCE_WITHOUT_PROGRESS": _event("scene_transition", "CORRECTIVE_BOUNCE_WITHOUT_PROGRESS", "Rebond correctif sans progrès durable", "Rebond sans progrès", "Le rebond corrige localement mais ne déplace pas la mémoire.", "WATCH"),
        "HIGH_REJECTION": _event("scene_transition", "HIGH_REJECTION", "Rejet de zone haute", "Rejet haut", "Le haut travaillé n’est pas accepté et la mémoire reste fragile.", "ATTENTION"),
        "LOW_DEFENDED": _event("scene_transition", "LOW_DEFENDED", "Zone basse défendue", "Bas défendu", "L’effort opposé ne parvient pas à déplacer la mémoire sous la zone.", "ATTENTION"),
        "SECOND_LEG_DOWN": _event("scene_transition", "SECOND_LEG_DOWN", "Deuxième jambe baissière", "Deuxième jambe basse", "Après rejet ou counter-breath échoué, une nouvelle jambe prolonge le déplacement bas.", "ATTENTION"),
        "SECOND_LEG_UP": _event("scene_transition", "SECOND_LEG_UP", "Deuxième jambe haussière", "Deuxième jambe haute", "Après pullback absorbé, une nouvelle jambe prolonge le déplacement haut.", "ATTENTION"),
        "RELEASE_UP_ACCEPTED": _event("scene_transition", "RELEASE_UP_ACCEPTED", "Release haussière acceptée", "Release acceptée haut", "Le prix accepte la projection supérieure après tension libérée.", "ATTENTION"),
        "RELEASE_DOWN_ACCEPTED": _event("scene_transition", "RELEASE_DOWN_ACCEPTED", "Release baissière acceptée", "Release acceptée bas", "Le prix accepte la projection inférieure après tension libérée.", "ATTENTION"),
        "EFFORT_WITHOUT_RESULT": _event("scene_transition", "EFFORT_WITHOUT_RESULT", "Effort sans résultat", "Effort sans résultat", "Le flux dépense de l’énergie mais ne gagne pas de terrain mesurable.", "WATCH"),
        "ABSORPTION_ACCOMPANYING_PRESSURE": _event("scene_transition", "ABSORPTION_ACCOMPANYING_PRESSURE", "Absorption qui accompagne la pression", "Absorption accompagnante", "L’absorption ne bloque pas le mouvement ; elle accompagne le déplacement.", "ATTENTION"),
    },
    "scene_role": {
        "PROGRESSIVE_FIRST_LEG": _event("scene_role", "PROGRESSIVE_FIRST_LEG", "Première jambe progressive", "Première jambe", "La scène démarre un déplacement réel avec mémoire qui commence à migrer.", "ATTENTION"),
        "PROGRESSIVE_WAVE_MEMORY_SHIFT": _event("scene_role", "PROGRESSIVE_WAVE_MEMORY_SHIFT", "Vague progressive avec mémoire déplacée", "Vague + mémoire", "La vague produit assez de résultat pour déplacer la mémoire.", "ATTENTION"),
        "CENTER_MIGRATION": _event("scene_role", "CENTER_MIGRATION", "Migration de centre", "Centre migré", "Le centre de gravité de la scène se déplace par paliers.", "ATTENTION"),
        "PROJECTION_REJECTED_THEN_MEMORY_SHIFTED": _event("scene_role", "PROJECTION_REJECTED_THEN_MEMORY_SHIFTED", "Projection refusée puis mémoire déplacée", "Projection refusée", "La projection initiale échoue puis le flux imprime une mémoire ailleurs.", "ATTENTION"),
        "CORRECTIVE_REBOUND_WITHOUT_PROGRESS": _event("scene_role", "CORRECTIVE_REBOUND_WITHOUT_PROGRESS", "Rebond correctif sans progrès", "Correction sans progrès", "La scène respire mais ne répare pas la mémoire précédente.", "WATCH"),
        "LOW_ZONE_DEFENSE": _event("scene_role", "LOW_ZONE_DEFENSE", "Défense de zone basse", "Défense basse", "La zone basse absorbe les tests et reste active.", "ATTENTION"),
        "HIGH_ZONE_REJECTION": _event("scene_role", "HIGH_ZONE_REJECTION", "Rejet de zone haute", "Rejet haut", "Le haut travaillé ne se transforme pas en acceptation durable.", "ATTENTION"),
        "FAILED_REINTEGRATION_ROLE": _event("scene_role", "FAILED_REINTEGRATION_ROLE", "Réintégration refusée", "Retour refusé", "La tentative de retour dans la zone échoue.", "ATTENTION"),
        "EFFORT_RESULT_PROGRESS": _event("scene_role", "EFFORT_RESULT_PROGRESS", "Effort / résultat / progrès", "Effort-résultat", "La scène est lue par ce que l’effort obtient et par la mémoire déplacée.", "INFO"),
    },
    "price_verdict": {
        "ACCEPTED": _event("price_verdict", "ACCEPTED", "Accepté par le prix", "Accepté", "Le prix confirme la zone ou la projection.", "ATTENTION"),
        "REJECTED": _event("price_verdict", "REJECTED", "Rejeté par le prix", "Rejeté", "Le prix refuse la zone, la projection ou le retour.", "ATTENTION"),
        "PENDING": _event("price_verdict", "PENDING", "Prix en attente de verdict", "En attente", "Le prix n’a pas encore donné un jugement clair.", "WATCH"),
        "FAILED_RETEST": _event("price_verdict", "FAILED_RETEST", "Retest échoué", "Retest échoué", "Le retour sur la zone ne tient pas.", "ATTENTION"),
        "RETEST_ACCEPTED": _event("price_verdict", "RETEST_ACCEPTED", "Retest accepté", "Retest accepté", "Le retest confirme que la zone reste travaillée ou défendue.", "ATTENTION"),
        "RETEST_PENDING": _event("price_verdict", "RETEST_PENDING", "Retest en attente", "Retest attendu", "La cassure ou projection n’est pas encore jugée par retour sur zone.", "WATCH"),
        "PRICE_NOT_VISIBLE": _event("price_verdict", "PRICE_NOT_VISIBLE", "Prix non visible", "Prix absent", "Le verdict prix ne peut pas être établi depuis les champs disponibles.", "BLOCKER"),
        "LOWER_ACCEPTED": _event("price_verdict", "LOWER_ACCEPTED", "Zone basse acceptée", "Bas accepté", "Le prix accepte de travailler sous la mémoire précédente.", "ATTENTION"),
        "HIGH_REJECTED": _event("price_verdict", "HIGH_REJECTED", "Haut rejeté", "Haut rejeté", "La zone haute ne conserve pas l’acceptation.", "ATTENTION"),
    },
    "terrain_node": {
        "PROGRESSIVE_REACTION_NODE": _event("terrain_node", "PROGRESSIVE_REACTION_NODE", "Node de réaction progressive", "Node progressif", "Le node produit une réaction avec déplacement de mémoire.", "ATTENTION"),
        "ABSORPTION_NODE": _event("terrain_node", "ABSORPTION_NODE", "Node d’absorption", "Node absorption", "Le flux travaille une zone avec effort visible et résultat à mesurer.", "WATCH"),
        "CENTER_MIGRATION_NODE": _event("terrain_node", "CENTER_MIGRATION_NODE", "Node de migration du centre", "Node centre", "La structure interne déplace son centre de gravité.", "ATTENTION"),
        "LOW_DEFENSE_NODE": _event("terrain_node", "LOW_DEFENSE_NODE", "Node de défense basse", "Node défense basse", "La zone basse est testée puis défendue.", "ATTENTION"),
        "HIGH_REJECTION_NODE": _event("terrain_node", "HIGH_REJECTION_NODE", "Node de rejet haut", "Node rejet haut", "La zone haute attire l’effort mais ne conserve pas le centre.", "ATTENTION"),
        "FAILED_REINTEGRATION_NODE": _event("terrain_node", "FAILED_REINTEGRATION_NODE", "Node de réintégration échouée", "Node retour échoué", "Le retour dans l’ancienne zone échoue.", "ATTENTION"),
        "EFFORT_WITHOUT_RESULT_NODE": _event("terrain_node", "EFFORT_WITHOUT_RESULT_NODE", "Node d’effort sans résultat", "Node friction", "Le flux dépense de l’énergie sans déplacer la mémoire.", "WATCH"),
        "UNKNOWN_TERRAIN_NODE": _event("terrain_node", "UNKNOWN_TERRAIN_NODE", "Node terrain non qualifié", "Node inconnu", "Le node existe mais manque de preuves exploitables.", "INFO"),
    },
    "memory_confidence_ladder": {
        "MEMORY_STRONG_COMPARABLE": _event("memory_confidence_ladder", "MEMORY_STRONG_COMPARABLE", "Mémoire fortement comparable", "Mémoire forte", "B6 trouve une famille de film proche avec comparaison exploitable.", "ATTENTION"),
        "MEMORY_PARTIAL_COMPARABLE": _event("memory_confidence_ladder", "MEMORY_PARTIAL_COMPARABLE", "Mémoire comparable partielle", "Mémoire partielle", "B6 trouve une ressemblance utile mais incomplète.", "WATCH"),
        "MEMORY_WEAK_COMPARABLE": _event("memory_confidence_ladder", "MEMORY_WEAK_COMPARABLE", "Mémoire faiblement comparable", "Mémoire faible", "La ressemblance existe mais reste fragile.", "INFO"),
        "MEMORY_NOT_COMPARABLE": _event("memory_confidence_ladder", "MEMORY_NOT_COMPARABLE", "Mémoire non comparable", "Non comparable", "B6 ne trouve pas de film proche exploitable.", "INFO"),
        "MEMORY_UNKNOWN": _event("memory_confidence_ladder", "MEMORY_UNKNOWN", "Mémoire inconnue", "Mémoire inconnue", "La mémoire n’est pas disponible ou pas encore construite.", "INFO"),
        "B6_KEEP_CANDIDATE": _event("memory_confidence_ladder", "B6_KEEP_CANDIDATE", "Film mémoire conservé", "Film conservé", "B6 garde ce film comme candidat mémoire.", "INFO"),
        "B6_REVIEW_CANDIDATE": _event("memory_confidence_ladder", "B6_REVIEW_CANDIDATE", "Film mémoire à revoir", "Film à revoir", "B6 conserve le film mais demande une relecture technique.", "WATCH"),
        "B6_LIVE_QUERY_ONLY_NOT_CANDIDATE": _event("memory_confidence_ladder", "B6_LIVE_QUERY_ONLY_NOT_CANDIDATE", "Scène live utilisée seulement comme requête", "Requête live", "La scène sert à interroger B6 ; elle n’est pas une carte mémoire stockée.", "INFO"),
    },
    "false_positive_context": {
        "B9_FALSE_POSITIVE_CONTEXT_HIGH": _event("false_positive_context", "B9_FALSE_POSITIVE_CONTEXT_HIGH", "Film proche, mais piège technique fort", "Piège fort", "La ressemblance existe mais plusieurs conditions techniques divergent.", "BLOCKER"),
        "B9_FALSE_POSITIVE_CONTEXT_MEDIUM": _event("false_positive_context", "B9_FALSE_POSITIVE_CONTEXT_MEDIUM", "Film proche, piège technique moyen", "Piège moyen", "La ressemblance doit être lue avec prudence technique.", "WATCH"),
        "B9_FALSE_POSITIVE_CONTEXT_LOW": _event("false_positive_context", "B9_FALSE_POSITIVE_CONTEXT_LOW", "Film proche, piège technique faible", "Piège faible", "La ressemblance paraît utilisable, avec limites normales.", "INFO"),
        "B6_FALSE_POSITIVE_CONTEXT_HIGH": _event("false_positive_context", "B6_FALSE_POSITIVE_CONTEXT_HIGH", "Film proche, mais piège technique fort", "Piège fort", "B6 rapproche les formes, T0117 signale une forte fragilité de comparaison.", "BLOCKER"),
        "B6_FALSE_POSITIVE_CONTEXT_MEDIUM": _event("false_positive_context", "B6_FALSE_POSITIVE_CONTEXT_MEDIUM", "Film proche, piège technique moyen", "Piège moyen", "La comparaison est utile mais plusieurs écarts doivent rester visibles.", "WATCH"),
        "B6_FALSE_POSITIVE_CONTEXT_LOW": _event("false_positive_context", "B6_FALSE_POSITIVE_CONTEXT_LOW", "Film proche, piège technique faible", "Piège faible", "Peu de divergences techniques relevées par B6.", "INFO"),
        "FALSE_POSITIVE_CONTEXT_NOT_PROVIDED": _event("false_positive_context", "FALSE_POSITIVE_CONTEXT_NOT_PROVIDED", "Contexte faux positif non fourni", "Contexte absent", "Le brief ne reçoit pas encore de contexte faux positif.", "WATCH"),
        "MEMORY_FP_LOW": _event("false_positive_context", "MEMORY_FP_LOW", "Risque de faux rapprochement faible", "Faux proche faible", "La mémoire comparable ne montre pas de piège majeur.", "INFO"),
        "MEMORY_FP_HIGH": _event("false_positive_context", "MEMORY_FP_HIGH", "Risque de faux rapprochement fort", "Faux proche fort", "La mémoire ressemble au présent mais peut tromper la lecture.", "BLOCKER"),
    },
    "source_quality_gate": {
        "SOURCE_RAW_CONFIRMED": _event("source_quality_gate", "SOURCE_RAW_CONFIRMED", "Source confirmée par raw", "Raw confirmé", "La lecture proxy est soutenue par la texture raw disponible.", "ATTENTION"),
        "SOURCE_RAW_NUANCED": _event("source_quality_gate", "SOURCE_RAW_NUANCED", "Source nuancée par raw", "Raw nuancé", "La source soutient la lecture mais ajoute des limites.", "WATCH"),
        "SOURCE_QUALITY_LIVE_UNQUALIFIED": _event("source_quality_gate", "SOURCE_QUALITY_LIVE_UNQUALIFIED", "Source live non qualifiée", "Live non qualifié", "Le live est utilisable mais sans validation raw complète.", "WATCH"),
        "SOURCE_QUALITY_USABLE": _event("source_quality_gate", "SOURCE_QUALITY_USABLE", "Source exploitable", "Source exploitable", "La source est suffisante pour une lecture comparative.", "INFO"),
        "SOURCE_QUALITY_PARTIAL": _event("source_quality_gate", "SOURCE_QUALITY_PARTIAL", "Source partielle", "Source partielle", "La source permet une lecture, mais des champs manquent.", "WATCH"),
        "SOURCE_QUALITY_DEGRADED": _event("source_quality_gate", "SOURCE_QUALITY_DEGRADED", "Source dégradée", "Source dégradée", "La qualité des données limite fortement la lecture.", "BLOCKER"),
        "RAW_UNAVAILABLE_REJECTED": _event("source_quality_gate", "RAW_UNAVAILABLE_REJECTED", "Rejeté : raw indisponible", "Raw indisponible", "La scène est rejetée car la preuve raw attendue n’est pas disponible.", "BLOCKER"),
        "RAW_AGREEMENT_NOT_VISIBLE": _event("source_quality_gate", "RAW_AGREEMENT_NOT_VISIBLE", "Accord raw non visible", "Raw non visible", "Le raw ne permet pas encore de confirmer ou nuancer la lecture.", "WATCH"),
        "M1_BAR_PROXY": _event("source_quality_gate", "M1_BAR_PROXY", "Lecture reconstruite M1", "M1 reconstruit", "Lecture utile pour le film, limitée pour footprint exact.", "WATCH"),
        "RECONSTRUCTED": _event("source_quality_gate", "RECONSTRUCTED", "Donnée reconstruite", "Reconstruit", "La lecture vient d’une reconstruction et doit afficher ses limites.", "WATCH"),
    },
    "telegram_gate_state": {
        "TELEGRAM_READY_DRAFT_ONLY": _event("telegram_gate_state", "TELEGRAM_READY_DRAFT_ONLY", "Message Telegram prêt en brouillon", "Brouillon prêt", "Le message peut être préparé mais aucun envoi live n’est effectué.", "INFO"),
        "TELEGRAM_NOT_SENT_READ_ONLY": _event("telegram_gate_state", "TELEGRAM_NOT_SENT_READ_ONLY", "Telegram non envoyé : mode read-only", "Non envoyé", "Le contrat autorise l’affichage du texte, pas l’envoi.", "INFO"),
        "TELEGRAM_BLOCKED_MISSING_INPUTS": _event("telegram_gate_state", "TELEGRAM_BLOCKED_MISSING_INPUTS", "Telegram bloqué : entrées manquantes", "Entrées manquantes", "Le message ne peut pas être préparé correctement.", "BLOCKER"),
        "TELEGRAM_BLOCKED_FORBIDDEN_LANGUAGE": _event("telegram_gate_state", "TELEGRAM_BLOCKED_FORBIDDEN_LANGUAGE", "Telegram bloqué : langage interdit", "Langage bloqué", "Le texte contient un langage incompatible avec PowerFlow.", "BLOCKER"),
        "TELEGRAM_ALLOWED_PREVIEW_ONLY": _event("telegram_gate_state", "TELEGRAM_ALLOWED_PREVIEW_ONLY", "Prévisualisation Telegram autorisée", "Prévisualisation", "Le trader peut lire le message, aucun envoi n’est fait.", "INFO"),
    },
    "reality_board_payload_state": {
        "REALITY_BOARD_PAYLOAD_READY": _event("reality_board_payload_state", "REALITY_BOARD_PAYLOAD_READY", "Payload Reality Board prêt", "Payload prêt", "Les champs nécessaires à l’affichage sont disponibles.", "INFO"),
        "REALITY_BOARD_PAYLOAD_PARTIAL": _event("reality_board_payload_state", "REALITY_BOARD_PAYLOAD_PARTIAL", "Payload Reality Board partiel", "Payload partiel", "L’affichage peut se faire, mais certaines preuves manquent.", "WATCH"),
        "REALITY_BOARD_PAYLOAD_BLOCKED": _event("reality_board_payload_state", "REALITY_BOARD_PAYLOAD_BLOCKED", "Payload Reality Board bloqué", "Payload bloqué", "Le payload ne doit pas être affiché sans correction d’entrée.", "BLOCKER"),
        "REALITY_BOARD_NOT_MUTATED_READ_ONLY": _event("reality_board_payload_state", "REALITY_BOARD_NOT_MUTATED_READ_ONLY", "Reality Board non modifié : read-only", "Board non modifié", "Le contrat produit des fichiers, sans mutation dashboard live.", "INFO"),
        "B9_LIVE_BRIEF_READY": _event("reality_board_payload_state", "B9_LIVE_BRIEF_READY", "Brief B9 prêt pour affichage", "Brief affichable", "Le brief peut alimenter une surface d’affichage si un module séparé le décide.", "INFO"),
        "BLOCKED_MISSING_INPUTS": _event("reality_board_payload_state", "BLOCKED_MISSING_INPUTS", "Affichage bloqué : entrées manquantes", "Entrées manquantes", "Le payload manque de matière pour être affiché proprement.", "BLOCKER"),
    },
}


ALIASES: Dict[str, str] = {
    "memory_confidence_state": "memory_confidence_ladder",
    "memory_ladder_state": "memory_confidence_ladder",
    "b6_memory_ladder": "memory_confidence_ladder",
    "b9_memory_false_positive_state": "false_positive_context",
    "false_positive_state": "false_positive_context",
    "source_quality_state": "source_quality_gate",
    "source_quality_gate_state": "source_quality_gate",
    "telegram_gate": "telegram_gate_state",
    "reality_board_state": "reality_board_payload_state",
}


def canonical_category(category: str) -> str:
    return ALIASES.get(category, category)


def get_display(category: str, key: Any) -> FrenchEventDisplay:
    cat = canonical_category(str(category))
    enum_key = str(key) if key is not None else "UNKNOWN"
    record = CONTRACT.get(cat, {}).get(enum_key)
    if record:
        return record
    return _event(
        cat,
        enum_key,
        f"Traduction à ajouter : {enum_key}",
        "Traduction à ajouter",
        "Enum technique reçu sans traduction française validée.",
        "WATCH",
        trader_usage_fr="Afficher comme enum technique non traduit ; ne pas masquer.",
        technical_limit_fr="Ajouter ce cas au contrat T0159 si récurrent.",
    )


def translate_event(category: str, key: Any, field: str = "label_fr") -> str:
    display = get_display(category, key).to_dict()
    return str(display.get(field, display["label_fr"]))


def translate_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    translated: Dict[str, Any] = {}
    for raw_category, value in payload.items():
        category = canonical_category(str(raw_category))
        if category in CONTRACT or category in set(ALIASES.values()):
            translated[raw_category] = get_display(category, value).to_dict()
    return translated


def iter_contract_rows() -> Iterable[Dict[str, str]]:
    for category in sorted(CONTRACT):
        for key in sorted(CONTRACT[category]):
            yield CONTRACT[category][key].to_dict()


def validate_contract() -> Dict[str, Any]:
    rows = list(iter_contract_rows())
    hits: List[Dict[str, str]] = []
    missing_labels: List[Dict[str, str]] = []
    for row in rows:
        combined = " ".join(
            str(row.get(field, "")) for field in ("label_fr", "short_fr", "explanation_fr", "trader_usage_fr", "technical_limit_fr")
        ).lower()
        for term in FORBIDDEN_DISPLAY_SUBSTRINGS:
            if term.strip() and term in combined:
                hits.append({"category": row["category"], "key": row["key"], "term": term.strip()})
        if not row.get("label_fr") or not row.get("short_fr"):
            missing_labels.append({"category": row["category"], "key": row["key"]})
    return {
        "version": VERSION,
        "total_events": len(rows),
        "categories": sorted(CONTRACT.keys()),
        "forbidden_display_hits": hits,
        "missing_labels": missing_labels,
        "passed": not hits and not missing_labels,
        "policy": POLICY,
    }


def build_contract_payload() -> Dict[str, Any]:
    validation = validate_contract()
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "policy": POLICY,
        "validation": validation,
        "categories": {
            category: {key: event.to_dict() for key, event in sorted(events.items())}
            for category, events in sorted(CONTRACT.items())
        },
    }


def write_json_csv_md(output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_contract_payload()
    rows = list(iter_contract_rows())

    json_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json"
    csv_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.csv"
    md_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "category",
                "key",
                "label_fr",
                "short_fr",
                "explanation_fr",
                "attention_level",
                "trader_usage_fr",
                "technical_limit_fr",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# B9 French Event Display Contract V0",
        "",
        "Contrat read-only de traduction français trader pour affichage dashboard / Telegram draft.",
        "",
        "## Politique",
        "",
        "- Le moteur garde les enums techniques anglais.",
        "- L’affichage expose un français trader clair.",
        "- Le contrat ne modifie aucune DB, aucun dashboard live, aucun envoi Telegram.",
        "- La mémoire B6 reste comparative : elle ne décide pas.",
        "",
        "## Validation",
        "",
        f"- Total events : `{payload['validation']['total_events']}`",
        f"- Passed : `{payload['validation']['passed']}`",
        f"- Forbidden display hits : `{len(payload['validation']['forbidden_display_hits'])}`",
        "",
    ]
    for category in sorted(CONTRACT):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Enum technique | Français trader | Court | Niveau |")
        lines.append("|---|---|---|---|")
        for key in sorted(CONTRACT[category]):
            event = CONTRACT[category][key]
            lines.append(f"| `{key}` | {event.label_fr} | {event.short_fr} | `{event.attention_level}` |")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return {"json": str(json_path), "csv": str(csv_path), "md": str(md_path)}


if __name__ == "__main__":
    out = Path("outputs/b9_french_event_display_contract_v0")
    paths = write_json_csv_md(out)
    print(json.dumps({"version": VERSION, "output_dir": str(out), "paths": paths, "validation": validate_contract()}, ensure_ascii=False, indent=2))
