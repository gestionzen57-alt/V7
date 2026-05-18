# B9 Reality Board Read Model V0

**Version :** `T0160_T0161_B9_REALITY_BOARD_READ_MODEL_V0`
**Généré UTC :** `2026-05-18T16:20:26Z`

## Contrat

```text
Read-only.
Aucun dashboard live branché.
Aucune écriture powerflow.db / tick_archive.db.
Aucun Telegram.
Aucun PRESSION_UP_SOURCE_NEUTRALISEE/PRESSION_DOWN_SOURCE_NEUTRALISEE.
Aucune probabilité de succès.
Aucun bouton décision.
Le dashboard affiche, il ne décide pas.
```

## Ce que B9 voit

B6 trouve des films proches, mais le contexte faux positif reste élevé. Comparer, ne pas projeter.

**Preuves / indices source**
- B9 voit une vague progressive acceptée, mais la mémoire comparable porte un piège technique fort.

## État de scène

SCENE_ACCEPTED

- **scene_id** : NON_RENSEIGNE
- **scene_role** : PROGRESSIVE_FIRST_LEG
- **session_chapter** : NON_RENSEIGNE

## Transition

{"ABSORPTION_ACCOMPANYING_PRESSURE": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "L’absorption ne bloque pas le mouvement ; elle accompagne le déplacement.", "key": "ABSORPTION_ACCOMPANYING_PRESSURE", "label_fr": "Absorption qui accompagne la pression", "short_fr": "Absorption accompagnante", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "CENTER_MIGRATION_DOWN": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "La mémoire interne se déplace par paliers vers une zone inférieure.", "key": "CENTER_MIGRATION_DOWN", "label_fr": "Centre qui migre vers le bas", "short_fr": "Centre descendant", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "CENTER_MIGRATION_UP": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "La mémoire interne se déplace par paliers vers une zone supérieure.", "key": "CENTER_MIGRATION_UP", "label_fr": "Centre qui migre vers le haut", "short_fr": "Centre montant", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "CORRECTIVE_BOUNCE": {"attention_level": "WATCH", "category": "scene_transition", "explanation_fr": "Le prix respire mais ne prouve pas encore un progrès durable.", "key": "CORRECTIVE_BOUNCE", "label_fr": "Rebond correctif", "short_fr": "Rebond correctif", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "CORRECTIVE_BOUNCE_WITHOUT_PROGRESS": {"attention_level": "WATCH", "category": "scene_transition", "explanation_fr": "Le rebond corrige localement mais ne déplace pas la mémoire.", "key": "CORRECTIVE_BOUNCE_WITHOUT_PROGRESS", "label_fr": "Rebond correctif sans progrès durable", "short_fr": "Rebond sans progrès", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "EFFORT_WITHOUT_RESULT": {"attention_level": "WATCH", "category": "scene_transition", "explanation_fr": "Le flux dépense de l’énergie mais ne gagne pas de terrain mesurable.", "key": "EFFORT_WITHOUT_RESULT", "label_fr": "Effort sans résultat", "short_fr": "Effort sans résultat", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "FAILED_REINTEGRATION": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le prix tente de revenir dans une zone mais n’y conserve pas de centre stable.", "key": "FAILED_REINTEGRATION", "label_fr": "Réintégration échouée", "short_fr": "Réintégration échouée", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "HIGH_REJECTION": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le haut travaillé n’est pas accepté et la mémoire reste fragile.", "key": "HIGH_REJECTION", "label_fr": "Rejet de zone haute", "short_fr": "Rejet haut", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "LOW_DEFENDED": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "L’effort opposé ne parvient pas à déplacer la mémoire sous la zone.", "key": "LOW_DEFENDED", "label_fr": "Zone basse défendue", "short_fr": "Bas défendu", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "MEMORY_SHIFT_DOWN": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le flux imprime une nouvelle mémoire sous la zone précédente.", "key": "MEMORY_SHIFT_DOWN", "label_fr": "Mémoire déplacée vers le bas", "short_fr": "Mémoire basse", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "MEMORY_SHIFT_UP": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le flux imprime une nouvelle mémoire au-dessus de la zone précédente.", "key": "MEMORY_SHIFT_UP", "label_fr": "Mémoire déplacée vers le haut", "short_fr": "Mémoire haute", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "PROGRESSIVE_WAVE": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "L’effort produit du résultat et déplace la mémoire.", "key": "PROGRESSIVE_WAVE", "label_fr": "Vague progressive réelle", "short_fr": "Vague progressive", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "PULLBACK_ABSORBED": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le retour contre le mouvement ne reprend pas la mémoire précédente.", "key": "PULLBACK_ABSORBED", "label_fr": "Pullback absorbé", "short_fr": "Pullback absorbé", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "RELEASE_DOWN_ACCEPTED": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le prix accepte la projection inférieure après tension libérée.", "key": "RELEASE_DOWN_ACCEPTED", "label_fr": "Release baissière acceptée", "short_fr": "Release acceptée bas", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "RELEASE_UP_ACCEPTED": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Le prix accepte la projection supérieure après tension libérée.", "key": "RELEASE_UP_ACCEPTED", "label_fr": "Release haussière acceptée", "short_fr": "Release acceptée haut", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "SECOND_LEG_DOWN": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Après rejet ou counter-breath échoué, une nouvelle jambe prolonge le déplacement bas.", "key": "SECOND_LEG_DOWN", "label_fr": "Deuxième jambe baissière", "short_fr": "Deuxième jambe basse", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}, "SECOND_LEG_UP": {"attention_level": "ATTENTION", "category": "scene_transition", "explanation_fr": "Après pullback absorbé, une nouvelle jambe prolonge le déplacement haut.", "key": "SECOND_LEG_UP", "label_fr": "Deuxième jambe haussière", "short_fr": "Deuxième jambe haute", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}}

## Zone active

{"zone_high": 1.33742, "zone_label": "zone de progression 10:00-10:23", "zone_low": 1.33506}

- **zone_low** : 1.33506
- **zone_high** : 1.33742
- **zone_center** : {"attention_level": "ATTENTION", "category": "scene_role", "explanation_fr": "Le centre de gravité de la scène se déplace par paliers.", "key": "CENTER_MIGRATION", "label_fr": "Migration de centre", "short_fr": "Centre migré", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}

## Node terrain

{"node_id": "NODE_20260515_1000_1023", "node_role": "PROGRESSIVE_REACTION_NODE"}

## Verdict prix

ACCEPTED

## Mémoire B6 proche

{"attention_level": "BLOCKER", "category": "false_positive_context", "explanation_fr": "B6 rapproche les formes, T0117 signale une forte fragilité de comparaison.", "key": "B6_FALSE_POSITIVE_CONTEXT_HIGH", "label_fr": "Film proche, mais piège technique fort", "short_fr": "Piège fort", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}

## Similarités

- Similarités non renseignées.

## Différences

- Différences non renseignées.

## Pièges techniques

- ['Source live candidate encore unqualified côté raw texture.', 'Contexte faux positif HIGH : mémoire proche mais fragile.', 'force_snapshots_v2 vide sur le run local observé.']
- Source live candidate encore unqualified côté raw texture.
- Contexte faux positif HIGH : mémoire proche mais fragile.
- force_snapshots_v2 vide sur le run local observé.

## Source quality

Mode source=UNKNOWN_SOURCE_MODE | visibilité=UNKNOWN_VISIBILITY | cap=NON_RENSEIGNE | statut=DEGRADED

| Entrée | Statut | Chemin | SHA |
|---|---|---|---|
| `integration_candidate` | `OK` | `outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json` | `f999a2baadb9765b` |
| `trader_attention_packet` | `MISSING` | `outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json` | `None` |
| `live_brief` | `MISSING` | `outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json` | `None` |
| `latest_scene_candidate` | `MISSING` | `outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json` | `None` |
| `french_event_display_contract` | `OK` | `outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json` | `2968c3d6e4f2f1a3` |

## Ce qu’il faut surveiller ensuite

- Surveiller le prochain retest et la cohérence du centre interne avant de durcir la lecture.

## Ce que B9 ne peut pas conclure

- {"attention_level": "INFO", "category": "memory_confidence_ladder", "explanation_fr": "La mémoire n’est pas disponible ou pas encore construite.", "key": "MEMORY_UNKNOWN", "label_fr": "Mémoire inconnue", "short_fr": "Mémoire inconnue", "technical_limit_fr": "Contrat de traduction ; ne modifie aucune logique moteur.", "trader_usage_fr": "Affichage seulement : perception à lire, décision trader."}
- memory_confidence_ladder
- MEMORY_UNKNOWN
- Mémoire inconnue
- La mémoire n’est pas disponible ou pas encore construite.
- INFO
- Affichage seulement : perception à lire, décision trader.
- Contrat de traduction ; ne modifie aucune logique moteur.
- Lecture complète impossible : entrées manquantes = trader_attention_packet, live_brief, latest_scene_candidate
