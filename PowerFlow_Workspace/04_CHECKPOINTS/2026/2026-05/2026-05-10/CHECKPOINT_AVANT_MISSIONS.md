# CHECKPOINT FINAL — PowerFlow V7.1
**Date : 2026-05-09 | Statut : PRÉ-MISSION SAMEDI | Token : changement forfait demain**

---

## 📊 ÉTAT GLOBAL

```
PowerFlow V7.1         : ✅ PRODUCTION LIVE
Pipeline               : ✅ 9 steps orchestrateur complet
Dashboard              : ✅ 4 live guard cards
Documentation         : ✅ Complète + 6 fichiers livrables
Git                   : ✅ Propre (acbe258 dashboard + orchestrator)

TOKEN STATUS (CRITIQUE)
  Session actuelle     : 31% utilisés
  Hebdo               : 97% utilisés (réinit mardi 20h)
  Forfait             : Standard (changeront demain max)
```

---

## 🎯 MISSIONS CONFIRMÉES AVANT LUNDI

### SAMEDI — 3 BRIQUES À UPGRADER

#### ✅ B1 HMM (SAMEDI MATIN)
```
Statut          : À CODER
Rôle            : HTF regime confidence (remplace heuristique)
Données dispo   : TF60 133 rows + TF240 39 rows
Entrée          : angle + speed + zone_state
Sortie          : regime (0=COMPRESSION, 1=TENDANCE, 2=RANGE) + confidence (0-1)
Impact          : Toutes les alertes deviennent + qualifiées
Durée estimée   : 1-2 jours
Dépendances     : hmmlearn (pip install hmmlearn)
Validation      : Comparer HMM vs heuristique sur snapshot live

PRIORITÉ : 🔴 CRITIQUE (affecte TOUTES alertes)
```

#### ✅ B4 WAVELET (SAMEDI APRÈS-MIDI)
```
Statut          : À CODER
Rôle            : Cycle density robuste (remplace autocorr fragile)
Méthode         : Morlet CWT (Continuous Wavelet Transform)
Données dispo   : force_rolling_window 100 barres (déjà en DB)
Entrée          : signal brut TF5
Sortie          : compression_ratio (0-1) + cycle_state (COMPRESSING/EXPANDING/STABLE)
Impact          : B4 moins bruyant, moins faux positifs
Durée estimée   : 1 jour
Dépendances     : pywt (pip install PyWavelets)
Validation      : Comparer wavelet vs autocorr sur même fenêtre

PRIORITÉ : 🟡 HAUTE (core robustesse)
```

#### ✅ MEMORY V1 (SAMEDI SOIR)
```
Statut          : À CODER
Rôle            : Pattern memory (quand ce pattern s'est produit avant, quoi après ?)
Méthode         : Hash pattern comportemental + lookup queue
Données dispo   : behavioral_alert_queue.json (existante)
Entrée          : alert_type + regime + session + EIE + B4 + B5
Sortie          : {occurrences: N, outcomes: [list], median_duration: X bars}
Impact          : Trader voit "ce pattern = 7 fois avant = 5 fois expansion"
Durée estimée   : 1 jour
Dépendances     : Python standard (hash, json)
Validation      : Query sur 5 patterns différents

PRIORITÉ : 🟢 HAUTE (nouveau levier utile)
```

### DIMANCHE — VALIDATION + COMMIT

```
Matin   : Tests live B1 HMM + B4 Wavelet + Memory V1
Après   : Git commit "V7.1.1: B1 HMM + B4 Wavelet + Memory V1"
Soir    : CHECKLIST_DIMANCHE (15 min) + sleep
```

### LUNDI 02h00 UTC — P0 AUTOMATION

```
GPT lance : python .\run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD
GPT remplit : P0_MARKET_OPEN_VALIDATION.md
GPT décide : PASS ou FAIL
GPT commite : "P0: Market open validation — [PASS|FAIL]"
GPT push : origin main

Durée : 5 min (GPT seul)
Toi   : dors
```

---

## 📁 LIVRABLES ACTUELS (DÉJÀ CRÉÉS)

```
✅ P0_GUIDE_EXPLICATIF_SIMPLE.md
   → Explique les 7 vérifications à faire lundi
   → Template à remplir

✅ CLAUDE_md_V7_1_FINAL.md
   → État complet V7.1 après GPT1/GPT2
   → Commandes, critères, plan

✅ CURRENT_STATE_V7.1_FINAL.md
   → Inventory détaillé tous modules
   → DB densité, outputs JSON, dépendances

✅ PROMPT_P0_AUTOMATION_COMPLET.md
   → À donner à GPT lundi 02h00 UTC
   → Toutes les étapes P0 automatisées

✅ CHECKLIST_DIMANCHE_AVANT_P0.md
   → Checklist à toi faire dimanche soir
   → py_compile, git, vérifications

✅ RESUME_FINAL_SEMAINE_P0.md
   → Vue macro stratégique
   → Calendrier court/moyen terme

📂 TOUS DANS : /mnt/user-data/outputs/
   → À télécharger et mettre dans PowerFlow_Workspace/00_CURRENT/
```

---

## 🎯 MISSIONS À ENCODER SAMEDI (AVANT LUNDI)

### MISSION 2️⃣ — B4 WAVELET (pour GPT Pro 1)

```
Fichier à créer    : Core/pf_wavelet_density.py
Entrée             : force_rolling (100 barres TF5)
Sortie JSON        : output/wavelet_density.json
Runner             : run_wavelet_density_once.py (utiliser pywt)
Validation         : Comparer compression_ratio(wavelet) vs compression_ratio(autocorr)

Prompt requis      : 📌 À CRÉER CI-DESSOUS
```

### MISSION 3️⃣ — MEMORY V1 (pour GPT Pro 2)

```
Fichier à créer    : Core/pf_memory_engine.py
Entrée             : behavioral_alert_queue.json (existante)
Sortie JSON        : output/memory_query_results.json
Runner             : run_memory_query_once.py (query sur pattern actuel)
Validation         : 5 queries différentes = 5 résultats cohérents

Prompt requis      : 📌 À CRÉER CI-DESSOUS
```

---

## 🔄 PROCHAINES ÉTAPES (TU DOIS FAIRE)

### AUJOURD'HUI (dimanche soir)
```
[ ] Télécharger les 6 fichiers checkpoint
[ ] Les mettre dans PowerFlow_Workspace/00_CURRENT/
[ ] git add . && git commit -m "Checkpoint: V7.1 final — avant missions B4+Memory"
[ ] git push origin main

DURÉE : 10 min
```

### DEMAIN (lundi)
```
[ ] Changer forfait à MAX (problème technique résolu ?)
[ ] Commencer missions B4 + Memory (j'ai les prompts prêts)
[ ] Ou si pas changement forfait : Haiku 4.5 suffit pour les 2 missions
```

### SAMEDI (jour missions)
```
[ ] GPT Pro 1 → PROMPT B4 WAVELET
[ ] GPT Pro 2 → PROMPT MEMORY V1
[ ] Toi : valider + tester + commit
```

### DIMANCHE (avant P0)
```
[ ] Checklist final
[ ] Git commit final
[ ] Dors
```

### LUNDI 02h00 UTC (Asian open)
```
[ ] GPT reçoit PROMPT_P0_AUTOMATION_COMPLET.md
[ ] Tu dors
[ ] 5 min plus tard : verdict P0
```

---

## 📋 RESSOURCES DISPO MAINTENANT

### Code rough à utiliser

**B4 Wavelet :**
```python
import pywt
import numpy as np

signal = force_rolling_window  # 100 barres
scales = np.arange(1, 65)
coeffs = pywt.cwt(signal, scales, 'morlet')
power = np.abs(coeffs) ** 2
compression_ratio = max(power.sum(axis=1)) / power.sum()

cycle_state = "CYCLE_COMPRESSING" if compression_ratio > 0.75 else "CYCLE_EXPANDING"
```

**Memory V1 :**
```python
def pattern_hash(alert):
    return hash((
        alert["alert_type"],
        alert["regime_context"]["regime"],
        alert.get("EIE_state", "NEUTRAL"),
        alert.get("B4_state", "NEUTRAL"),
        alert.get("B5_direction", "NEUTRAL")
    ))

similar = [a for a in queue if pattern_hash(a) == pattern_hash(current)]
return {"occurrences": len(similar), "outcomes": [...]}
```

---

## 🎯 POINTS CRITIQUES

### ✅ CONFIRMÉ
```
B1 HMM pas codé samedi (pas urgent avant lundi)
B4 Wavelet à coder samedi (remplace autocorr)
Memory V1 à coder samedi (nouveau levier)
P0 lundi = automatisé par GPT
Tu dois juste les prompts pour B4 + Memory
```

### ⚠️ ATTENTION
```
Forfait token : tu changes demain (Max)
Session tokens : 97% utilisés (réinit mardi 20h)
Haiku 4.5 : suffisant si besoin immédiat
Dois-tu coder ou juste donner prompts ? 
  → Réponse : juste prompts (j'ai code rough)
```

### 🚨 NE PAS FAIRE AVANT LUNDI
```
❌ Multi-Symbol (architectural, après P0 stable)
❌ B5 Copula (après lundi)
❌ Volatility Texture complète (après lundi)
❌ Fractal Resonance (après lundi)
❌ Lab Engine V2 (après lundi)
```

---

## 📌 PROMPTS À CRÉER (PROCHAINS)

### Pour GPT Pro 1 — B4 WAVELET
```
🔴 STATUS : À créer
📝 DURÉE : 5 min
🎯 CIBLE : Full pf_wavelet_density.py + runner
🔧 TECH : pywt (Morlet CWT), numpy, json output
✅ VALIDATION : comparaison wavelet vs autocorr
```

### Pour GPT Pro 2 — MEMORY V1
```
🔴 STATUS : À créer
📝 DURÉE : 5 min
🎯 CIBLE : Full pf_memory_engine.py + runner + queries
🔧 TECH : hash pattern, json, historical lookup
✅ VALIDATION : 5 queries différentes
```

---

## 📊 RÉSUMÉ EXÉCUTIF

```
CHECKPOINT COMPLET ✅
  Tous les documents créés et téléchargeable
  État V7.1 clair et documenté
  Plan P0 lundi 02h00 = 100% automatisé (GPT)
  
AVANT MISSIONS SAMEDI ✅
  Code rough fourni (copier-coller possible)
  Prompts GPT à créer (j'ai les specs)
  Dépendances claires (pywt pour B4, json pour Memory)

SAMEDI-DIMANCHE ✅
  B4 Wavelet : 1 jour
  Memory V1 : 1 jour
  Tests + commit : dimanche

LUNDI 02h00 UTC ✅
  P0 automation (GPT seul)
  Toi : dors
  Verdict : PASS/FAIL (probablement PASS)
```

---

## 🎬 ACTIONS IMMÉDIATES

### TOI MAINTENANT
```
1. Télécharge 6 fichiers checkpoint
2. git commit + push
3. Attends les prompts B4 + Memory (je les créé dans 5 min)
```

### DEMAIN (lundi)
```
1. Change forfait MAX si possible
2. Reçois prompts B4 + Memory
3. Lance GPT Pro 1 + GPT Pro 2
```

### SAMEDI
```
1. GPT Pro 1 code B4 Wavelet
2. GPT Pro 2 code Memory V1
3. Toi : valide + commit
```

### DIMANCHE
```
1. Checklist final
2. Dors bien
```

### LUNDI 02h00 UTC
```
1. P0 automation (GPT)
2. PASS verdict
3. Scheduler P1
```

---

*CHECKPOINT COMPLET — Prêt missions B4 + Memory — 2026-05-09*
