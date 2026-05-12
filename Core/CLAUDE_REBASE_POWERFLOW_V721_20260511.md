# CLAUDE REBASE — PowerFlow V7.2.1 Centralisé

**Date :** 2026-05-11  
**Generated UTC :** 2026-05-12T08:57:01Z  
**Objectif :** remettre Claude à niveau après perte de fil  
**Source :** état Git visible + logs terminal utilisateur + état GPT courant  
**Statut centralisé :** V7.2.1 production live / P0 PASS_STRICT / MultiSymbol scheduler actif / SessionOverlay V2 actif

---

## 1. Message court à donner à Claude

```text
Claude, reprends ici.

PowerFlow V7.2.1 est en production live.

État validé :
- P0 Core PASS
- P0 Strict PASS_STRICT
- Dashboard PASS
- Hydration PASS 16/16
- Dashboard contract 0 fail / 0 warn
- SessionOverlay V2 actif
- MultiSymbol scheduler actif
- Dashboard multi-symbol UI actif
- USDJPY audit disponible

Derniers commits importants :
- 50428c3 : P0 strict promotion PASS_STRICT
- 3eeee70 : SessionOverlay V2 + Dashboard dual display hardening
- 6834c7d : MultiSymbol parametric extension + cross-validation + scheduler
- 3879db5 : Docs MultiSymbol scheduler validation report
- c97fb1c : Dashboard multiSymbol UI tabs + cross-validation card + USDJPY audit

Ne pas réparer P0.
Ne pas réparer Dashboard MAX.
Ne pas toucher capture_bridge.py.
Ne pas écrire powerflow.db.
La suite est extension / consolidation V7.2.1.
```

---

## 2. État officiel PowerFlow connu

```text
PowerFlow version        : V7.2.1
P0 Core                  : PASS
P0 Strict                : PASS_STRICT
Dashboard                : PASS
Hydration                : PASS — 16 runners / 0 failure
Contract dashboard       : PASS — 0 fail / 0 warn
SessionOverlay           : V2 actif
MultiSymbol scheduler    : actif
Dashboard multi-symbol   : actif
Git branch               : main
Remote                   : origin/main
```

PowerFlow reste un moteur de perception comportementale, pas un bot de trading.

---

## 3. Commits à connaître

### Base P0 / Dashboard

```text
8787dd6 — P0: core perception PASS, strict pending data window
aac44f0 — Dashboard: stabilize V7.2 MAX contract surface and full hydration stack
f9cb7ba — Docs: archive V7.2 P0 live dashboard stabilization checkpoint
93fc478 — Dashboard: finalize V7.2 stable delivery and validation docs
0dc2df6 — Dashboard: harden V7.2 wrapper exit checks and log doctor
372204a — Docs: archive V7.2 final official state and lexique
50428c3 — P0: promote strict validation to PASS_STRICT
```

### Session / Dashboard dual

```text
3eeee70 — SessionOverlay: V2 complete injection + Dashboard dual display hardening
```

### V7.2.1 parallèle — MultiSymbol / UI

```text
6834c7d — MultiSymbol: parametric symbol extension + cross-validation + scheduler
3879db5 — Docs: add MultiSymbol scheduler validation report
c97fb1c — Dashboard: add multiSymbol UI tabs + cross-validation card + USDJPY audit
```

---

## 4. Mission MultiSymbol Scheduler — état consolidé

### Fichiers clés

```text
pf_cross_symbol_validation.py
run_cross_symbol_validation_once.py
scheduler_powerflow.py
scheduler_config.json
setup_windows_task_scheduler.ps1
LEXIQUE_PATCH_MULTISYMBOL.md
REGISTRE_BRIQUES_PATCH_MULTISYMBOL.md
```

### Validation observée

```text
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
```

Premier problème :

```text
OVERLAP_SKIP cycle=1 previous lock active
```

Correction :

```powershell
Remove-Item .\logs\scheduler_powerflow.lock -Force
```

Résultat validé :

```text
CYCLE_END id=1 errors=0 consecutive_errors=0
SCHEDULER_SUMMARY completed_cycles=1
```

### Windows Task Scheduler

```text
Task name : PowerFlow_V72_MultiSymbol_Scheduler
Mode      : python scheduler_powerflow.py --once
Interval  : toutes les 5 minutes
Validation: CYCLE_END id=2 errors=0
```

Verdict :

```text
MULTISYMBOL AUTO-RUN VALIDÉ
```

---

## 5. Dashboard UI + USDJPY audit — état consolidé

### Commit

```text
c97fb1c — Dashboard: add multiSymbol UI tabs + cross-validation card + USDJPY audit
```

### Fichiers clés

```text
Core/LEXIQUE_PATCH_UI.md
Core/REGISTRE_PATCH_UI.md
Core/RAPPORT_DASHBOARD_UI_USDJPY_20260511.md
Core/audit_usdjpy_capture.py
Core/run_audit_usdjpy_once.py
Core/test_dashboard_tabs.py
Core/dashboard_cross_validation_card.html
Core/dashboard_live_multisymbol.html
Core/dashboard_multisymbol_ui_patch.html
Core/dashboard_live.html
Core/INTEGRATION_GUIDE.md
Core/PACK_MANIFEST.json
Core/validation_checklist.md
```

### Dashboard UI

```text
Tabs multi-symbol : GBPUSD | EURUSD | USDJPY | XAUUSD
Cross-validation card : ajoutée
USDJPY audit : ajouté
```

### Important

```text
output/ est ignoré par Git — normal.
dashboard_data.json est runtime legacy — ne pas committer.
```

---

## 6. SessionOverlay V2 + Dashboard dual — état consolidé

### Commit

```text
3eeee70 — SessionOverlay: V2 complete injection + Dashboard dual display hardening
```

### Fichiers clés

```text
Core/pf_session_overlay.py
Core/run_session_overlay_once.py
Core/patch_behavioral_alert_mapper.py
Core/test_session_overlay.py
Core/pf_behavioral_alert_mapper.py
Core/dashboard_live.html
Core/dashboard_dual_display_patch.html
Core/dashboard_freshness_module.js
Core/dashboard_session_card.html
Core/dashboard_contract_v2.json
Core/LEXIQUE_PATCH_SESSION_OVERLAY.md
Core/REGISTRE_BRIQUES_PATCH_SESSION.md
Core/deploy_powerflow_v72_session_dashboard_all_in_one.ps1
```

### Validation observée

```text
py_compile PASS
test_session_overlay.py PASS
run_session_overlay_once.py --pretty PASS
pf_behavioral_alert_mapper.py patché + compile PASS
dashboard_contract_v2.json valid JSON
dashboard_live.html patché
```

### Règle centrale

```text
session_context qualifie l’alerte.
session_context ne filtre jamais l’alerte.
```

---

## 7. État symboles

### GBPUSD

```text
Status : LIVE OK
Node   : HOT_NODE actif
Regime : TENDANCE confidence 1.0
Alerts : OK
```

### EURUSD

```text
Status : ENGINE OK / HTF INCOMPLETE
Regime : UNKNOWN confidence 0.0
Lecture: normal tant que le contexte HTF reste incomplet
```

### USDJPY

```text
Status     : ENGINE OK / DATA STALE_OR_THIN
Rows       : 1
Timestamp  : 2026-05-04T12:20:00+00:00
Lecture    : problème capture/data freshness, pas problème scheduler
Priorité   : audit MT4 / bridge / insertion DB
```

---

## 8. Ordre de lecture recommandé pour Claude

```text
1. Core/CURRENT_STATE_V7_OFFICIAL_20260511.md
2. Core/CLAUDE_md_V72_FINAL_UPDATE.md
3. Core/P0_PASS_STRICT_PROMOTION_20260511.md
4. Core/RAPPORT_COMPLET_POWERFLOW_V72_P0_PASS_STRICT_20260511.md
5. Core/LEXIQUE_PATCH_MULTISYMBOL.md
6. Core/REGISTRE_BRIQUES_PATCH_MULTISYMBOL.md
7. Core/docs/2026/2026-05/RAPPORT_MULTISYMBOL_SCHEDULER_20260511.md
8. Core/LEXIQUE_PATCH_UI.md
9. Core/REGISTRE_PATCH_UI.md
10. Core/RAPPORT_DASHBOARD_UI_USDJPY_20260511.md
11. Core/LEXIQUE_PATCH_SESSION_OVERLAY.md
12. Core/REGISTRE_BRIQUES_PATCH_SESSION.md
13. Core/RAPPORT_COMPLET_SESSION_DASHBOARD_V72_20260511.md
```

---

## 9. Ne pas confondre

```text
dashboard_data.json = output runtime legacy
output/ = runtime ignoré par Git
USDJPY stale/thin = capture/data freshness, pas scheduler
EURUSD UNKNOWN = HTF incomplet, pas bug moteur
OVERLAP_SKIP isolé = lock stale possible, pas panne si non répété
```

---

## 10. Prochaine mission logique

### Priorité 1 — document central Git

Créer puis committer :

```text
Core/CURRENT_STATE_POWERFLOW_V721_CENTRALISE_20260511.md
Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md
Core/RAPPORT_ETAT_LIEUX_POWERFLOW_V721_20260511.md
```

### Priorité 2 — audit USDJPY

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
python run_audit_usdjpy_once.py --db powerflow.db --pretty
```

Puis vérifier :

```sql
SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
FROM force_snapshots
WHERE symbol = 'USDJPY';
```

### Priorité 3 — vérifier MT4

```text
- symbol list EA
- bridge reçoit USDJPY
- insertion force_snapshots USDJPY
- timeframes attendus
```

---

## 11. Doctrine maintenue

```text
❌ Jamais BUY/SELL
❌ Jamais morale financière
❌ Session ne filtre pas les alertes
❌ Legacy/HMM jamais fusionnés
❌ Rolling/Wavelet jamais fusionnés
❌ STALE jamais invisible
✅ Session qualifie
✅ Duals côte à côte
✅ M1 central
✅ capture_bridge.py intouchable
✅ powerflow.db read-only dans pf_*
```

---

## 12. Commandes de vérification rapides

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT

git status
```

Si seul `Core/dashboard_data.json` est modifié :

```powershell
git restore Core\dashboard_data.json
```

P0 :

```powershell
cd Core
.\run_p0_final_auto.ps1 -Symbol GBPUSD
```

Scheduler :

```powershell
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
```

USDJPY :

```powershell
python run_audit_usdjpy_once.py --db powerflow.db --pretty
```

Dashboard :

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
```

---

## 13. Conclusion

```text
Claude n’a pas besoin de reconstruire P0.
Claude n’a pas besoin de réparer le dashboard.
Claude doit lire les documents Git listés ci-dessus.
Le vrai état V7.2.1 inclut maintenant :
- P0 PASS_STRICT
- MultiSymbol scheduler live
- Dashboard multi-symbol UI
- SessionOverlay V2
- USDJPY audit à poursuivre
```

**Décision : REBASE CLAUDE V7.2.1 — READY**
