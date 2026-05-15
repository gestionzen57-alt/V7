# T006-F1B - Corrected wording hit triage with context

Date: 2026-05-15 23:20:46 +02:00
Mission: correct broken T006-F1 report and provide full context for T006-E wording hits
Status: T006_F1B_TRIAGE_CORRECTED_COMPLETE

## Correction note

- Previous T006-F1 report was incomplete because PowerShell parsing failed while writing context rows.
- This T006-F1B report supersedes the incomplete T006-F1 report.
- No source wording is patched in this step.

## Superseded report

- Docs\Checkpoints\T006_F1_WORDING_HIT_TRIAGE_20260515_231540.md

## Source audit report

- Docs\Checkpoints\T006_E_DASHBOARD_PACKET_WORDING_AUDIT_20260515_230602.md

## Metrics

- Raw T006-E hit lines: 79
- Parsed hits: 79
- Context rows: 160

## Class summary

- NEEDS_MANUAL_REVIEW: 86
- CODE_OR_TEMPLATE_REVIEW: 68
- LIKELY_DATA_OR_CONFIG_REVIEW: 3
- COMMENT_OR_DOC_REVIEW: 3

## Interpretation rule

- Hits are potential violations only.
- Historical docs, comments, JSON data, and code/template strings may be false positives.
- T006-F2 must patch only confirmed trader-facing wording violations.
- T006-F2 must not patch archived/historical evidence unless it is actively used in dashboard or packet output.

## Context rows

---

### Core\AVANT\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L12: - Ne pas modifier capture_bridge.py ni pf_temporal_node_state.py
   L13: - NODE_HEAT â‰  CURRENCY_ENERGY
>> L14: - Energy ne produit jamais BUY/SELL ni HOT seule
   L15: - COUNTER_RELEASE_ATTEMPT â‰  RELEASE_CONFIRMED
   L16: - Pas de first_detachment = pas de release confirmÃ©e
~~~

---

### Core\AVANT\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 128
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L126:     - is_present = False â†’ tous les checkers energy sont silencieux
   L127:     - node_energy_relation est observationnel â€” jamais un signal
>> L128:     - Energy ne produit jamais HOT ni BUY/SELL
   L129:     """
   L130:     source: str = "NONE"  # "energy_context" | "energy_release_alignment" | "standalone" | "NONE"
~~~

---

### Core\AVANT\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 838
- Class: COMMENT_OR_DOC_REVIEW

~~~text
   L836: # Signature : (rg: dict) â†’ BehavioralAlert | None
   L837: # RÃ¨gle absolue : jamais de HOT si topline_reliable == False
>> L838: # Jamais de BUY/SELL. Jamais de DB. Jamais de Telegram direct.
   L839: # ---------------------------------------------------------------------------
   L840: 
~~~

---

### Core\backups\dashboard_cleanup\20260511_082526\DASHBOARD_V72_MAX_HARDENING_REPORT.md

- Pattern: certain
- Line: 12
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L10: 
   L11: - Les 4 WARN `FORBIDDEN_*` sont des faux positifs du validateur V0.1 : il scannait aussi les phrases doctrinales nÃ©gatives du type â€œPas de BUY/SELLâ€.
>> L12: - Les 3 WARN `NO_TIMESTAMP_IN_JSON` sont de vrais risques techniques de surface : certains JSON lus nâ€™exposent pas de timestamp UTC parseable.
   L13: - Les 10 sources manquantes du dashboard ne sont pas une panne moteur. Elles signalent une diffÃ©rence entre les outputs directs attendus et les agrÃ©gats post-P0 disponibles.
   L14: 
~~~

---

### Core\backups\dashboard_cleanup\20260511_082526\DASHBOARD_V72_SURFACE_V4_REPORT.md

- Pattern: certain
- Line: 5
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L3: ## DÃ©cision
   L4: 
>> L5: La V3 a bien isolÃ© le dashboard dans `output/dashboard_surface/`, mais elle a rÃ©vÃ©lÃ© un dÃ©faut de surface : certains fichiers directs existaient dÃ©jÃ  sous forme de placeholders `MISSING` et masquaient les informations disponibles dans les agrÃ©gats post-P0.
   L6: 
   L7: La V4 corrige ce point sans toucher au moteur.
~~~

---

### Core\backups\dashboard_cleanup\20260511_082526\P0_DASHBOARD_GO_NO_GO_CHECKLIST.md

- Pattern: sell
- Line: 100
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L98:   - Memory est formulÃ©e comme probabilitÃ© de succÃ¨s.
   L99:   - Les attributs data-* obligatoires manquent sur cartes.
>> L100:   - Des BUY/SELL apparaissent dans l'interface.
   L101: ```
   L102: 
~~~

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\docs\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 19
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L17: | JSON polling | âœ… PASS | RafraÃ®chissement contractuel via `output/dashboard_surface/*.json`, refresh 30s. |
   L18: | MISSING / STALE / DEGRADED | âœ… PASS | Ã‰tats explicites, jamais blanc, jamais recyclage silencieux. |
>> L19: | No BUY/SELL | âœ… PASS | Aucune dÃ©cision trade affichÃ©e. |
   L20: | No memory as probability | âœ… PASS | B6 affichÃ© comme frÃ©quence historique / occurrence / distribution, pas probabilitÃ© de succÃ¨s. |
   L21: | Technical risks exposed | âœ… PASS | Les risques techniques sont montrÃ©s, pas utilisÃ©s pour censurer. |
~~~

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\docs\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 92
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L90: âœ… Pas de fusion B1/B1+
   L91: âœ… Pas de fusion B4/B4+
>> L92: âœ… Pas de BUY/SELL
   L93: âœ… Pas de dÃ©cision trader
   L94: âœ… Pas dâ€™Ã©criture DB
~~~

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\runtime\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 19
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L17: | JSON polling | âœ… PASS | RafraÃ®chissement contractuel via `output/dashboard_surface/*.json`, refresh 30s. |
   L18: | MISSING / STALE / DEGRADED | âœ… PASS | Ã‰tats explicites, jamais blanc, jamais recyclage silencieux. |
>> L19: | No BUY/SELL | âœ… PASS | Aucune dÃ©cision trade affichÃ©e. |
   L20: | No memory as probability | âœ… PASS | B6 affichÃ© comme frÃ©quence historique / occurrence / distribution, pas probabilitÃ© de succÃ¨s. |
   L21: | Technical risks exposed | âœ… PASS | Les risques techniques sont montrÃ©s, pas utilisÃ©s pour censurer. |
~~~

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\runtime\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 92
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L90: âœ… Pas de fusion B1/B1+
   L91: âœ… Pas de fusion B4/B4+
>> L92: âœ… Pas de BUY/SELL
   L93: âœ… Pas de dÃ©cision trader
   L94: âœ… Pas dâ€™Ã©criture DB
~~~

---

### Core\backups\post_pass_strict_cleanup_20260511_130018\_squad2_docs_final\docs\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: 100%
- Line: 252
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L250: 
   L251: ```text
>> L252: DÃ©clencheur : PENDING_DATA_WINDOW â†’ 100%
   L253: Statut attendu : PASS_STRICT
   L254: Commit attendu : P0: promote strict validation from pending data window to PASS_STRICT
~~~

---

### Core\backups\post_pass_strict_cleanup_20260511_130018\_squad2_docs_final\docs\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: sell
- Line: 186
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L184: âœ… Aucune Ã©criture manuelle powerflow.db
   L185: âœ… Dual regime/density prÃ©servÃ©s
>> L186: âœ… No BUY/SELL injected
   L187: âœ… Technical risks explicit
   L188: âœ… Memory reste frÃ©quence historique, pas prÃ©diction
~~~

---

### Core\backups\post_pass_strict_cleanup_20260511_130018\_squad2_docs_final\docs\CLAUDE_md_V72_FINAL_UPDATE.md

- Pattern: 100%
- Line: 223
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L221: 
   L222: ```text
>> L223: Quand PENDING_DATA_WINDOW atteint 100%.
   L224: Quand market_open_validator / P0 strict passe naturellement en PASS_STRICT.
   L225: ```
~~~

---

### Core\backups\post_session_dashboard_commit_20260511_164455\_docs_pass_strict_update\docs\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: sell
- Line: 145
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L143: âœ… Aucune Ã©criture manuelle powerflow.db
   L144: âœ… Dual regime/density prÃ©servÃ©s
>> L145: âœ… No BUY/SELL injected
   L146: âœ… Technical risks explicit
   L147: âœ… Memory reste frÃ©quence historique, pas prÃ©diction
~~~

---

### Core\backups\post_session_dashboard_commit_20260511_164455\RAPPORT_COMPLET_POWERFLOW_V721_B1HMM_MTF_B4WAVELET_SCHEMAFLEX_20260511.md

- Pattern: certain
- Line: 23
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L21: 1. `hmmlearn` ne s'installait pas sous Python 3.14 sans toolchain C++.
   L22: 2. Le moteur attendait initialement un schÃ©ma DB trop strict.
>> L23: 3. Le script one-click marquait certaines Ã©tapes en `PASS` malgrÃ© des erreurs runtime.
   L24: 
   L25: Le hotfix final `71c2f91` corrige ces points.
~~~

---

### Core\backups\post_session_dashboard_commit_20260511_164455\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 9
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L7: **Statut :** VALIDE / PUSHE / ACTIVE  
   L8: **Architecture :** Dual perception - jamais fusionnee  
>> L9: **Doctrine :** Perception, mesure, qualification technique. Aucun BUY/SELL.
   L10: 
   L11: ---
~~~

---

### Core\backups\post_session_dashboard_commit_20260511_164455\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 475
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L473: Aucune dependance circulaire introduite.
   L474: Aucune ecriture DB introduite.
>> L475: Aucun BUY/SELL introduit.
   L476: Aucune fusion dual introduite.
   L477: 
~~~

---

### Core\CHECKPOINT_P0_LIVE_20260511.md

- Pattern: 100%
- Line: 119
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L117: 
   L118: ```text
>> L119: Date cible : 2026-05-12 ou dÃ¨s PENDING_DATA_WINDOW = 100%.
   L120: Verdict attendu : PASS_STRICT ou progression continue documentÃ©e.
   L121: ```
~~~

---

### Core\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: sell
- Line: 145
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L143: âœ… Aucune Ã©criture manuelle powerflow.db
   L144: âœ… Dual regime/density prÃ©servÃ©s
>> L145: âœ… No BUY/SELL injected
   L146: âœ… Technical risks explicit
   L147: âœ… Memory reste frÃ©quence historique, pas prÃ©diction
~~~

---

### Core\CURRENT_STATE_V7_POST_P0_UPDATE.md

- Pattern: sell
- Line: 235
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L233: Ne pas importer cockpit_* depuis pf_*.
   L234: Ne pas crÃ©er de dÃ©pendance circulaire.
>> L235: Ne pas produire BUY/SELL dans les alertes.
   L236: Ne pas censurer alerte M1 par prudence.
   L237: ```
~~~

---

### Core\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 19
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L17: | JSON polling | âœ… PASS | RafraÃ®chissement contractuel via `output/dashboard_surface/*.json`, refresh 30s. |
   L18: | MISSING / STALE / DEGRADED | âœ… PASS | Ã‰tats explicites, jamais blanc, jamais recyclage silencieux. |
>> L19: | No BUY/SELL | âœ… PASS | Aucune dÃ©cision trade affichÃ©e. |
   L20: | No memory as probability | âœ… PASS | B6 affichÃ© comme frÃ©quence historique / occurrence / distribution, pas probabilitÃ© de succÃ¨s. |
   L21: | Technical risks exposed | âœ… PASS | Les risques techniques sont montrÃ©s, pas utilisÃ©s pour censurer. |
~~~

---

### Core\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 92
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L90: âœ… Pas de fusion B1/B1+
   L91: âœ… Pas de fusion B4/B4+
>> L92: âœ… Pas de BUY/SELL
   L93: âœ… Pas de dÃ©cision trader
   L94: âœ… Pas dâ€™Ã©criture DB
~~~

---

### Core\docs\2026\2026-05\RAPPORT_MULTISYMBOL_SCHEDULER_20260511.md

- Pattern: sell
- Line: 74
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L72: âœ… EURUSD / USDJPY extensions opÃ©rationnelles
   L73: âœ… Cross-validation sÃ©parÃ©e des outputs par symbole
>> L74: âœ… Aucun BUY/SELL ajoutÃ©
   L75: âœ… pf_* reste moteur, pas cockpit
   L76: âœ… Scheduler pilotÃ© par config / CLI
~~~

---

### Core\docs\RAPPORT_TRADER_ALERT_STATE_V01_COMPLETE.md

- Pattern: sell
- Line: 175
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L173: | ScÃ¨ne < 3 lignes | âœ… | Message = 2 lignes max |
   L174: | FranÃ§ais court | âœ… | Termes courts, pas jargon |
>> L175: | Pas BUY/SELL | âœ… | ZÃ©ro mention direction trade |
   L176: | HOT â‰  confirmed | âœ… | Champ `not_confirmed_reason` visible |
   L177: | Grouper alertes | âœ… | Familles auto-dÃ©tectÃ©es |
~~~

---

### Core\docs\RAPPORT_TRADER_ALERT_STATE_V01_COMPLETE.md

- Pattern: sell
- Line: 277
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L275: - âœ… Contradictions dÃ©tectÃ©es
   L276: - âœ… Runtime context intÃ©grÃ©
>> L277: - âœ… Aucune mention BUY/SELL
   L278: - âœ… HOT avec `not_confirmed_reason` si applicable
   L279: 
~~~

---

### Core\docs\RAPPORT_TRADER_ALERT_STATE_V01_COMPLETE.md

- Pattern: sell
- Line: 331
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L329: - âœ… Contradictions visibles
   L330: - âœ… Freshness tracking
>> L331: - âœ… Pas BUY/SELL
   L332: - âœ… FranÃ§ais naturel
   L333: - âœ… ZÃ©ro spam
~~~

---

### Core\P0_FINAL_ARCHITECT_DECISION.md

- Pattern: 100%
- Line: 97
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L95: 2. Relancer validation P0 toutes les heures si besoin statut.
   L96: 3. Surveiller progression fenÃªtre : TF1 >= 50, TF5 >= 20, TF15 >= 10.
>> L97: 4. Quand PENDING_DATA_WINDOW atteint 100%, relancer P0 final validator.
   L98: 5. Documenter Ã©volution vers PASS_STRICT si elle apparaÃ®t.
   L99: ```
~~~

---

### Core\patch_dashboard_v75f_session_full_width.py

- Pattern: 100%
- Line: 11
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L9: <style id="pf75f-session-full-width-style">
   L10: #sessionMemory {
>> L11:   width: 100% !important;
   L12:   max-width: none !important;
   L13:   grid-column: 1 / -1 !important;
~~~

---

### Core\patch_dashboard_v75f_session_full_width.py

- Pattern: 100%
- Line: 19
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L17: 
   L18: #sessionMemory table {
>> L19:   width: 100% !important;
   L20:   table-layout: auto !important;
   L21: }
~~~

---

### Core\patch_dashboard_v75f_session_full_width.py

- Pattern: 100%
- Line: 38
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L36: 
   L37: #sessionMemory details {
>> L38:   width: 100%;
   L39:   box-sizing: border-box;
   L40: }
~~~

---

### Core\patch_dashboard_v75f_session_full_width.py

- Pattern: 100%
- Line: 44
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L42: #sessionMemory .session-scroll {
   L43:   overflow-x: auto;
>> L44:   width: 100%;
   L45: }
   L46: </style>
~~~

---

### Core\patch_dashboard_v75f_session_full_width.py

- Pattern: 100%
- Line: 61
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L59:   session.classList.add("wide");
   L60:   session.style.gridColumn = "1 / -1";
>> L61:   session.style.width = "100%";
   L62: 
   L63:   for (const table of session.querySelectorAll("table")) {
~~~

---

### Core\PATCH_LEXIQUE_POWERFLOW_V76_ALERT_GATE_20260513.md

- Pattern: certain
- Line: 270
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L268: 
   L269: ```text
>> L270: Certaines preuves temporelles manquent pour le symbole.
   L271: ```
   L272: 
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: buy
- Line: 137
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L135: 
   L136:     if b6["action"] == "WAKE_TRADER":
>> L137:         if "SHORT" in daily_intent and b6["direction"] == "BUY_SIDE":
   L138:             final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
   L139:             final_message = "B6 charge BUY alors que le daily lit un piège/distribution baissier possible. Surveiller réintégration ou piège inverse."
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: buy
- Line: 139
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L137:         if "SHORT" in daily_intent and b6["direction"] == "BUY_SIDE":
   L138:             final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
>> L139:             final_message = "B6 charge BUY alors que le daily lit un piège/distribution baissier possible. Surveiller réintégration ou piège inverse."
   L140:         elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
   L141:             final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: sell
- Line: 140
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L138:             final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
   L139:             final_message = "B6 charge BUY alors que le daily lit un piège/distribution baissier possible. Surveiller réintégration ou piège inverse."
>> L140:         elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
   L141:             final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
   L142:             final_message = "B6 charge SELL dans le sens du daily trap/downside acceptance. Attention précoce renforcée."
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: sell
- Line: 142
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L140:         elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
   L141:             final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
>> L142:             final_message = "B6 charge SELL dans le sens du daily trap/downside acceptance. Attention précoce renforcée."
   L143:         else:
   L144:             final_synthesis = "B6_EARLY_TENSION_PRESENT"
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L12: - Ne pas modifier capture_bridge.py ni pf_temporal_node_state.py
   L13: - NODE_HEAT â‰  CURRENCY_ENERGY
>> L14: - Energy ne produit jamais BUY/SELL ni HOT seule
   L15: - COUNTER_RELEASE_ATTEMPT â‰  RELEASE_CONFIRMED
   L16: - Pas de first_detachment = pas de release confirmÃ©e
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 144
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L142:     - is_present = False â†’ tous les checkers energy sont silencieux
   L143:     - node_energy_relation est observationnel â€” jamais un signal
>> L144:     - Energy ne produit jamais HOT ni BUY/SELL
   L145:     """
   L146:     source: str = "NONE"  # "energy_context" | "energy_release_alignment" | "standalone" | "NONE"
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 959
- Class: COMMENT_OR_DOC_REVIEW

~~~text
   L957: # Signature : (rg: dict) â†’ BehavioralAlert | None
   L958: # RÃ¨gle absolue : jamais de HOT si topline_reliable == False
>> L959: # Jamais de BUY/SELL. Jamais de DB. Jamais de Telegram direct.
   L960: # ---------------------------------------------------------------------------
   L961: 
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1356
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1354:         "db_write": False,
   L1355:         "telegram_send": False,
>> L1356:         "buy_sell_output": False,
   L1357:         "p1_2_guard_aware": True,
   L1358:         "p_next_4_eie_queue_reader": True,
~~~

---

### Core\pf_cross_symbol_validation.py

- Pattern: sell
- Line: 11
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L9: --------
   L10: This module is a perception engine. It names and qualifies a driver.
>> L11: It never emits BUY/SELL instructions and never writes to the database.
   L12: """
   L13: 
~~~

---

### Core\pf_engine_scenes.py

- Pattern: entree automatique
- Line: 433
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L431:     if scene_type == "TREND_CONTINUATION":
   L432:         return "Flux propre; chercher continuation apres respiration."
>> L433:     return "Surveiller, pas d'entree automatique."
   L434: 
   L435: 
~~~

---

### Core\pf_lab_engine_v72.py

- Pattern: certain
- Line: 844
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L842:             "- No trade decision.",
   L843:             "- No filtering.",
>> L844:             "- Footprints are candidates, never institutional certainties.",
   L845:             "",
   L846:             "## Scene distribution",
~~~

---

### Core\pf_memory.py

- Pattern: certain
- Line: 545
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L543: 
   L544:     if confirmed >= 3:
>> L545:         lessons.append("Les postures Cockpit semblent protÃ©ger correctement certaines dÃ©cisions confirmÃ©es.")
   L546:     if invalidated >= 2:
   L547:         lessons.append("Plusieurs lectures ont Ã©tÃ© invalidÃ©es : renforcer les confirmations avant de passer de WATCH Ã  ARMED.")
~~~

---

### Core\RAPPORT_SESSION_POWERFLOW_V76_ALERT_GATE_20260513.md

- Pattern: certain
- Line: 513
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L511: ```
   L512: 
>> L513: Certaines surfaces temporelles incomplÃ¨tes.
   L514: 
   L515: ```text
~~~

---

### Core\RAPPORT_SESSION_POWERFLOW_V76_ALERT_GATE_20260513.md

- Pattern: certain
- Line: 519
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L517: ```
   L518: 
>> L519: Couverture cross-pair B8 insuffisante pour certaines synthÃ¨ses.
   L520: 
   L521: ---
~~~

---

### Core\REGISTRE_BRIQUES_PATCH_SIGNAL_ADAPTIVE_PROFILE.md

- Pattern: sell
- Line: 9
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L7: Sorties : profils signal adaptatifs par symbole  
   L8: DB write : non  
>> L9: BUY/SELL : non
   L10: 
   L11: ## Runner : run_signal_adaptive_profile_once.py
~~~

---

### Core\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 9
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L7: **Statut :** VALIDE / PUSHE / ACTIVE  
   L8: **Architecture :** Dual perception - jamais fusionnee  
>> L9: **Doctrine :** Perception, mesure, qualification technique. Aucun BUY/SELL.
   L10: 
   L11: ---
~~~

---

### Core\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 475
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L473: Aucune dependance circulaire introduite.
   L474: Aucune ecriture DB introduite.
>> L475: Aucun BUY/SELL introduit.
   L476: Aucune fusion dual introduite.
   L477: 
~~~

---

### Core\scheduler_powerflow_turbo_wrapper.py

- Pattern: sell
- Line: 12
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L10: Doctrine:
   L11: - Read-only analytical layers after the scheduler core.
>> L12: - No trade decision, no BUY/SELL output.
   L13: - M1 is qualified, never censored.
   L14: - V7.3 topdown stack: HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS.
~~~

---

### Core\telegram_trader_alert_v01.py

- Pattern: achete
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L46: # Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
   L47: FORBIDDEN_SIGNAL_WORDS = re.compile(
>> L48:     r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
   L49:     flags=re.IGNORECASE,
   L50: )
~~~

---

### Core\telegram_trader_alert_v01.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L12: - never reads or writes powerflow.db
   L13: - does not import pf_* or cockpit_*
>> L14: - does not emit BUY/SELL wording
   L15: """
   L16: 
~~~

---

### Core\telegram_trader_alert_v01.py

- Pattern: sell
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L46: # Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
   L47: FORBIDDEN_SIGNAL_WORDS = re.compile(
>> L48:     r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
   L49:     flags=re.IGNORECASE,
   L50: )
~~~

---

### Core\telegram_trader_alert_v01_1.py

- Pattern: achete
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L46: # Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
   L47: FORBIDDEN_SIGNAL_WORDS = re.compile(
>> L48:     r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
   L49:     flags=re.IGNORECASE,
   L50: )
~~~

---

### Core\telegram_trader_alert_v01_1.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L12: - never reads or writes powerflow.db
   L13: - does not import pf_* or cockpit_*
>> L14: - does not emit BUY/SELL wording
   L15: """
   L16: 
~~~

---

### Core\telegram_trader_alert_v01_1.py

- Pattern: sell
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L46: # Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
   L47: FORBIDDEN_SIGNAL_WORDS = re.compile(
>> L48:     r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
   L49:     flags=re.IGNORECASE,
   L50: )
~~~

---

### Core\telegram_trader_alert_v01_2.py

- Pattern: achete
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L46: # Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
   L47: FORBIDDEN_SIGNAL_WORDS = re.compile(
>> L48:     r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
   L49:     flags=re.IGNORECASE,
   L50: )
~~~

---

### Core\telegram_trader_alert_v01_2.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L12: - never reads or writes powerflow.db
   L13: - does not import pf_* or cockpit_*
>> L14: - does not emit BUY/SELL wording
   L15: """
   L16: 
~~~

---

### Core\telegram_trader_alert_v01_2.py

- Pattern: sell
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L46: # Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
   L47: FORBIDDEN_SIGNAL_WORDS = re.compile(
>> L48:     r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
   L49:     flags=re.IGNORECASE,
   L50: )
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 532
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L530: 
   L531: 
>> L532: def test_film_steps_energy_label_not_buy_sell():
   L533:     """film_steps ne contient pas BUY ni SELL â€” Energy n'est pas un signal."""
   L534:     tns = _make_tns()
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 533
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L531: 
   L532: def test_film_steps_energy_label_not_buy_sell():
>> L533:     """film_steps ne contient pas BUY ni SELL â€” Energy n'est pas un signal."""
   L534:     tns = _make_tns()
   L535:     energy = _make_energy()
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 538
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L536:     out = map_behavioral_alerts(tns, energy)
   L537:     for step in out["film_steps"]:
>> L538:         _assert("BUY" not in step, f"film_step ne doit pas contenir BUY: {step}")
   L539:         _assert("SELL" not in step, f"film_step ne doit pas contenir SELL: {step}")
   L540:     print("[OK] test_film_steps_energy_label_not_buy_sell")
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 540
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L538:         _assert("BUY" not in step, f"film_step ne doit pas contenir BUY: {step}")
   L539:         _assert("SELL" not in step, f"film_step ne doit pas contenir SELL: {step}")
>> L540:     print("[OK] test_film_steps_energy_label_not_buy_sell")
   L541: 
   L542: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 556
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L554: 
   L555: 
>> L556: def test_no_buy_sell_in_any_output():
   L557:     """Aucune alerte ne contient BUY ou SELL."""
   L558:     tns = _make_tns(
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 557
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L555: 
   L556: def test_no_buy_sell_in_any_output():
>> L557:     """Aucune alerte ne contient BUY ou SELL."""
   L558:     tns = _make_tns(
   L559:         highest_level="HOT_NODE",
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 569
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L567:         for field in ("reason", "dashboard_badge", "telegram_text"):
   L568:             v = a.get(field, "")
>> L569:             _assert("BUY" not in v, f"Alerte {a['name']} contient BUY dans {field}")
   L570:             _assert("SELL" not in v, f"Alerte {a['name']} contient SELL dans {field}")
   L571:     print("[OK] test_no_buy_sell_in_any_output")
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 571
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L569:             _assert("BUY" not in v, f"Alerte {a['name']} contient BUY dans {field}")
   L570:             _assert("SELL" not in v, f"Alerte {a['name']} contient SELL dans {field}")
>> L571:     print("[OK] test_no_buy_sell_in_any_output")
   L572: 
   L573: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1097
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1095: 
   L1096: 
>> L1097: def test_energy_context_no_buy_sell():
   L1098:     """Aucune alerte ne contient BUY ni SELL avec energy_context."""
   L1099:     tns = _make_tns_with_energy_context()
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1098
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1096: 
   L1097: def test_energy_context_no_buy_sell():
>> L1098:     """Aucune alerte ne contient BUY ni SELL avec energy_context."""
   L1099:     tns = _make_tns_with_energy_context()
   L1100:     out = map_behavioral_alerts(tns, None)
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1104
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1102:         for f_key in ("reason", "dashboard_badge", "telegram_text"):
   L1103:             v = a.get(f_key, "")
>> L1104:             _assert("BUY" not in v, f"{a['name']}.{f_key} contient BUY")
   L1105:             _assert("SELL" not in v, f"{a['name']}.{f_key} contient SELL")
   L1106:     print("[OK] test_energy_context_no_buy_sell")
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1106
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1104:             _assert("BUY" not in v, f"{a['name']}.{f_key} contient BUY")
   L1105:             _assert("SELL" not in v, f"{a['name']}.{f_key} contient SELL")
>> L1106:     print("[OK] test_energy_context_no_buy_sell")
   L1107: 
   L1108: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1151
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1149:     test_same_angle_not_triggered_on_no_cluster,
   L1150:     test_film_steps_present,
>> L1151:     test_film_steps_energy_label_not_buy_sell,
   L1152:     test_next_watch_enriched,
   L1153:     test_no_buy_sell_in_any_output,
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1153
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1151:     test_film_steps_energy_label_not_buy_sell,
   L1152:     test_next_watch_enriched,
>> L1153:     test_no_buy_sell_in_any_output,
   L1154:     test_degraded_alerts_in_dedicated_key,
   L1155:     test_counter_release_not_confirmed,
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1183
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1181:     # V0.8.2.1 â€” garde-fous
   L1182:     test_energy_context_never_produces_hot,
>> L1183:     test_energy_context_no_buy_sell,
   L1184:     test_counter_release_never_becomes_confirmed,
   L1185: ]
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 532
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L530: 
   L531: 
>> L532: def test_film_steps_energy_label_not_buy_sell():
   L533:     """film_steps ne contient pas BUY ni SELL â€” Energy n'est pas un signal."""
   L534:     tns = _make_tns()
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 533
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L531: 
   L532: def test_film_steps_energy_label_not_buy_sell():
>> L533:     """film_steps ne contient pas BUY ni SELL â€” Energy n'est pas un signal."""
   L534:     tns = _make_tns()
   L535:     energy = _make_energy()
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 539
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L537:     for step in out["film_steps"]:
   L538:         _assert("BUY" not in step, f"film_step ne doit pas contenir BUY: {step}")
>> L539:         _assert("SELL" not in step, f"film_step ne doit pas contenir SELL: {step}")
   L540:     print("[OK] test_film_steps_energy_label_not_buy_sell")
   L541: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 540
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L538:         _assert("BUY" not in step, f"film_step ne doit pas contenir BUY: {step}")
   L539:         _assert("SELL" not in step, f"film_step ne doit pas contenir SELL: {step}")
>> L540:     print("[OK] test_film_steps_energy_label_not_buy_sell")
   L541: 
   L542: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 556
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L554: 
   L555: 
>> L556: def test_no_buy_sell_in_any_output():
   L557:     """Aucune alerte ne contient BUY ou SELL."""
   L558:     tns = _make_tns(
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 557
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L555: 
   L556: def test_no_buy_sell_in_any_output():
>> L557:     """Aucune alerte ne contient BUY ou SELL."""
   L558:     tns = _make_tns(
   L559:         highest_level="HOT_NODE",
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 570
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L568:             v = a.get(field, "")
   L569:             _assert("BUY" not in v, f"Alerte {a['name']} contient BUY dans {field}")
>> L570:             _assert("SELL" not in v, f"Alerte {a['name']} contient SELL dans {field}")
   L571:     print("[OK] test_no_buy_sell_in_any_output")
   L572: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 571
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L569:             _assert("BUY" not in v, f"Alerte {a['name']} contient BUY dans {field}")
   L570:             _assert("SELL" not in v, f"Alerte {a['name']} contient SELL dans {field}")
>> L571:     print("[OK] test_no_buy_sell_in_any_output")
   L572: 
   L573: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1097
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1095: 
   L1096: 
>> L1097: def test_energy_context_no_buy_sell():
   L1098:     """Aucune alerte ne contient BUY ni SELL avec energy_context."""
   L1099:     tns = _make_tns_with_energy_context()
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1098
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1096: 
   L1097: def test_energy_context_no_buy_sell():
>> L1098:     """Aucune alerte ne contient BUY ni SELL avec energy_context."""
   L1099:     tns = _make_tns_with_energy_context()
   L1100:     out = map_behavioral_alerts(tns, None)
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1105
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1103:             v = a.get(f_key, "")
   L1104:             _assert("BUY" not in v, f"{a['name']}.{f_key} contient BUY")
>> L1105:             _assert("SELL" not in v, f"{a['name']}.{f_key} contient SELL")
   L1106:     print("[OK] test_energy_context_no_buy_sell")
   L1107: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1106
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1104:             _assert("BUY" not in v, f"{a['name']}.{f_key} contient BUY")
   L1105:             _assert("SELL" not in v, f"{a['name']}.{f_key} contient SELL")
>> L1106:     print("[OK] test_energy_context_no_buy_sell")
   L1107: 
   L1108: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1151
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1149:     test_same_angle_not_triggered_on_no_cluster,
   L1150:     test_film_steps_present,
>> L1151:     test_film_steps_energy_label_not_buy_sell,
   L1152:     test_next_watch_enriched,
   L1153:     test_no_buy_sell_in_any_output,
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1153
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1151:     test_film_steps_energy_label_not_buy_sell,
   L1152:     test_next_watch_enriched,
>> L1153:     test_no_buy_sell_in_any_output,
   L1154:     test_degraded_alerts_in_dedicated_key,
   L1155:     test_counter_release_not_confirmed,
~~~

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1183
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L1181:     # V0.8.2.1 â€” garde-fous
   L1182:     test_energy_context_never_produces_hot,
>> L1183:     test_energy_context_no_buy_sell,
   L1184:     test_counter_release_never_becomes_confirmed,
   L1185: ]
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 12
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L10: - MIXED_TOPLINE â†’ INFO
   L11: - dominant_leader=MIXED â†’ INFO
>> L12: - no BUY/SELL
   L13: - 50 tests existants toujours stables (via import)
   L14: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 275
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L273: 
   L274: 
>> L275: def test_no_buy_sell_in_any_rg_alert() -> None:
   L276:     section("Pas de BUY/SELL dans les alertes RG")
   L277:     for ts in [
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 276
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L274: 
   L275: def test_no_buy_sell_in_any_rg_alert() -> None:
>> L276:     section("Pas de BUY/SELL dans les alertes RG")
   L277:     for ts in [
   L278:         "RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT",
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 287
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L285:             full = str(a).upper()
   L286:             check(f"{a['name']} â€” pas de BUY",  "BUY"  not in full)
>> L287:             check(f"{a['name']} â€” pas de SELL", "SELL" not in full)
   L288: 
   L289: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 317
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L315: 
   L316: def test_dominant_direction_not_used_as_signal() -> None:
>> L317:     section("dominant_direction non transformÃ© en signal BUY/SELL")
   L318:     for direction in ["UP", "DOWN", "MIXED", "UNKNOWN"]:
   L319:         rg_block = _rg(
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 327
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L325:         for a in alerts:
   L326:             full = str(a).upper()
>> L327:             check(f"dir={direction} â€” pas de BUY/SELL",
   L328:                   "BUY" not in full and "SELL" not in full)
   L329: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 328
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L326:             full = str(a).upper()
   L327:             check(f"dir={direction} â€” pas de BUY/SELL",
>> L328:                   "BUY" not in full and "SELL" not in full)
   L329: 
   L330: 
~~~

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 350
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L348:     test_mixed_topline_unreliable_also_produces_info()
   L349:     test_topline_reliable_no_rg_alerts()
>> L350:     test_no_buy_sell_in_any_rg_alert()
   L351:     test_existing_50_still_pass()
   L352:     test_dominant_leader_mixed_triggers_leader_conflict()
~~~

---

### Core\verify_b6_order_flow_proxy_once.py

- Pattern: buy
- Line: 175
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L173: ## proxy_delta
   L174: Score signé représentant pression estimée de la bougie M1.
>> L175: Positif = buy proxy.
   L176: Négatif = sell proxy.
   L177: 
~~~

---

### Core\verify_b6_order_flow_proxy_once.py

- Pattern: sell
- Line: 176
- Class: CODE_OR_TEMPLATE_REVIEW

~~~text
   L174: Score signé représentant pression estimée de la bougie M1.
   L175: Positif = buy proxy.
>> L176: Négatif = sell proxy.
   L177: 
   L178: ## absorption_rate
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_OPTIMIZED_V2_COMPLETE_20260506.md

- Pattern: sell
- Line: 15
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L13: PowerFlow = Forex flux perception engine, NOT:
   L14:   âŒ nounou / risk nanny
>> L15:   âŒ BUY/SELL robot
   L16:   âŒ classic technical indicator
   L17:   âŒ delayed signal factory
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_OPTIMIZED_V2_COMPLETE_20260506.md

- Pattern: sell
- Line: 543
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L541: ðŸš« Never commit without tests passing
   L542: ðŸš« Never create circular dependencies
>> L543: ðŸš« Never transform Node alert into BUY/SELL
   L544: ðŸš« Never use Energy as standalone signal
   L545: ðŸš« Never confuse TemporalDensity with Temporal Nodes
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_OPTIMIZED_V2_COMPLETE_20260506.md

- Pattern: sell
- Line: 590
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L588: ```
   L589: PowerFlow V6 is perception + measurement + naming + alerting.
>> L590: Not decision. Not BUY/SELL. Not risk management.
   L591: 
   L592: Node V0.8.2 validates complete behavioral reading:
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V3_HTF_ORCHESTRAL_20260507.md

- Pattern: sell
- Line: 15
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L13: PowerFlow = Forex flux perception engine, NOT:
   L14:   âŒ nounou / risk nanny
>> L15:   âŒ BUY/SELL robot
   L16:   âŒ classic technical indicator
   L17:   âŒ delayed signal factory
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V3_HTF_ORCHESTRAL_20260507.md

- Pattern: sell
- Line: 895
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L893: ðŸš« Never commit without tests passing
   L894: ðŸš« Never create circular dependencies
>> L895: ðŸš« Never transform Node alert into BUY/SELL
   L896: ðŸš« Never use Energy as standalone signal
   L897: ðŸš« Never reduce PowerFlow to M1-only microfilm
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V3_HTF_ORCHESTRAL_20260507.md

- Pattern: sell
- Line: 982
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L980: ```
   L981: PowerFlow V6 is perception + measurement + naming + alerting.
>> L982: Not decision. Not BUY/SELL. Not risk management.
   L983: 
   L984: HTF (W/D/H4/H1) gives context, gravity, delayed window.
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V4_LOOP_COCKPIT_20260507.md

- Pattern: sell
- Line: 15
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L13: PowerFlow = Forex flux perception engine, NOT:
   L14:   âŒ nounou / risk nanny
>> L15:   âŒ BUY/SELL robot
   L16:   âŒ classic technical indicator
   L17:   âŒ delayed signal factory
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V4_LOOP_COCKPIT_20260507.md

- Pattern: sell
- Line: 1003
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L1001: ðŸš« Never commit without tests passing
   L1002: ðŸš« Never create circular dependencies
>> L1003: ðŸš« Never transform Node alert into BUY/SELL
   L1004: ðŸš« Never use Energy as standalone signal
   L1005: ðŸš« Never reduce PowerFlow to M1-only microfilm
~~~

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V4_LOOP_COCKPIT_20260507.md

- Pattern: sell
- Line: 1092
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L1090: ```
   L1091: PowerFlow V6 is perception + measurement + naming + alerting.
>> L1092: Not decision. Not BUY/SELL. Not risk management.
   L1093: 
   L1094: HTF (W/D/H4/H1) gives context, gravity, delayed window.
~~~

---

### Docs\2026\2026-05\00_RESUME_2MIN_V7_2.md

- Pattern: sell
- Line: 68
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L66: âœ… 0 dÃ©pendance circulaire
   L67: âœ… 0 Ã©criture DB directe
>> L68: âœ… 0 BUY/SELL dans le moteur
   L69: âœ… 0 import cockpit_* depuis pf_*
   L70: âœ… py_compile OK sur tout
~~~

---

### Docs\2026\2026-05\B7_FRACTAL_RESONANCE_VALIDATION.md

- Pattern: certain
- Line: 19
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L17: ```text
   L18: M1, M5, M15, M30, H1 vibrent-ils sur le mÃªme Ã©vÃ©nement,
>> L19: ou est-ce que certains timeframes sont en retard ?
   L20: ```
   L21: 
~~~

---

### Docs\2026\2026-05\CLAUDE_md_V7_2_UPDATED_20260510.md

- Pattern: sell
- Line: 274
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L272: âœ… Aucune Ã©criture DB directe depuis pf_* ou run_*
   L273: âœ… DB read-only systÃ©matique : sqlite3.connect("file:...?mode=ro", uri=True)
>> L274: âœ… Aucun BUY/SELL dans le moteur
   L275: âœ… Aucune dÃ©pendance circulaire
   L276: âœ… py_compile OK sur tous les fichiers crÃ©Ã©s
~~~

---

### Docs\2026\2026-05\CLAUDE_md_V7_2_UPDATED_20260510.md

- Pattern: sell
- Line: 378
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L376: âŒ Ne pas importer cockpit_* dans pf_*
   L377: âŒ Pas de dÃ©pendances circulaires
>> L378: âŒ Pas de BUY/SELL dans les alertes
   L379: âŒ cockpit_orchestral V0.1.5+ = NO GO
   L380: âŒ Pas de censure d'alerte prÃ©coce
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_ALERT_OBSERVABILITY_V72_20260510.md

- Pattern: certain
- Line: 446
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L444: ## 26. MATURITY_PARTIAL
   L445: 
>> L446: Note technique indiquant que certaines alertes nâ€™exposent pas leur maturitÃ©.
   L447: 
   L448: La maturitÃ© attendue est :
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: certain
- Line: 38
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L36: follower
   L37: direction de trade
>> L38: flux institutionnel certain
   L39: ```
   L40: 
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: certain
- Line: 391
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L389: ```text
   L390: trade valid
>> L391: signal certain
   L392: institution confirmed
   L393: direction guaranteed
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: guaranteed
- Line: 393
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L391: signal certain
   L392: institution confirmed
>> L393: direction guaranteed
   L394: ```
   L395: 
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: signal certain
- Line: 391
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L389: ```text
   L390: trade valid
>> L391: signal certain
   L392: institution confirmed
   L393: direction guaranteed
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_LAB_ENGINE_V72_20260510.md

- Pattern: certain
- Line: 399
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L397: ```text
   L398: B4 compressing
>> L399: B1 range ou incertain
   L400: B5 neutral
   L401: EIE absent
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_MEMORY_ENGINE_V1.md

- Pattern: garanti
- Line: 83
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L81: 
   L82: ### DETERMINISTIC_PATTERN_HASH
>> L83: PropriÃ©tÃ© technique garantissant que deux alertes ayant les mÃªmes 6 dimensions produisent toujours le mÃªme `pattern_hash`.
   L84: Indispensable pour que la mÃ©moire soit fiable entre deux runs, deux sessions ou deux jours.
   L85: 
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_MULTI_SYMBOL_EXTENSION.md

- Pattern: certain
- Line: 116
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L114: 
   L115: ### PARTIAL_SYMBOL_DENSITY
>> L116: Ã‰tat technique oÃ¹ un symbol possÃ¨de des donnÃ©es sur certains timeframes mais pas sur toute la stack attendue. Exemple : `EURUSD` disponible en M1/M5 mais absent en M15/M30.
   L117: 
   L118: Ce n'est pas une dÃ©cision de marchÃ©. C'est une information de qualitÃ© de perception.
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_MULTI_SYMBOL_EXTENSION.md

- Pattern: certain
- Line: 127
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L125: 
   L126: ### RUNNER_ARGUMENT_DRIFT
>> L127: Risque technique oÃ¹ certains anciens runners n'acceptent pas encore `--symbol`, `--output`, ou une autre option standard. L'orchestrateur doit exposer ce drift par step au lieu de masquer l'Ã©chec.
   L128: 
   L129: ### SCHEMA_AWARE_SYMBOL_MAPPING
~~~

---

### Docs\2026\2026-05\PATCH_LEXIQUE_V7_1_ORCHESTRATEUR.md

- Pattern: certain
- Line: 121
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L119: ```text
   L120: COMPLETE  : tous les steps sont OK
>> L121: PARTIAL   : certains steps OK, certains FAIL
   L122: FAILED    : aucun step OK
   L123: ```
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 31
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L29: ```text
   L30: pf_temporal_node_state.py       â†’ faux positif majoritaire, fichier sain, read-only confirmÃ©
>> L31: pf_behavioral_alert_mapper.py   â†’ faux positif protecteur, fichier sain, doctrine anti BUY/SELL explicite
   L32: pf_flow_nodes.py                â†’ vrai point dâ€™attention architecture : ancien module legacy qui Ã©crit en DB
   L33: ```
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 195
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L193: 
   L194: ```python
>> L195: - Energy ne produit jamais BUY/SELL ni HOT seule
   L196: ```
   L197: 
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 201
- Class: COMMENT_OR_DOC_REVIEW

~~~text
   L199: 
   L200: ```python
>> L201: # Jamais de BUY/SELL. Jamais de DB. Jamais de Telegram direct.
   L202: ```
   L203: 
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 207
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L205: 
   L206: ```python
>> L207: "buy_sell_output": False
   L208: ```
   L209: 
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 212
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L210: ## Lecture
   L211: 
>> L212: Le scanner a dÃ©tectÃ© `BUY/SELL`, mais les occurrences sont des garde-fous doctrinaux.
   L213: 
   L214: Ce nâ€™est pas une dÃ©rive.
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 219
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L217: 
   L218: ```text
>> L219: pas de BUY/SELL
   L220: pas de DB
   L221: pas de Telegram
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 275
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L273: 
   L274: ```python
>> L275: - Pas de BUY/SELL.
   L276: - Pas de Telegram direct.
   L277: - Sortie cockpit/backtest : score, intÃ©rÃªt, devises, message court.
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 323
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L321: ## Institutional red flag
   L322: 
>> L323: Le scanner a aussi remontÃ© `BUY/SELL`, mais dans les lignes exactes on voit :
   L324: 
   L325: ```text
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 326
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L324: 
   L325: ```text
>> L326: Pas de BUY/SELL
   L327: ```
   L328: 
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 371
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L369: |---|---|---|---|
   L370: | `pf_temporal_node_state.py` | classical zone + architecture | faux positif : support = relay, DB read-only confirmÃ© | sain, ne pas modifier |
>> L371: | `pf_behavioral_alert_mapper.py` | institutional | faux positif : anti BUY/SELL explicite | sain, ne pas modifier |
   L372: | `pf_flow_nodes.py` | architecture + institutional | vrai risque DB write, mais BUY/SELL est garde-fou | classer legacy / isoler |
   L373: 
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 372
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L370: | `pf_temporal_node_state.py` | classical zone + architecture | faux positif : support = relay, DB read-only confirmÃ© | sain, ne pas modifier |
   L371: | `pf_behavioral_alert_mapper.py` | institutional | faux positif : anti BUY/SELL explicite | sain, ne pas modifier |
>> L372: | `pf_flow_nodes.py` | architecture + institutional | vrai risque DB write, mais BUY/SELL est garde-fou | classer legacy / isoler |
   L373: 
   L374: ---
~~~

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 492
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L490: Le principal risque est pf_flow_nodes.py, module legacy write.
   L491: La sÃ©mantique support dans pf_temporal_node_state.py est un faux positif.
>> L492: Le langage BUY/SELL dans pf_behavioral_alert_mapper.py est un garde-fou, pas une sortie.
   L493: ```
   L494: 
~~~

---

### Docs\2026\2026-05\RAPPORT_COMPLET_B7_FRACTAL_RESONANCE_POST_COMMIT.md

- Pattern: certain
- Line: 316
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L314: ```text
   L315: Les Ã©tages ne tremblent pas ensemble.
>> L316: Certains Ã©tages rÃ©pondent mÃªme Ã  contre-phase.
   L317: ```
   L318: 
~~~

---

### Docs\2026\2026-05\RAPPORT_COMPLET_POWERFLOW_V721_B1HMM_MTF_B4WAVELET_SCHEMAFLEX_20260511.md

- Pattern: certain
- Line: 23
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L21: 1. `hmmlearn` ne s'installait pas sous Python 3.14 sans toolchain C++.
   L22: 2. Le moteur attendait initialement un schÃ©ma DB trop strict.
>> L23: 3. Le script one-click marquait certaines Ã©tapes en `PASS` malgrÃ© des erreurs runtime.
   L24: 
   L25: Le hotfix final `71c2f91` corrige ces points.
~~~

---

### Docs\2026\2026-05\RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_20260510.md

- Pattern: certain
- Line: 75
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L73: | Git helper | stabilisÃ© via `471b1c7` |
   L74: 
>> L75: Conclusion : **l'Ã©tat rÃ©el Git est plus avancÃ© que certains documents d'administration**.
   L76: 
   L77: ---
~~~

---

### Docs\2026\2026-05\RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_20260510.md

- Pattern: certain
- Line: 196
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L194: #### Risque 2 â€” runners manquants
   L195: 
>> L196: Certains runners listÃ©s peuvent ne pas exister selon l'Ã©tat rÃ©el du repo :
   L197: 
   L198: ```text
~~~

---

### Docs\2026\2026-05\RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_20260510.md

- Pattern: certain
- Line: 233
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L231: ```
   L232: 
>> L233: ou forcer explicitement certains rapports finaux.
   L234: 
   L235: #### Risque 5 â€” confusion PASS / WARNING / FAIL
~~~

---

### Docs\2026\2026-05\RAPPORT_LAB_ENGINE_V72_20260510.md

- Pattern: certain
- Line: 474
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L472: - Le HMM B1+ nâ€™est pas rejouÃ© frame par frame.
   L473: - B4 Wavelet complet nâ€™est pas encore recalculÃ© sur chaque fenÃªtre.
>> L474: - EIE complet est approximÃ© dans certains runs.
   L475: - Les footprints restent INFERENCE_ONLY.
   L476: - Pas de volume / orderbook.
~~~

---

### Docs\2026\2026-05\RAPPORT_MISSION_MULTI_SYMBOL_EXTENSION.md

- Pattern: certain
- Line: 354
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L352: 
   L353: RUNNER_ARGUMENT_DRIFT
>> L354:   Certains anciens runners peuvent ne pas accepter --symbol ou --output.
   L355:   L'orchestrateur les marque FAIL ou SKIPPED explicitement.
   L356: 
~~~

---

### Docs\CLAUDE.md

- Pattern: guaranteed
- Line: 361
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L359: ### Mandatory doctrine
   L360: 
>> L361: - PowerFlow reads market structure; it does not issue guaranteed trading signals.
   L362: - PowerFlow qualifies perception; the trader decides.
   L363: - PowerFlow must separate observation, qualification, hypothesis, confirmation, invalidation, data limits, and trader decision.
~~~

---

### Docs\Contracts\T004_CAPTURE_DB_PATH_AUDIT.json

- Pattern: sell
- Line: 6370
- Class: LIKELY_DATA_OR_CONFIG_REVIEW

~~~text
   L6368:           "line": 11,
   L6369:           "pattern": "database",
>> L6370:           "text": "It never emits BUY/SELL instructions and never writes to the database."
   L6371:         },
   L6372:         {
~~~

---

### Docs\Contracts\T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json

- Pattern: certain
- Line: 11724
- Class: LIKELY_DATA_OR_CONFIG_REVIEW

~~~text
   L11722:             "symbol"
   L11723:           ],
>> L11724:           "text": "Certaines preuves temporelles manquent pour le symbole."
   L11725:         },
   L11726:         {
~~~

---

### Docs\DISPATCH_STATUS.json

- Pattern: sell
- Line: 169
- Class: LIKELY_DATA_OR_CONFIG_REVIEW

~~~text
   L167:           "Legacy implementation preserved as _detect_tf_alignment_impl",
   L168:           "Wrapper absorbs extra args/kwargs from /api/cockpit-state call drift",
>> L169:           "No DB write, no dashboard contract change, no BUY/SELL semantics"
   L170:         ]
   L171:       },
~~~

---

### Docs\PATCH_LEXIQUE_ALERT_OBSERVABILITY_V72_20260510.md

- Pattern: certain
- Line: 446
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L444: ## 26. MATURITY_PARTIAL
   L445: 
>> L446: Note technique indiquant que certaines alertes nâ€™exposent pas leur maturitÃ©.
   L447: 
   L448: La maturitÃ© attendue est :
~~~

---

### Docs\POWERFLOW_BRICK_AUDIT_TERRAIN_V76_FINAL.md

- Pattern: certain
- Line: 22
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L20: ## 1. Diagnostic gÃ©nÃ©ral
   L21: 
>> L22: PowerFlow V7.5 possÃ¨de assez de briques pour percevoir des fragments : empilement, dÃ©tachement, compression, Ã©nergie, gravitÃ© relationnelle, mÃ©moire, propagation, texture, guards, evidence et packet. Le problÃ¨me V7.6 n'est pas l'absence de capteurs. Le problÃ¨me est la surinterprÃ©tation de certains capteurs en rÃ´le de film.
   L23: 
   L24: ### Briques utiles
~~~

---

### Docs\POWERFLOW_BRICK_TO_PACKET_FIELD_MAPPING_V76.md

- Pattern: certain
- Line: 23
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L21: | B5 relational gravity | `relational_context`, `leader_follower_state` | Driver final, outcome | B8, coverage, price, B7 | Fausse certitude relationnelle |
   L22: | B8 cross-symbol validation | `cross_validation_state`, `driver_context` | Vraie force GBP/USD si coverage faible | coverage map, symbol freshness, B5 | `B8_DEGRADED` |
>> L23: | B6 film memory | `memory_match`, `known_false_positive`, `next_expected_behavior`, `invalidation_reference` | Prediction, outcome certain | current film, price arbiter, guards | Ã‰vÃ©nement isolÃ© confondu avec film |
   L24: | B7 propagation | `propagation_state`, `relay_quality` | Trade, release alone, qualified_bias alone | B3, price, zone, B7+, data | `LTF_ONLY` pris pour structure |
   L25: | B7+ detachment texture | `detachment_texture`, support `current_move_role` | Direction finale | price, last_structural_event, B7, B6 | Texture floue / UNKNOWN masquÃ© |
~~~

---

### Docs\POWERFLOW_ORCHESTRATION_UPDATE_PACK_20260507\00_CURRENT_STATE_POWERFLOW_V6_ORCHESTRATION_20260507.md

- Pattern: sell
- Line: 14
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L12: 
   L13: Il nâ€™est pas :
>> L14: - un bot BUY/SELL ;
   L15: - une nounou ;
   L16: - une tour de contrÃ´le ;
~~~

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: 100%
- Line: 620
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L618: 
   L619: - ZÃ©ro message principal ne doit Ãªtre constituÃ© seulement de `PAIR_UP` ou `PAIR_DOWN`.
>> L620: - 100% des packets terrain ont `data_visibility`.
   L621: - 100% des packets terrain ont `price_confirmation`.
   L622: - `UNKNOWN`, `HONEST_UNKNOWN` et `READING_PARTIAL` sont disponibles et autorisÃ©s.
~~~

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: 100%
- Line: 621
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L619: - ZÃ©ro message principal ne doit Ãªtre constituÃ© seulement de `PAIR_UP` ou `PAIR_DOWN`.
   L620: - 100% des packets terrain ont `data_visibility`.
>> L621: - 100% des packets terrain ont `price_confirmation`.
   L622: - `UNKNOWN`, `HONEST_UNKNOWN` et `READING_PARTIAL` sont disponibles et autorisÃ©s.
   L623: - Compatible `terrain_packet_v76_0`.
~~~

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: sell
- Line: 602
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L600: | `film_state` | comprendre le contexte | premiÃ¨re ligne | ordre directionnel |
   L601: | `last_structural_event` | garder la mÃ©moire du film | premiÃ¨re ou seconde ligne | prÃ©diction mÃ©canique |
>> L602: | `last_structural_direction` | comprendre l'inertie structurelle | compact avec last event | buy/sell |
   L603: | `current_zone` | situer le prix | cockpit dÃ©tail | niveau d'entrÃ©e |
   L604: | `current_zone_status` | savoir si zone accepte/rejette | ligne courte | dÃ©cision automatique |
~~~

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: sell
- Line: 626
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L624: - `raw_bias` existe mais ne domine jamais la phrase cockpit.
   L625: - Les packets dÃ©gradÃ©s affichent la dÃ©gradation en haut.
>> L626: - La grammaire ne crÃ©e pas de buy/sell/entry/exit/target/stop.
   L627: - La grammaire ne crÃ©e pas de nouveau score abstrait.
   L628: - La grammaire est intÃ©grable sans refonte dashboard ni Telegram.
~~~

---

### Docs\POWERFLOW_TERRAIN_LEXICON_UPDATES_V76.md

- Pattern: sell
- Line: 11
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L9: | `current_move_role` | field | RÃ´le du mouvement actuel dans le film | `POST_LOW_REACTION` | direction brute | Champ central |
   L10: | `raw_bias` | field | Bias brut moteur conservÃ© pour traÃ§abilitÃ© | `PAIR_UP` | dÃ©cision | AffichÃ© aprÃ¨s requalification |
>> L11: | `qualified_bias` | field | Bias brut reclassÃ© par film, zone et prix | `POST_LOW_COUNTER_BREATH` | signal buy/sell | Message interprÃ©table |
   L12: | `packet_quality` | field | QualitÃ© comportementale du packet | `REACTION_NOT_RELEASE` | score de trade | Badge qualitÃ© |
   L13: | `price_confirmation` | field | Statut de confirmation/invalidation par le prix | `PRICE_PENDING` | entrÃ©e/sortie | Badge prix obligatoire |
~~~

---

### Docs\POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

- Pattern: 100%
- Line: 127
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L125: - `PRICE_UNKNOWN`
   L126: 
>> L127: **RÃ¨gle** : 100% des packets doivent avoir ce champ.
   L128: 
   L129: ### 2.7 Propagation
~~~

---

### Docs\POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

- Pattern: buy
- Line: 267
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L265: Un packet trader V7.6 ne doit jamais dÃ©clencher directement :
   L266: 
>> L267: - buy ;
   L268: - sell ;
   L269: - entry ;
~~~

---

### Docs\POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

- Pattern: sell
- Line: 268
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L266: 
   L267: - buy ;
>> L268: - sell ;
   L269: - entry ;
   L270: - exit ;
~~~

---

### Docs\POWERFLOW_V76_B6_MEMORY_GBPUSD_REPORT.md

- Pattern: garanti
- Line: 57
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L55: ```
   L56: 
>> L57: Sortie garantie:
   L58: 
   L59: ```json
~~~

---

### Docs\POWERFLOW_V76_TELEGRAM_FR_CLEANUP_REPORT.md

- Pattern: certain
- Line: 7
- Class: NEEDS_MANUAL_REVIEW

~~~text
   L5: Nettoyer lâ€™affichage Telegram FR sans modifier les enums internes PowerFlow.
   L6: 
>> L7: ProblÃ¨me traitÃ© : certains champs restaient visibles sous forme dâ€™enums anglais dans Telegram :
   L8: 
   L9: ```text
~~~

## Operational conclusion

- T006-F1B produced a corrected contextual triage report.
- No source wording was modified.
- Next step: T006-F2 should patch only confirmed trader-facing violations.