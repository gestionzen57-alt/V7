# T006-F2A - Confirmed patch candidate selection

Date: 2026-05-15 23:26:05 +02:00
Mission: select confirmed patch candidates from corrected T006-F1B wording triage
Status: T006_F2A_SELECTION_COMPLETE

## Source report

- Docs\Checkpoints\T006_F1B_WORDING_HIT_TRIAGE_CORRECTED_20260515_232046.md

## Rule

- T006-F2A does not patch source files.
- T006-F2A selects candidates only.
- T006-F2B may patch only confirmed active trader-facing wording.
- Negative/protective doctrine wording is excluded.
- Historical, checkpoint, staging, report, and canonical lexique files are excluded.

## Metrics

- Parsed F1B context rows: 160
- Confirmed patch candidates: 18
- Excluded / review-only rows: 142

## Candidate files

- Core\patch_dashboard_v75f_session_full_width.py: 5
- Core\pf_b6_live_fusion_once.py: 4
- Core\pf_behavioral_alert_mapper.py: 3
- Core\verify_b6_order_flow_proxy_once.py: 2
- Core\AVANT\pf_behavioral_alert_mapper.py: 2
- Core\pf_engine_scenes.py: 1
- Core\pf_memory.py: 1

## Excluded summary

- EXCLUDED: 113
- REVIEW_ONLY: 29

## Confirmed patch candidates

---

### Core\AVANT\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L12: - Ne pas modifier capture_bridge.py ni pf_temporal_node_state.py
   L13: - NODE_HEAT Ã¢â€°Â  CURRENCY_ENERGY
>> L14: - Energy ne produit jamais BUY/SELL ni HOT seule
   L15: - COUNTER_RELEASE_ATTEMPT Ã¢â€°Â  RELEASE_CONFIRMED
   L16: - Pas de first_detachment = pas de release confirmÃƒÂ©e
~~~

---

### Core\AVANT\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 128
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L126:     - is_present = False Ã¢â€ â€™ tous les checkers energy sont silencieux
   L127:     - node_energy_relation est observationnel Ã¢â‚¬â€ jamais un signal
>> L128:     - Energy ne produit jamais HOT ni BUY/SELL
   L129:     """
   L130:     source: str = "NONE"  # "energy_context" | "energy_release_alignment" | "standalone" | "NONE"
~~~

---

### Core\patch_dashboard_v75f_session_full_width.py

- Pattern: 100%
- Line: 11
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

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
- Reason: Active Core Python wording/template requires manual patch review.

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
- Reason: Active Core Python wording/template requires manual patch review.

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
- Reason: Active Core Python wording/template requires manual patch review.

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
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L59:   session.classList.add("wide");
   L60:   session.style.gridColumn = "1 / -1";
>> L61:   session.style.width = "100%";
   L62: 
   L63:   for (const table of session.querySelectorAll("table")) {
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: buy
- Line: 137
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L135: 
   L136:     if b6["action"] == "WAKE_TRADER":
>> L137:         if "SHORT" in daily_intent and b6["direction"] == "BUY_SIDE":
   L138:             final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
   L139:             final_message = "B6 charge BUY alors que le daily lit un piÃ¨ge/distribution baissier possible. Surveiller rÃ©intÃ©gration ou piÃ¨ge inverse."
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: buy
- Line: 139
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L137:         if "SHORT" in daily_intent and b6["direction"] == "BUY_SIDE":
   L138:             final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
>> L139:             final_message = "B6 charge BUY alors que le daily lit un piÃ¨ge/distribution baissier possible. Surveiller rÃ©intÃ©gration ou piÃ¨ge inverse."
   L140:         elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
   L141:             final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: sell
- Line: 140
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L138:             final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
   L139:             final_message = "B6 charge BUY alors que le daily lit un piÃ¨ge/distribution baissier possible. Surveiller rÃ©intÃ©gration ou piÃ¨ge inverse."
>> L140:         elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
   L141:             final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
   L142:             final_message = "B6 charge SELL dans le sens du daily trap/downside acceptance. Attention prÃ©coce renforcÃ©e."
~~~

---

### Core\pf_b6_live_fusion_once.py

- Pattern: sell
- Line: 142
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L140:         elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
   L141:             final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
>> L142:             final_message = "B6 charge SELL dans le sens du daily trap/downside acceptance. Attention prÃ©coce renforcÃ©e."
   L143:         else:
   L144:             final_synthesis = "B6_EARLY_TENSION_PRESENT"
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L12: - Ne pas modifier capture_bridge.py ni pf_temporal_node_state.py
   L13: - NODE_HEAT Ã¢â€°Â  CURRENCY_ENERGY
>> L14: - Energy ne produit jamais BUY/SELL ni HOT seule
   L15: - COUNTER_RELEASE_ATTEMPT Ã¢â€°Â  RELEASE_CONFIRMED
   L16: - Pas de first_detachment = pas de release confirmÃƒÂ©e
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 144
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L142:     - is_present = False Ã¢â€ â€™ tous les checkers energy sont silencieux
   L143:     - node_energy_relation est observationnel Ã¢â‚¬â€ jamais un signal
>> L144:     - Energy ne produit jamais HOT ni BUY/SELL
   L145:     """
   L146:     source: str = "NONE"  # "energy_context" | "energy_release_alignment" | "standalone" | "NONE"
~~~

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1356
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L1354:         "db_write": False,
   L1355:         "telegram_send": False,
>> L1356:         "buy_sell_output": False,
   L1357:         "p1_2_guard_aware": True,
   L1358:         "p_next_4_eie_queue_reader": True,
~~~

---

### Core\pf_engine_scenes.py

- Pattern: entree automatique
- Line: 433
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L431:     if scene_type == "TREND_CONTINUATION":
   L432:         return "Flux propre; chercher continuation apres respiration."
>> L433:     return "Surveiller, pas d'entree automatique."
   L434: 
   L435:
~~~

---

### Core\pf_memory.py

- Pattern: certain
- Line: 545
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L543: 
   L544:     if confirmed >= 3:
>> L545:         lessons.append("Les postures Cockpit semblent protÃƒÂ©ger correctement certaines dÃƒÂ©cisions confirmÃƒÂ©es.")
   L546:     if invalidated >= 2:
   L547:         lessons.append("Plusieurs lectures ont ÃƒÂ©tÃƒÂ© invalidÃƒÂ©es : renforcer les confirmations avant de passer de WATCH ÃƒÂ  ARMED.")
~~~

---

### Core\verify_b6_order_flow_proxy_once.py

- Pattern: buy
- Line: 175
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L173: ## proxy_delta
   L174: Score signÃ© reprÃ©sentant pression estimÃ©e de la bougie M1.
>> L175: Positif = buy proxy.
   L176: NÃ©gatif = sell proxy.
   L177:
~~~

---

### Core\verify_b6_order_flow_proxy_once.py

- Pattern: sell
- Line: 176
- Class: CODE_OR_TEMPLATE_REVIEW
- Reason: Active Core Python wording/template requires manual patch review.

~~~text
L174: Score signÃ© reprÃ©sentant pression estimÃ©e de la bougie M1.
   L175: Positif = buy proxy.
>> L176: NÃ©gatif = sell proxy.
   L177: 
   L178: ## absorption_rate
~~~


## Excluded / review-only rows

---

### Core\AVANT\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 838
- Class: COMMENT_OR_DOC_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Core\backups\dashboard_cleanup\20260511_082526\DASHBOARD_V72_MAX_HARDENING_REPORT.md

- Pattern: certain
- Line: 12
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\backups\dashboard_cleanup\20260511_082526\DASHBOARD_V72_SURFACE_V4_REPORT.md

- Pattern: certain
- Line: 5
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\dashboard_cleanup\20260511_082526\P0_DASHBOARD_GO_NO_GO_CHECKLIST.md

- Pattern: sell
- Line: 100
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\docs\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 19
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\docs\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 92
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\runtime\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 19
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_final_delivery_20260511_121023\_dashboard_final_delivery\runtime\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 92
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_pass_strict_cleanup_20260511_130018\_squad2_docs_final\docs\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: 100%
- Line: 252
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_pass_strict_cleanup_20260511_130018\_squad2_docs_final\docs\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: sell
- Line: 186
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_pass_strict_cleanup_20260511_130018\_squad2_docs_final\docs\CLAUDE_md_V72_FINAL_UPDATE.md

- Pattern: 100%
- Line: 223
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_session_dashboard_commit_20260511_164455\_docs_pass_strict_update\docs\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: sell
- Line: 145
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_session_dashboard_commit_20260511_164455\RAPPORT_COMPLET_POWERFLOW_V721_B1HMM_MTF_B4WAVELET_SCHEMAFLEX_20260511.md

- Pattern: certain
- Line: 23
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_session_dashboard_commit_20260511_164455\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 9
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\backups\post_session_dashboard_commit_20260511_164455\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 475
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\CHECKPOINT_P0_LIVE_20260511.md

- Pattern: 100%
- Line: 119
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\CHECKPOINT_SESSION_FINAL_20260511.md

- Pattern: sell
- Line: 145
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\CURRENT_STATE_V7_POST_P0_UPDATE.md

- Pattern: sell
- Line: 235
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 19
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md

- Pattern: sell
- Line: 92
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\docs\2026\2026-05\RAPPORT_MULTISYMBOL_SCHEDULER_20260511.md

- Pattern: sell
- Line: 74
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\docs\RAPPORT_TRADER_ALERT_STATE_V01_COMPLETE.md

- Pattern: sell
- Line: 175
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\docs\RAPPORT_TRADER_ALERT_STATE_V01_COMPLETE.md

- Pattern: sell
- Line: 277
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\docs\RAPPORT_TRADER_ALERT_STATE_V01_COMPLETE.md

- Pattern: sell
- Line: 331
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\P0_FINAL_ARCHITECT_DECISION.md

- Pattern: 100%
- Line: 97
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\PATCH_LEXIQUE_POWERFLOW_V76_ALERT_GATE_20260513.md

- Pattern: certain
- Line: 270
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\pf_behavioral_alert_mapper.py

- Pattern: sell
- Line: 959
- Class: COMMENT_OR_DOC_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Core\pf_cross_symbol_validation.py

- Pattern: sell
- Line: 11
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\pf_lab_engine_v72.py

- Pattern: certain
- Line: 844
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\RAPPORT_SESSION_POWERFLOW_V76_ALERT_GATE_20260513.md

- Pattern: certain
- Line: 513
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\RAPPORT_SESSION_POWERFLOW_V76_ALERT_GATE_20260513.md

- Pattern: certain
- Line: 519
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\REGISTRE_BRIQUES_PATCH_SIGNAL_ADAPTIVE_PROFILE.md

- Pattern: sell
- Line: 9
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 9
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\REGISTRE_BRIQUES_PATCH_V721_B1HMM_MTF_SCHEMAFLEX.md

- Pattern: sell
- Line: 475
- Class: NEEDS_MANUAL_REVIEW
- Decision: REVIEW_ONLY
- Reason: Core markdown may be documentation; review before patch.

---

### Core\scheduler_powerflow_turbo_wrapper.py

- Pattern: sell
- Line: 12
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01.py

- Pattern: achete
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01.py

- Pattern: sell
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01_1.py

- Pattern: achete
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01_1.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01_1.py

- Pattern: sell
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01_2.py

- Pattern: achete
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01_2.py

- Pattern: sell
- Line: 14
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\telegram_trader_alert_v01_2.py

- Pattern: sell
- Line: 48
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 532
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 533
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 538
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 540
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 556
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 557
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 569
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 571
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1097
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1098
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1104
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1106
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1151
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1153
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: buy
- Line: 1183
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 532
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 533
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 539
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 540
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 556
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 557
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 570
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 571
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1097
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1098
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1105
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1106
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1151
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1153
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper.py

- Pattern: sell
- Line: 1183
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 12
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 275
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 276
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 287
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 317
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 327
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 328
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Core\TEST\test_behavioral_alert_mapper_rg_p2.py

- Pattern: sell
- Line: 350
- Class: CODE_OR_TEMPLATE_REVIEW
- Decision: EXCLUDED
- Reason: Test or validation file; patch only if runtime wording uses it directly.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_OPTIMIZED_V2_COMPLETE_20260506.md

- Pattern: sell
- Line: 15
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_OPTIMIZED_V2_COMPLETE_20260506.md

- Pattern: sell
- Line: 543
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_OPTIMIZED_V2_COMPLETE_20260506.md

- Pattern: sell
- Line: 590
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V3_HTF_ORCHESTRAL_20260507.md

- Pattern: sell
- Line: 15
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V3_HTF_ORCHESTRAL_20260507.md

- Pattern: sell
- Line: 895
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V3_HTF_ORCHESTRAL_20260507.md

- Pattern: sell
- Line: 982
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V4_LOOP_COCKPIT_20260507.md

- Pattern: sell
- Line: 15
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V4_LOOP_COCKPIT_20260507.md

- Pattern: sell
- Line: 1003
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Docs\2026\2026-05\_legacy_root_docs\CLAUDE_md_V4_LOOP_COCKPIT_20260507.md

- Pattern: sell
- Line: 1092
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\00_RESUME_2MIN_V7_2.md

- Pattern: sell
- Line: 68
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\B7_FRACTAL_RESONANCE_VALIDATION.md

- Pattern: certain
- Line: 19
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\CLAUDE_md_V7_2_UPDATED_20260510.md

- Pattern: sell
- Line: 274
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\CLAUDE_md_V7_2_UPDATED_20260510.md

- Pattern: sell
- Line: 378
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_ALERT_OBSERVABILITY_V72_20260510.md

- Pattern: certain
- Line: 446
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: certain
- Line: 38
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: certain
- Line: 391
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: guaranteed
- Line: 393
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72_20260510.md

- Pattern: signal certain
- Line: 391
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_LAB_ENGINE_V72_20260510.md

- Pattern: certain
- Line: 399
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_MEMORY_ENGINE_V1.md

- Pattern: garanti
- Line: 83
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_MULTI_SYMBOL_EXTENSION.md

- Pattern: certain
- Line: 116
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_MULTI_SYMBOL_EXTENSION.md

- Pattern: certain
- Line: 127
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\PATCH_LEXIQUE_V7_1_ORCHESTRATEUR.md

- Pattern: certain
- Line: 121
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 31
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 195
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 201
- Class: COMMENT_OR_DOC_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 207
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 212
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 219
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 275
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 323
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 326
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 371
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 372
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_AUDIT_CODE_REEL_GRAVITY_ZONES_V72_20260510.md

- Pattern: sell
- Line: 492
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_COMPLET_B7_FRACTAL_RESONANCE_POST_COMMIT.md

- Pattern: certain
- Line: 316
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_COMPLET_POWERFLOW_V721_B1HMM_MTF_B4WAVELET_SCHEMAFLEX_20260511.md

- Pattern: certain
- Line: 23
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_20260510.md

- Pattern: certain
- Line: 75
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_20260510.md

- Pattern: certain
- Line: 196
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_20260510.md

- Pattern: certain
- Line: 233
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_LAB_ENGINE_V72_20260510.md

- Pattern: certain
- Line: 474
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\2026\2026-05\RAPPORT_MISSION_MULTI_SYMBOL_EXTENSION.md

- Pattern: certain
- Line: 354
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\CLAUDE.md

- Pattern: guaranteed
- Line: 361
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: CLAUDE.md contains doctrine and negative constraints; not a runtime wording violation.

---

### Docs\Contracts\T004_CAPTURE_DB_PATH_AUDIT.json

- Pattern: sell
- Line: 6370
- Class: LIKELY_DATA_OR_CONFIG_REVIEW
- Decision: EXCLUDED
- Reason: Forbidden term appears in a negative/protective rule, not as an instruction.

---

### Docs\Contracts\T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json

- Pattern: certain
- Line: 11724
- Class: LIKELY_DATA_OR_CONFIG_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\DISPATCH_STATUS.json

- Pattern: sell
- Line: 169
- Class: LIKELY_DATA_OR_CONFIG_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\PATCH_LEXIQUE_ALERT_OBSERVABILITY_V72_20260510.md

- Pattern: certain
- Line: 446
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_BRICK_AUDIT_TERRAIN_V76_FINAL.md

- Pattern: certain
- Line: 22
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_BRICK_TO_PACKET_FIELD_MAPPING_V76.md

- Pattern: certain
- Line: 23
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_ORCHESTRATION_UPDATE_PACK_20260507\00_CURRENT_STATE_POWERFLOW_V6_ORCHESTRATION_20260507.md

- Pattern: sell
- Line: 14
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: 100%
- Line: 620
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: 100%
- Line: 621
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: sell
- Line: 602
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TERRAIN_GRAMMAR_V76_FINAL.md

- Pattern: sell
- Line: 626
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TERRAIN_LEXICON_UPDATES_V76.md

- Pattern: sell
- Line: 11
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

- Pattern: 100%
- Line: 127
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

- Pattern: buy
- Line: 267
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

- Pattern: sell
- Line: 268
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_V76_B6_MEMORY_GBPUSD_REPORT.md

- Pattern: garanti
- Line: 57
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

---

### Docs\POWERFLOW_V76_TELEGRAM_FR_CLEANUP_REPORT.md

- Pattern: certain
- Line: 7
- Class: NEEDS_MANUAL_REVIEW
- Decision: EXCLUDED
- Reason: Not confirmed as active trader-facing wording.

## Operational conclusion

- T006-F2A found confirmed patch candidates.
- Next step: T006-F2B targeted patch on candidate files only.
- No source wording was modified by T006-F2A.