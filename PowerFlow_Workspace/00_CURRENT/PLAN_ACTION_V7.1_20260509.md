# PLAN D'ACTION — PowerFlow V7.1
**Mode guerre | Chef d'orchestre : Claude Projects | 2026-05-09**

---

## SITUATION

V7.1 sprint 7J LIVRÉ par Gemini/Perplexity.
12 nouveaux modules en production.
Git propre.
LEXIQUE à jour.
CURRENT_STATE, ROADMAP, REGISTRE = encore sur V7 base → mis à jour ce soir.

**PROCHAINE ÉTAPE CRITIQUE : P0 — Lundi 12 mai 23h CEST (Asian open)**

---

## CETTE SEMAINE — SÉQUENCE EXACTE

### MAINTENANT (ce soir/dimanche)
```
1. Mettre à jour docs dans workspace :
   → CURRENT_STATE_V7.1_20260509.md [FAIT]
   → git_sync.ps1 "Docs: CURRENT_STATE V7.1 + delegation prompts"

2. Vérifier que les 12 modules V7.1 compilent proprement :
   for f in pf_data_quality_guard.py pf_market_open_validator.py \
             pf_entropy_engine.py pf_session_overlay.py \
             pf_replay_engine.py pf_film_engine.py; do
     python -m py_compile $f && echo "OK: $f" || echo "FAIL: $f"
   done

3. Test DB santé avant lundi :
   python run_data_quality_guard_once.py --db powerflow.db --pretty
```

### DÉLÉGATION GPT1 (cette semaine)
```
Mission : run_powerflow_cycle_once.py
→ Copier prompt GPT1 depuis PROMPTS_DELEGATION_GPT1_GPT2_V7.1.md
→ Livrable : orchestrateur cycle 5min complet
→ Tester : python run_powerflow_cycle_once.py --db powerflow.db --dry-run
```

### DÉLÉGATION GPT2 (cette semaine)
```
Mission : Dashboard Cards V7.1
→ Copier prompt GPT2 depuis PROMPTS_DELEGATION_GPT1_GPT2_V7.1.md
→ Livrable : 4 nouvelles cards HTML/JS
→ Intégrer dans dashboard_live.html
```

### LUNDI 12 MAI — 23h CEST (Asian open)
```
P0 VALIDATION — SÉQUENCE OBLIGATOIRE :

python .\run_data_quality_guard_once.py --db .\powerflow.db --pretty
python .\run_market_open_validator_once.py --db .\powerflow.db --recent-minutes 180 --pretty
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
python -c "from lab_elastic import q_eie_snapshot; q_eie_snapshot()"
python run_confluence_alert.py --once --dry-run
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
python .\run_session_overlay_once.py --timestamp now --pretty

→ Remplir P0_MARKET_OPEN_VALIDATION.md (template dans prompts délégation)
→ git_sync.ps1 "P0: Market open validation ASIAN 20260512"
```

### SEMAINE 12 MAI — APRÈS P0 PASS
```
P1 : Task Scheduler → run_powerflow_cycle_once.py automatisé (Windows Task Scheduler)
P2 : Dashboard V7.1 Cards activées
P3 : Lab Engine V2 — 6 queries trading B4+B5+regime
```

---

## CE QUI EST GELÉ JUSQU'APRÈS P0+P1
```
❌ Fractal Resonance
❌ Volatility Texture
❌ Memory Engine B6
❌ Multi-Symbol
❌ B1 HMM
❌ B4 Wavelet
```

---

## CRITÈRES P0 PASS

```
B4  : dominant_period_bars ≠ 1 sur TF1 et TF5
B5  : rho fluctuant, labels non figés
EIE : snapshot ≠ NEUTRAL si tension réelle
DB  : fraîche, no stale critique, no gaps majeurs
Session : ASIAN confirmé à 23h CEST
Entropy : alert_entropy_state ≠ SATURATED
```

---

## DÉLÉGATION CLAIRE

```
Claude Projects (toi) = Chef d'orchestre
  → Vision, architecture, prompts, validation finale
  → Ne pas coder les modules simples = économie de tokens

GPT1 = run_powerflow_cycle_once.py
  → Infra / algo / subprocess / rapport JSON cycle

GPT2 = Dashboard Cards V7.1
  → HTML/JS vanilla / 4 cards / polling 30s

Perplexity / Gemini = si nouveau sprint 7J+ nécessaire
  → Donner contexte ONBOARDING_IA + CLAUDE.md V7.1 + mission précise
```

---

## TOKEN BUDGET — RÈGLE DE FER

```
Claude Projects = questions architecturales + validation + prompts délégation
Claude Projects ≠ coder 200 lignes de Python simple

Si la tâche peut être déléguée avec un prompt de 30 lignes → déléguer
Si la tâche nécessite la vision doctrine → Claude Projects
```

---

*Plan d'action PowerFlow V7.1 — 2026-05-09 — Mode guerre*
