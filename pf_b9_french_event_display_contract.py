"""T0159 - B9 French Event Display Contract V0.

Read-only translation layer for B9/B6 technical enums.
The engine keeps stable English enum keys; dashboard/Telegram/Markdown surfaces use
French trader labels and controlled sentences.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping, Optional

VERSION = "T0159_B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0"

FORBIDDEN_TERMS = (
    "BUY",
    "SELL",
    "signal gagnant",
    "probabilite de reussite",
    "probabilité de réussite",
    "taux de reussite",
    "taux de réussite",
    "entre maintenant",
    "execution obligatoire",
    "exécution obligatoire",
)

CATEGORIES = (
    "scene_state",
    "scene_transition",
    "scene_role",
    "price_verdict",
    "terrain_node",
    "memory_confidence_ladder",
    "false_positive_context",
    "source_quality_gate",
    "telegram_gate_state",
    "reality_board_payload_state",
)


@dataclass(frozen=True)
class DisplayEntry:
    category: str
    enum_key: str
    label_fr_short: str
    phrase_fr_trader: str
    dashboard_text_fr: str
    telegram_text_fr: str
    technical_limit_fr: str
    forbidden_formulation_fr: str
    severity_hint: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _entry(
    category: str,
    enum_key: str,
    short: str,
    phrase: str,
    limit: str = "Garde la provenance et les limites visibles.",
    severity: str = "INFO",
) -> DisplayEntry:
    return DisplayEntry(
        category=category,
        enum_key=enum_key,
        label_fr_short=short,
        phrase_fr_trader=phrase,
        dashboard_text_fr=phrase,
        telegram_text_fr=phrase,
        technical_limit_fr=limit,
        forbidden_formulation_fr="Ne pas transformer cette lecture en ordre, promesse ou certitude.",
        severity_hint=severity,
    )


_BASE_ENTRIES: List[DisplayEntry] = [
    # scene_state
    _entry("scene_state", "SCENE_BUILDING", "Scene en construction", "B9 voit une scene en construction : le flux travaille encore sa zone."),
    _entry("scene_state", "SCENE_TESTING", "Scene en test", "B9 voit une zone en test : le prix juge la memoire active."),
    _entry("scene_state", "SCENE_ACCEPTED", "Scene acceptee", "B9 voit une scene acceptee par le prix : la zone gagne en lisibilite."),
    _entry("scene_state", "SCENE_REJECTED", "Scene rejetee", "B9 voit une scene rejetee : le prix refuse la zone travaillee."),
    _entry("scene_state", "SCENE_DECONSTRUCTING", "Scene en deconstruction", "B9 voit une scene qui se deconstruit : le role initial perd de la coherence."),
    _entry("scene_state", "SCENE_REBUILDING", "Scene en reconstruction", "B9 voit une reconstruction : le flux recompose une base apres rupture ou rejet."),
    _entry("scene_state", "SCENE_MEMORY_SHIFTED", "Memoire deplacee", "B9 voit une memoire deplacee : le centre utile migre vers une nouvelle zone."),
    _entry("scene_state", "SCENE_BLOCKED_RAW_UNAVAILABLE", "Scene bloquee raw indisponible", "B9 bloque la scene active : la texture raw manque pour exploiter la memoire.", severity="BLOCK"),
    _entry("scene_state", "SCENE_REVIEW_REQUIRED", "Scene a revoir", "B9 marque la scene en revue technique : lecture utile mais encore fragile.", severity="REVIEW"),
    # transitions
    _entry("scene_transition", "BUILD_TO_TEST", "Construction vers test", "La scene passe de construction a test de zone."),
    _entry("scene_transition", "TEST_TO_ACCEPTED", "Test accepte", "Le test de zone est accepte par le prix."),
    _entry("scene_transition", "TEST_TO_REJECTED", "Test rejete", "Le test de zone est rejete par le prix."),
    _entry("scene_transition", "ACCEPTED_TO_MEMORY_SHIFTED", "Acceptation puis memoire deplacee", "La scene acceptee deplace la memoire active."),
    _entry("scene_transition", "MEMORY_SHIFT_TO_NEW_TEST", "Memoire deplacee vers nouveau test", "La memoire deplacee appelle un nouveau test de zone."),
    _entry("scene_transition", "RAW_UNAVAILABLE_TRANSITION_BLOCKED", "Transition bloquee raw indisponible", "La transition est bloquee : la texture raw manque.", severity="BLOCK"),
    # scene_role
    _entry("scene_role", "EFFORT_WITHOUT_RESULT_FRICTION", "Effort sans resultat", "Beaucoup d'effort apparait, mais le prix ne transforme pas encore cet effort en progres net."),
    _entry("scene_role", "ABSORPTION_SHELF_FRICTION", "Palier d'absorption", "Le flux construit un palier d'absorption : la zone est habitee et freine le mouvement."),
    _entry("scene_role", "PROGRESSIVE_FIRST_LEG", "Premiere jambe progressive", "B9 voit une premiere jambe progressive : l'effort produit un deplacement lisible."),
    _entry("scene_role", "PROGRESSIVE_SECOND_LEG_CANDIDATE", "Deuxieme jambe candidate", "B9 voit une deuxieme jambe candidate : le film prolonge une pression deja installee."),
    _entry("scene_role", "CENTER_MIGRATION_DOWN_MEMORY_SHIFT", "Centre qui migre vers le bas", "Le centre utile descend : la memoire travaille plus bas."),
    _entry("scene_role", "CENTER_MIGRATION_UP_MEMORY_SHIFT", "Centre qui migre vers le haut", "Le centre utile monte : la memoire travaille plus haut."),
    _entry("scene_role", "CORRECTIVE_BREATH_NO_PROGRESS", "Respiration corrective sans progres", "Le flux respire, mais ne construit pas encore de progres durable."),
    _entry("scene_role", "FAILED_REINTEGRATION_SCENE_ROLE", "Reintegration echouee", "La reintegration echoue : le prix ne reprend pas proprement la zone."),
    _entry("scene_role", "PULLBACK_ABSORBED_RECONSTRUCTION", "Pullback absorbe", "Le pullback est absorbe : la zone tient et reconstruit une base."),
    # price_verdict
    _entry("price_verdict", "ACCEPTED", "Accepte", "Le prix accepte la zone travaillee."),
    _entry("price_verdict", "REJECTED", "Rejete", "Le prix rejette la zone travaillee."),
    _entry("price_verdict", "PULLBACK_ABSORBED", "Pullback absorbe", "Le pullback est absorbe par la zone active."),
    _entry("price_verdict", "LOWER_ZONE_DEFENDED", "Zone basse defendue", "La zone basse est defendue : le prix ne la consomme pas."),
    _entry("price_verdict", "FAILED_REINTEGRATION", "Reintegration echouee", "La reintegration echoue : la zone refuse le retour."),
    _entry("price_verdict", "HIGH_ZONE_EXHAUSTED", "Zone haute essoufflee", "La zone haute montre un essoufflement technique."),
    _entry("price_verdict", "CONSUMED", "Zone consommee", "La zone est consommee : sa memoire active perd son role initial."),
    _entry("price_verdict", "PENDING", "Verdict en attente", "Le verdict prix reste en attente : la scene n'est pas encore tranchee."),
    _entry("price_verdict", "RAW_UNAVAILABLE_REJECTED", "Rejete raw indisponible", "La lecture active est rejetee car la texture raw manque.", severity="BLOCK"),
    # terrain_node
    _entry("terrain_node", "HIGH_REJECTION_NODE", "Node de rejet haut", "Node de rejet haut : la zone superieure refuse la poursuite."),
    _entry("terrain_node", "LOWER_ZONE_DEFENDED_NODE", "Node de zone basse defendue", "Node de zone basse defendue : le bas reste habite."),
    _entry("terrain_node", "PULLBACK_ABSORBED_NODE", "Node de pullback absorbe", "Node de pullback absorbe : la correction est absorbee dans la zone."),
    _entry("terrain_node", "FAILED_REINTEGRATION_NODE", "Node de reintegration echouee", "Node de reintegration echouee : le retour dans la zone ne tient pas."),
    _entry("terrain_node", "RETEST_FAILED_NODE", "Node de retest echoue", "Node de retest echoue : le test de zone ne valide pas le retour."),
    _entry("terrain_node", "ABSORPTION_SHELF_NODE", "Node de palier d'absorption", "Node de palier d'absorption : effort, compression et frein local."),
    _entry("terrain_node", "PROGRESSIVE_REACTION_NODE", "Node de reaction progressive", "Node de reaction progressive : le centre avance par paliers."),
    # memory ladder
    _entry("memory_confidence_ladder", "MEMORY_STRONG_COMPARABLE", "Memoire fortement comparable", "B6 trouve une memoire fortement comparable, avec limites visibles."),
    _entry("memory_confidence_ladder", "MEMORY_PARTIAL_COMPARABLE", "Memoire comparable partielle", "B6 trouve une memoire comparable partielle : utile, mais a lire avec prudence technique."),
    _entry("memory_confidence_ladder", "MEMORY_SOURCE_LIMITED", "Memoire limitee par la source", "La memoire est limitee par la qualite de source."),
    _entry("memory_confidence_ladder", "MEMORY_SESSION_MISMATCH", "Memoire en session differente", "La memoire existe, mais la session differe de la scene actuelle."),
    _entry("memory_confidence_ladder", "MEMORY_RETEST_MISSING", "Memoire sans retest visible", "La memoire est comparable, mais le retest manque ou reste incomplet."),
    _entry("memory_confidence_ladder", "MEMORY_REJECTED_RAW_UNAVAILABLE", "Memoire rejetee raw indisponible", "La memoire est rejetee : raw indisponible.", severity="BLOCK"),
    # false positive
    _entry("false_positive_context", "B6_FALSE_POSITIVE_CONTEXT_LOW", "Piege technique faible", "Film proche avec piege technique faible."),
    _entry("false_positive_context", "B6_FALSE_POSITIVE_CONTEXT_MEDIUM", "Piege technique moyen", "Film proche, mais comparaison a nuancer."),
    _entry("false_positive_context", "B6_FALSE_POSITIVE_CONTEXT_HIGH", "Piege technique fort", "Film proche, mais piege technique fort : ne pas lire comme repetition certaine.", severity="REVIEW"),
    _entry("false_positive_context", "MEMORY_FP_REJECT_RAW_UNAVAILABLE", "Piege raw indisponible", "Comparaison memoire bloquee : raw indisponible.", severity="BLOCK"),
    # source quality
    _entry("source_quality_gate", "SOURCE_RAW_CONFIRMED", "Source raw confirmee", "La source raw confirme la lecture disponible."),
    _entry("source_quality_gate", "SOURCE_RAW_NUANCED", "Source raw nuancee", "La source raw nuance la lecture : ne pas durcir en confirmation."),
    _entry("source_quality_gate", "SOURCE_PROXY_ONLY", "Source proxy seule", "Lecture proxy uniquement : utile pour le film, limitee pour la texture fine."),
    _entry("source_quality_gate", "SOURCE_RECONSTRUCTED_LIMITED", "Source reconstruite limitee", "Lecture reconstruite : provenance et confidence cap doivent rester visibles."),
    _entry("source_quality_gate", "SOURCE_RAW_UNAVAILABLE_REJECTED", "Raw indisponible rejete", "Raw indisponible : la scene active est bloquee.", severity="BLOCK"),
    _entry("source_quality_gate", "SOURCE_QUALITY_LIVE_UNQUALIFIED", "Live non qualifie raw", "Scene live non encore qualifiee cote texture raw.", severity="REVIEW"),
    # telegram states
    _entry("telegram_gate_state", "B9_TELEGRAM_FR_GATE_CANDIDATE_READY", "Message FR pret", "Message Telegram candidat pret en mode no-send."),
    _entry("telegram_gate_state", "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK", "Message FR a risque technique", "Message Telegram candidat lisible, avec risque technique visible.", severity="REVIEW"),
    _entry("telegram_gate_state", "BLOCKED_REALITY_BOARD_PAYLOAD_NOT_READY", "Telegram bloque payload non pret", "Message bloque : payload Reality Board non pret.", severity="BLOCK"),
    _entry("telegram_gate_state", "BLOCKED_FORBIDDEN_LANGUAGE", "Telegram bloque langage interdit", "Message bloque : langage interdit detecte.", severity="BLOCK"),
    # reality board states
    _entry("reality_board_payload_state", "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_READY", "Payload Reality Board pret", "Payload Reality Board candidat pret pour affichage."),
    _entry("reality_board_payload_state", "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK", "Payload Reality Board a risque technique", "Payload affichable, mais limites techniques visibles.", severity="REVIEW"),
    _entry("reality_board_payload_state", "BLOCKED_MISSING_ATTENTION_PACKET_INPUT", "Payload bloque packet manquant", "Payload bloque : packet d'attention manquant.", severity="BLOCK"),
    _entry("reality_board_payload_state", "BLOCKED_RAW_UNAVAILABLE_IN_ATTENTION_PACKET", "Payload bloque raw indisponible", "Payload bloque : raw indisponible dans le packet.", severity="BLOCK"),
]


def build_contract(extra_entries: Optional[Iterable[Mapping[str, Any]]] = None) -> List[Dict[str, str]]:
    entries = [entry.to_dict() for entry in _BASE_ENTRIES]
    if extra_entries:
        for item in extra_entries:
            if not isinstance(item, Mapping):
                continue
            category = str(item.get("category", "custom"))
            enum_key = str(item.get("enum_key", item.get("key", "UNKNOWN"))).strip()
            if not enum_key:
                continue
            entries.append(
                _entry(
                    category=category,
                    enum_key=enum_key,
                    short=str(item.get("label_fr_short", enum_key)),
                    phrase=str(item.get("phrase_fr_trader", item.get("label_fr_short", enum_key))),
                    limit=str(item.get("technical_limit_fr", "Garde la provenance et les limites visibles.")),
                    severity=str(item.get("severity_hint", "INFO")),
                ).to_dict()
            )
    return sorted(entries, key=lambda row: (row["category"], row["enum_key"]))


def index_contract(entries: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, str]]:
    return {str(row["enum_key"]): {k: str(v) for k, v in row.items()} for row in entries if row.get("enum_key")}


def translate_event(enum_key: str, entries: Optional[Iterable[Mapping[str, Any]]] = None) -> Dict[str, str]:
    contract = index_contract(entries or build_contract())
    key = str(enum_key or "UNKNOWN").strip()
    if key in contract:
        return contract[key]
    return _entry(
        category="unknown",
        enum_key=key or "UNKNOWN",
        short="Evenement a traduire",
        phrase=f"Evenement technique a traduire : {key or 'UNKNOWN'}.",
        limit="Ajouter ce cas au contrat T0159 avant affichage public.",
        severity="REVIEW",
    ).to_dict()


def scan_forbidden_language(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    for idx, row in enumerate(rows):
        for field, value in row.items():
            text = str(value)
            lowered = text.lower()
            for term in FORBIDDEN_TERMS:
                if term.lower() in lowered:
                    hits.append({"row_index": str(idx), "field": str(field), "term": term})
    return hits


def validate_contract(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    data = list(rows)
    by_category: Dict[str, int] = {}
    missing: List[Dict[str, str]] = []
    seen = set()
    duplicates: List[str] = []
    required = {
        "category",
        "enum_key",
        "label_fr_short",
        "phrase_fr_trader",
        "dashboard_text_fr",
        "telegram_text_fr",
        "technical_limit_fr",
        "forbidden_formulation_fr",
        "severity_hint",
    }
    for idx, row in enumerate(data):
        cat = str(row.get("category", "UNKNOWN"))
        by_category[cat] = by_category.get(cat, 0) + 1
        key = str(row.get("enum_key", ""))
        if key in seen:
            duplicates.append(key)
        seen.add(key)
        for field in sorted(required):
            if not str(row.get(field, "")).strip():
                missing.append({"row_index": str(idx), "enum_key": key, "field": field})
    forbidden_hits = scan_forbidden_language(data)
    missing_categories = [cat for cat in CATEGORIES if by_category.get(cat, 0) == 0]
    return {
        "version": VERSION,
        "entry_count": len(data),
        "category_counts": dict(sorted(by_category.items())),
        "missing_required_fields": missing,
        "duplicate_enum_keys": duplicates,
        "missing_categories": missing_categories,
        "forbidden_language_hits": forbidden_hits,
        "contract_state": "PASS" if not missing and not duplicates and not missing_categories and not forbidden_hits else "REVIEW",
    }
