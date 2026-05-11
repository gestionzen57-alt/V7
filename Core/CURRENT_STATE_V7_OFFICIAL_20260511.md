# CURRENT_STATE — PowerFlow V7.2 OFFICIAL

**Date :** 2026-05-11  
**Generated UTC :** 2026-05-11T10:30:45Z  
**Generator :** Automated pipeline + manual review  
**Authority :** Architectural Decision  
**Validity period :** Until next checkpoint — fenêtre complète ou `PASS_STRICT` atteint  
**Branch :** `main`  
**Referenced P0 recovery commit :** `8787dd6`  
**Latest confirmed commit :** `0dc2df6`  
**Status :** PRODUCTION LIVE — P0 CORE PASS / STRICT PENDING_DATA_WINDOW

---

## SECTION 1 — MÉTADONNÉES OFFICIELLES

```text
Document role      : source of truth current system state
System             : PowerFlow V7.2
Environment        : Live production recovery
Generated          : 2026-05-11T10:30:45Z
Generator          : Automated pipeline + manual review
Authority          : Architectural Decision
Validity           : 1 week max, or until PASS_STRICT / next checkpoint
```

Ce document est la version officielle du `CURRENT_STATE` pour archivage Git.  
Il reprend l’état post-P0 live et ajoute les confirmations finales dashboard / hydration / docs.

---

## SECTION 2 — GIT METADATA

```text
P0 core recovery commit       : 8787dd6
Dashboard contract commit     : aac44f0
Docs checkpoint commit        : f9cb7ba
Dashboard final delivery      : 93fc478
Wrapper hardening commit      : 0dc2df6
Branch                        : main
Remote                        : origin/main
Next commit expected          : Docs: archive Squad 2 final official state
```

### Référence P0

```text
8787dd6 = P0 core recovery
Statut associé = core perception PASS, strict pending data window
```

---

## SECTION 3 — ÉTAT GLOBAL OFFICIEL

```text
PowerFlow V7.2             = MOTEUR DE PERCEPTION LIVE
P0 Core Perception         = PASS
P0 Dashboard Flow          = PASS
P0 LTF Data Quality        = PASS
P0 Automation              = PASS
P0 Strict Full             = PENDING_DATA_WINDOW
Dashboard MAX              = FULL HYDRATION PASS / CONTRACT PASS
Hydration Failure Doctor   = 16 steps / 0 failed
```

### Verdict

```text
Le moteur perçoit.
La DB respire.
Les briques critiques sont vivantes.
Le dashboard montre.
Le strict attend une fenêtre statistique complète.
```

---

## SECTION 4 — VALIDATION CHECKLIST

```text
✅ PowerFlow perçoit
✅ Dashboard hydrate
✅ Runners répondent
✅ Data Quality LTF PASS
✅ B4/B5 PASS_ALIVE
✅ B4 qualifie LAG1_COMPRESSION au lieu de faux static fail
✅ B5 qualifie SPEARMAN_GRAVITY_ACTIVE
✅ Temporal Node State expose HOT_NODE / M1 microfilm
✅ P0 Dashboard PASS
✅ P0 Automation PASS
✅ Dashboard contract validation PASS 0 fail / 0 warn
✅ Hydration stack PASS 16 steps / 0 failed
✅ Failure doctor clean
⏳ P0 Strict PENDING_DATA_WINDOW — fenêtre en cours
```

---

## SECTION 5 — SOURCE P0 LIVE

### Capture LTF restaurée

```text
2026-05-08 23:50Z  : M5 arrêt
2026-05-08 23:30Z  : M15 arrêt
2026-05-11 01:00Z  : Bons EA rechargés
2026-05-11 01:15Z  : M5/M15 revenus
2026-05-11 01:47Z  : Fenêtre fraîche validée
```

### Densité DB live post-reprise

```text
TF1    : rows fraîches depuis 2026-05-11T01:24:00Z
TF5    : rows fraîches depuis 2026-05-11T01:15:00Z
TF15   : rows fraîches depuis 2026-05-11T01:15:00Z
TF30+  : historique / partiel selon fenêtre
```

---

## SECTION 6 — PIPELINE ACTIF

```text
capture_bridge.py              ✅ LIVE — intouchable
powerflow.db                   ✅ mémoire centrale — aucune écriture manuelle
pf_regime_engine.py            ✅ B1 Legacy
pf_hmm_regime_engine.py        ✅ B1+ HMM
pf_cascade_engine.py           ✅ B2 Cascade
pf_force_kinematics.py         ✅ B3 Kalman
pf_currency_energy_probe.py    ✅ P1 Energy
pf_temporal_density.py         ✅ B4 Rolling / PASS_ALIVE
pf_wavelet_density.py          ✅ B4+ Wavelet
pf_spearman_gravity.py         ✅ B5 / PASS_ALIVE
pf_memory_engine.py            ✅ B6 Memory
pf_fractal_resonance.py        ✅ B7 / PASS_ENGINE
pf_volatility_texture.py       ✅ B7+ Texture
pf_alert_entropy.py            ✅ Guard Entropy
pf_data_quality_guard.py       ✅ Guard DQ LTF
pf_session_overlay.py          ✅ Guard Session
pf_behavioral_alert_mapper.py  ✅ P2 Mapper
pf_temporal_node_state.py      ✅ Node
dashboard_*                    ✅ surface live contractuelle
```

---

## SECTION 7 — COMMANDES OPÉRATIONNELLES

### P0 validation

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
.\run_p0_final_auto.ps1 -Symbol GBPUSD
```

Résultat attendu :

```text
PASS_CORE_PARTIAL_STRICT
```

### Dashboard live

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD -Serve
```

### Dashboard validation

```powershell
.\run_dashboard_validate.ps1 -CorePath .
.\run_hydration_failure_doctor.ps1 -CorePath .
```

Résultat attendu :

```text
Contract PASS 0 fail / 0 warn
Hydration failure doctor : WARN/failed 0
```

---

## SECTION 8 — USAGE DOCUMENTATION

### Source of truth

Ce fichier est la source de vérité de l’état système courant.

À utiliser pour :

```text
- reprise nouveau fil IA
- checkpoint Git
- audit de statut P0
- vérification avant phase Telegram / production enrichie
```

### Validité temporelle

```text
Validité recommandée : 1 semaine max.
Rafraîchir immédiatement si :
  - PASS_STRICT atteint
  - nouveau commit moteur critique
  - changement capture / EA / bridge
  - dashboard contract non-PASS
```

### Escalation path si problème

```text
1. Lire output/DASHBOARD_CONTRACT_VALIDATION.md
2. Lire output/DASHBOARD_HYDRATION_FAILURE_DOCTOR.md
3. Relancer .\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
4. Relancer .\run_p0_final_auto.ps1 -Symbol GBPUSD
5. Ne pas patcher pf_* avant classification technique
6. Ne jamais modifier capture_bridge.py / powerflow.db sans décision architecte
```

---

## SECTION 9 — RÈGLES OFFICIELLES

```text
❌ capture_bridge.py : intouchable
❌ powerflow.db : aucune écriture manuelle
❌ B1/B1+ : ne jamais fusionner
❌ B4/B4+ : ne jamais fusionner
❌ Memory : fréquence historique, pas probabilité
❌ Dashboard : ne jamais recycler ancienne valeur sans STALE
✅ Dashboard hydrate avant session
✅ P0 validation pour suivre fenêtre
✅ MISSING / STALE / DEGRADED explicites
✅ Technical risks visibles
```

---

## SECTION 10 — PROCHAIN STATUT ATTENDU

```text
Déclencheur       : fenêtre statistique complète
Évolution attendue: PENDING_DATA_WINDOW → PASS_STRICT
Action            : run_p0_final_auto.ps1 + commit statut
Message attendu   : P0: promote strict validation from pending data window to PASS_STRICT
```

---

## ANNEXE — SOURCE POST-P0 INTÉGRÉE

Le document source `CURRENT_STATE_V72_POST_P0_20260511.md` signalait déjà :

```text
P0 Core Perception     : PASS
P0 Dashboard Flow      : PASS
P0 LTF Data Quality    : PASS
P0 Strict Full         : PARTIAL / PENDING_DATA_WINDOW
```

Cette version officialise l’état avec les confirmations dashboard final, hydration stack et wrapper hardening.

---

*CURRENT_STATE_V7_OFFICIAL_20260511 — PowerFlow V7.2 — validité jusqu’au prochain checkpoint.*
