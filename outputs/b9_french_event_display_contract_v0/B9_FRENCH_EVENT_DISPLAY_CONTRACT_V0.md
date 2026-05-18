# B9 French Event Display Contract V0

Contrat read-only de traduction français trader pour affichage dashboard / Telegram draft.

## Politique

- Le moteur garde les enums techniques anglais.
- L’affichage expose un français trader clair.
- Le contrat ne modifie aucune DB, aucun dashboard live, aucun envoi Telegram.
- La mémoire B6 reste comparative : elle ne décide pas.

## Validation

- Total events : `91`
- Passed : `True`
- Forbidden display hits : `0`

## false_positive_context

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `B6_FALSE_POSITIVE_CONTEXT_HIGH` | Film proche, mais piège technique fort | Piège fort | `BLOCKER` |
| `B6_FALSE_POSITIVE_CONTEXT_LOW` | Film proche, piège technique faible | Piège faible | `INFO` |
| `B6_FALSE_POSITIVE_CONTEXT_MEDIUM` | Film proche, piège technique moyen | Piège moyen | `WATCH` |
| `B9_FALSE_POSITIVE_CONTEXT_HIGH` | Film proche, mais piège technique fort | Piège fort | `BLOCKER` |
| `B9_FALSE_POSITIVE_CONTEXT_LOW` | Film proche, piège technique faible | Piège faible | `INFO` |
| `B9_FALSE_POSITIVE_CONTEXT_MEDIUM` | Film proche, piège technique moyen | Piège moyen | `WATCH` |
| `FALSE_POSITIVE_CONTEXT_NOT_PROVIDED` | Contexte faux positif non fourni | Contexte absent | `WATCH` |
| `MEMORY_FP_HIGH` | Risque de faux rapprochement fort | Faux proche fort | `BLOCKER` |
| `MEMORY_FP_LOW` | Risque de faux rapprochement faible | Faux proche faible | `INFO` |

## memory_confidence_ladder

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `B6_KEEP_CANDIDATE` | Film mémoire conservé | Film conservé | `INFO` |
| `B6_LIVE_QUERY_ONLY_NOT_CANDIDATE` | Scène live utilisée seulement comme requête | Requête live | `INFO` |
| `B6_REVIEW_CANDIDATE` | Film mémoire à revoir | Film à revoir | `WATCH` |
| `MEMORY_NOT_COMPARABLE` | Mémoire non comparable | Non comparable | `INFO` |
| `MEMORY_PARTIAL_COMPARABLE` | Mémoire comparable partielle | Mémoire partielle | `WATCH` |
| `MEMORY_STRONG_COMPARABLE` | Mémoire fortement comparable | Mémoire forte | `ATTENTION` |
| `MEMORY_UNKNOWN` | Mémoire inconnue | Mémoire inconnue | `INFO` |
| `MEMORY_WEAK_COMPARABLE` | Mémoire faiblement comparable | Mémoire faible | `INFO` |

## price_verdict

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `ACCEPTED` | Accepté par le prix | Accepté | `ATTENTION` |
| `FAILED_RETEST` | Retest échoué | Retest échoué | `ATTENTION` |
| `HIGH_REJECTED` | Haut rejeté | Haut rejeté | `ATTENTION` |
| `LOWER_ACCEPTED` | Zone basse acceptée | Bas accepté | `ATTENTION` |
| `PENDING` | Prix en attente de verdict | En attente | `WATCH` |
| `PRICE_NOT_VISIBLE` | Prix non visible | Prix absent | `BLOCKER` |
| `REJECTED` | Rejeté par le prix | Rejeté | `ATTENTION` |
| `RETEST_ACCEPTED` | Retest accepté | Retest accepté | `ATTENTION` |
| `RETEST_PENDING` | Retest en attente | Retest attendu | `WATCH` |

## reality_board_payload_state

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `B9_LIVE_BRIEF_READY` | Brief B9 prêt pour affichage | Brief affichable | `INFO` |
| `BLOCKED_MISSING_INPUTS` | Affichage bloqué : entrées manquantes | Entrées manquantes | `BLOCKER` |
| `REALITY_BOARD_NOT_MUTATED_READ_ONLY` | Reality Board non modifié : read-only | Board non modifié | `INFO` |
| `REALITY_BOARD_PAYLOAD_BLOCKED` | Payload Reality Board bloqué | Payload bloqué | `BLOCKER` |
| `REALITY_BOARD_PAYLOAD_PARTIAL` | Payload Reality Board partiel | Payload partiel | `WATCH` |
| `REALITY_BOARD_PAYLOAD_READY` | Payload Reality Board prêt | Payload prêt | `INFO` |

## scene_role

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `CENTER_MIGRATION` | Migration de centre | Centre migré | `ATTENTION` |
| `CORRECTIVE_REBOUND_WITHOUT_PROGRESS` | Rebond correctif sans progrès | Correction sans progrès | `WATCH` |
| `EFFORT_RESULT_PROGRESS` | Effort / résultat / progrès | Effort-résultat | `INFO` |
| `FAILED_REINTEGRATION_ROLE` | Réintégration refusée | Retour refusé | `ATTENTION` |
| `HIGH_ZONE_REJECTION` | Rejet de zone haute | Rejet haut | `ATTENTION` |
| `LOW_ZONE_DEFENSE` | Défense de zone basse | Défense basse | `ATTENTION` |
| `PROGRESSIVE_FIRST_LEG` | Première jambe progressive | Première jambe | `ATTENTION` |
| `PROGRESSIVE_WAVE_MEMORY_SHIFT` | Vague progressive avec mémoire déplacée | Vague + mémoire | `ATTENTION` |
| `PROJECTION_REJECTED_THEN_MEMORY_SHIFTED` | Projection refusée puis mémoire déplacée | Projection refusée | `ATTENTION` |

## scene_state

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `B9_LIVE_BRIEF_READY` | Brief live B9 prêt | Brief prêt | `ATTENTION` |
| `BLOCKED_MISSING_INPUTS` | Brief bloqué : entrées manquantes | Entrées manquantes | `BLOCKER` |
| `SCENE_ACCEPTED` | Scène acceptée par le prix | Scène acceptée | `ATTENTION` |
| `SCENE_CANDIDATE` | Scène candidate | Scène candidate | `WATCH` |
| `SCENE_CONSUMED` | Scène consommée | Consommée | `INFO` |
| `SCENE_EXHAUSTED` | Scène essoufflée | Essoufflée | `WATCH` |
| `SCENE_PARTIAL` | Scène partielle | Partielle | `WATCH` |
| `SCENE_PENDING` | Scène en attente de jugement | En attente | `WATCH` |
| `SCENE_REJECTED` | Scène rejetée par le prix | Scène rejetée | `ATTENTION` |
| `SCENE_UNKNOWN` | Scène non qualifiée | Non qualifiée | `INFO` |

## scene_transition

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `ABSORPTION_ACCOMPANYING_PRESSURE` | Absorption qui accompagne la pression | Absorption accompagnante | `ATTENTION` |
| `CENTER_MIGRATION_DOWN` | Centre qui migre vers le bas | Centre descendant | `ATTENTION` |
| `CENTER_MIGRATION_UP` | Centre qui migre vers le haut | Centre montant | `ATTENTION` |
| `CORRECTIVE_BOUNCE` | Rebond correctif | Rebond correctif | `WATCH` |
| `CORRECTIVE_BOUNCE_WITHOUT_PROGRESS` | Rebond correctif sans progrès durable | Rebond sans progrès | `WATCH` |
| `EFFORT_WITHOUT_RESULT` | Effort sans résultat | Effort sans résultat | `WATCH` |
| `FAILED_REINTEGRATION` | Réintégration échouée | Réintégration échouée | `ATTENTION` |
| `HIGH_REJECTION` | Rejet de zone haute | Rejet haut | `ATTENTION` |
| `LOW_DEFENDED` | Zone basse défendue | Bas défendu | `ATTENTION` |
| `MEMORY_SHIFT_DOWN` | Mémoire déplacée vers le bas | Mémoire basse | `ATTENTION` |
| `MEMORY_SHIFT_UP` | Mémoire déplacée vers le haut | Mémoire haute | `ATTENTION` |
| `PROGRESSIVE_WAVE` | Vague progressive réelle | Vague progressive | `ATTENTION` |
| `PULLBACK_ABSORBED` | Pullback absorbé | Pullback absorbé | `ATTENTION` |
| `RELEASE_DOWN_ACCEPTED` | Release baissière acceptée | Release acceptée bas | `ATTENTION` |
| `RELEASE_UP_ACCEPTED` | Release haussière acceptée | Release acceptée haut | `ATTENTION` |
| `SECOND_LEG_DOWN` | Deuxième jambe baissière | Deuxième jambe basse | `ATTENTION` |
| `SECOND_LEG_UP` | Deuxième jambe haussière | Deuxième jambe haute | `ATTENTION` |

## source_quality_gate

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `M1_BAR_PROXY` | Lecture reconstruite M1 | M1 reconstruit | `WATCH` |
| `RAW_AGREEMENT_NOT_VISIBLE` | Accord raw non visible | Raw non visible | `WATCH` |
| `RAW_UNAVAILABLE_REJECTED` | Rejeté : raw indisponible | Raw indisponible | `BLOCKER` |
| `RECONSTRUCTED` | Donnée reconstruite | Reconstruit | `WATCH` |
| `SOURCE_QUALITY_DEGRADED` | Source dégradée | Source dégradée | `BLOCKER` |
| `SOURCE_QUALITY_LIVE_UNQUALIFIED` | Source live non qualifiée | Live non qualifié | `WATCH` |
| `SOURCE_QUALITY_PARTIAL` | Source partielle | Source partielle | `WATCH` |
| `SOURCE_QUALITY_USABLE` | Source exploitable | Source exploitable | `INFO` |
| `SOURCE_RAW_CONFIRMED` | Source confirmée par raw | Raw confirmé | `ATTENTION` |
| `SOURCE_RAW_NUANCED` | Source nuancée par raw | Raw nuancé | `WATCH` |

## telegram_gate_state

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `TELEGRAM_ALLOWED_PREVIEW_ONLY` | Prévisualisation Telegram autorisée | Prévisualisation | `INFO` |
| `TELEGRAM_BLOCKED_FORBIDDEN_LANGUAGE` | Telegram bloqué : langage interdit | Langage bloqué | `BLOCKER` |
| `TELEGRAM_BLOCKED_MISSING_INPUTS` | Telegram bloqué : entrées manquantes | Entrées manquantes | `BLOCKER` |
| `TELEGRAM_NOT_SENT_READ_ONLY` | Telegram non envoyé : mode read-only | Non envoyé | `INFO` |
| `TELEGRAM_READY_DRAFT_ONLY` | Message Telegram prêt en brouillon | Brouillon prêt | `INFO` |

## terrain_node

| Enum technique | Français trader | Court | Niveau |
|---|---|---|---|
| `ABSORPTION_NODE` | Node d’absorption | Node absorption | `WATCH` |
| `CENTER_MIGRATION_NODE` | Node de migration du centre | Node centre | `ATTENTION` |
| `EFFORT_WITHOUT_RESULT_NODE` | Node d’effort sans résultat | Node friction | `WATCH` |
| `FAILED_REINTEGRATION_NODE` | Node de réintégration échouée | Node retour échoué | `ATTENTION` |
| `HIGH_REJECTION_NODE` | Node de rejet haut | Node rejet haut | `ATTENTION` |
| `LOW_DEFENSE_NODE` | Node de défense basse | Node défense basse | `ATTENTION` |
| `PROGRESSIVE_REACTION_NODE` | Node de réaction progressive | Node progressif | `ATTENTION` |
| `UNKNOWN_TERRAIN_NODE` | Node terrain non qualifié | Node inconnu | `INFO` |
