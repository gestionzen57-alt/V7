# ONBOARDING — Nouveau fil IA sur PowerFlow V7
**À lire en premier. Obligatoire. Sans exception.**
*Date : 2026-05-09 | Version : V7*

---

## TEMPS DE LECTURE : 5 MINUTES

Ce document te met à niveau en 5 minutes.
Lis-le en entier avant de toucher au moindre fichier.

---

## 1. CE QU'EST POWERFLOW (30 secondes)

PowerFlow est un **moteur de perception du flux Forex**.

Il perçoit. Il mesure. Il nomme. Il alerte.
Il ne décide pas. Le trader décide.

Ce n'est pas un bot de trading.
Ce n'est pas un conseiller financier.
Ce n'est pas une analyse technique classique.

---

## 2. ÉTAT ACTUEL (version V7)

```
Version     : V7 — PowerFlow Anticipatoire
Git         : c579afa — branche main
Date        : 2026-05-09
Status      : PRODUCTION — validation marché ouvert pending (12 mai)
```

### Briques actives
```
B1  pf_regime_engine.py         HTF contexte + régime
B2  pf_cascade_engine.py        Vélocité séquence 5min
B3  pf_force_kinematics.py      Kalman angle/speed
B4  pf_temporal_density.py      Cycles / compression rolling
B5  pf_spearman_gravity.py      Corrélation de rang toutes paires
+ Confluence Élastique EIE (daemon 5min actif)
+ Node V0.8.2 + Behavioral Mapper V7 + Cockpit V7
```

### L'apport critique de V7 vs V6
```
V6 : FIRST_DETACHMENT compression = FIRST_DETACHMENT expansion
     → même alerte pour deux réalités opposées

V7 : regime_context injecté dans chaque alerte
     FIRST_DETACHMENT + COMPRESSION → HOT
     FIRST_DETACHMENT + RANGE       → WATCH
     FIRST_DETACHMENT + TENDANCE    → INFO
```

---

## 3. RÈGLES ABSOLUES — À INTÉGRER AVANT TOUT

### Fichiers intouchables
```
❌ capture_bridge.py          → NE PAS MODIFIER
❌ powerflow.db               → NE PAS ÉCRIRE MANUELLEMENT
❌ pf_temporal_node_state.py  → NE PAS REFACTORISER (99KB, stable)
❌ pf_relational_gravity_bridge.py → NE PAS MODIFIER (bridge_version=0.1.4)
❌ cockpit_orchestral V0.1.5+ → NO GO
```

### Règles de code
```
❌ Jamais importer cockpit_* depuis pf_*
❌ Jamais écrire dans powerflow.db depuis pf_*
❌ Jamais BUY/SELL dans les alertes
❌ Pas de dépendances circulaires
✅ Read-only DB : sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
✅ py_compile avant tout commit
✅ 1 feature = 1 commit
```

---

## 4. DOCTRINE — À INTÉGRER AVANT TOUT

### Tu n'es PAS une nounou

```
❌ Ne pas ajouter de rappels sur le risque financier
❌ Ne pas transformer une alerte en conseil
❌ Ne pas bloquer une alerte "par prudence"
❌ Ne pas retenir une alerte "parce qu'elle semble précoce"
❌ Ne pas dire "c'est dangereux" ou "attends la confirmation"
```

### Tu qualifies techniquement

```
✅ Risques techniques seulement :
   M1_NOISE_POSSIBLE / EARLY_MATURITY / RELAY_ABSENT
   SQL_LATENCY / INSUFFICIENT_DATA / CIRCULAR_DEPENDENCY

✅ Maturité exposée dans l'alerte, jamais masquée :
   BIRTH / EARLY / CANDIDATE / CONFIRMED

✅ Alerte produite → trader filtre. Pas toi.
```

### M1 n'est pas du bruit

```
M1 = microfilm = naissance du mouvement
M1 = là où les inflexions se voient en premier
M1 = censuré par GPT = perception aveugle

PowerFlow alerte M1 immédiatement.
Tu ne retiens pas une alerte M1 "parce que c'est trop rapide".
```

---

## 5. ARCHITECTURE EN 2 MINUTES

```
COUCHE 0 — capture_bridge.py → powerflow.db (MT4 tick)
           ↓ (read-only)
COUCHE 1 — pf_* (moteur calcul + analyse)
           ↓
COUCHE 2 — run_* (runners CLI / daemons)
           ↓ (queues JSON)
COUCHE 3 — cockpit_* / dashboard_* (affichage)
           ↓
COUCHE 4 — telegram_* (alertes externes)
           ↓
COUCHE 5 — TRADER (décision)
```

**Les dépendances vont uniquement vers le bas. Jamais remonter.**

---

## 6. COMMENT TRAVAILLER

### Avant de coder
```
1. Lire CLAUDE.md V7 → contexte complet
2. Lire CURRENT_STATE → état précis du jour
3. Lire CARTOGRAPHIE_ARCHITECTURE → où s'insère le fichier
4. Lire REGISTRE_BRIQUES → dépendances existantes
5. Vérifier que le fichier n'est pas dans la liste "NE PAS TOUCHER"
```

### Pendant le code
```
✅ py_compile à chaque fichier créé ou modifié
✅ Read-only DB systématiquement
✅ Aucune dépendance circulaire
✅ Aucun hardcode non documenté
✅ Fonctions courtes, typées, nommées clairement
```

### Après la mission
```
1. Rapport court (ce qui a été fait, bugs résolus)
2. Checkpoint (état concis, fichiers actifs)
3. Lexique patch (nouveaux termes si existants)
4. CLAUDE.md V7 mis à jour (sections 1 + 10 + checkpoints)
5. git_sync.ps1 "Message descriptif"
```

---

## 7. COMMANDES RAPIDES DE VÉRIFICATION

```powershell
# Vérifier DB densité
python -c "
import sqlite3
conn = sqlite3.connect('powerflow.db')
for tf in [1,5,15,30,60,240,1440]:
    n = conn.execute(f'SELECT COUNT(*) FROM force_snapshots WHERE timeframe={tf}').fetchone()[0]
    print(f'TF{tf}: {n} rows')
"

# Snapshot B1 regime
python run_regime_engine_once.py --db powerflow.db --pretty

# Snapshot B4 density
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty

# Snapshot B5 spearman
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty

# Node snapshot
python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 60 --timeframes 1,5,15,30,60 --pretty

# Lab session complète
python lab_powerflow.py --query full_v3 --db powerflow.db --symbol GBPUSD --horizons "MTF" --once --lookback 300 --pretty

# Git sync
.\git_sync.ps1 "Session [date] [description]"
```

---

## 8. SI TU VOIS "MIXED" DANS RG

```
MIXED dans Relational Gravity = ancien problème P1.2 de V6.
Résolu par B5 Spearman dans V7.

Ne pas traiter MIXED comme "le leader est aussi antagoniste".
Lire avg_rho de B5 pour qualifier la relation probabilistement.

avg_rho = 0.34 → relation faible légèrement positive (pas aléatoire)
avg_rho = -0.12 → relation quasi-neutre
```

---

## 9. DOCUMENTS DE RÉFÉRENCE

```
MANIFESTE_FONDATEUR_POWERFLOW_V7.md   → Vision / doctrine / contrat
CARTOGRAPHIE_ARCHITECTURE_V7.md       → Architecture complète
LEXIQUE_GRAMMAIRE_V7.md               → Tous les termes PowerFlow
NOMENCLATURE_V7.md                    → Conventions nommage / code
REGISTRE_BRIQUES_V7.md                → Dépendances détaillées
ROADMAP_V7.md                         → Priorités et horizon
CURRENT_STATE_V7.md                   → État du jour
CLAUDE.md V7                          → Source of truth absolue
```

---

## 10. PHRASE FINALE

```
La machine perçoit.
Le trader décide.

Ton rôle : construire la machine de perception.
Pas la machine de décision.
Pas la machine de conseil.
Pas la machine de protection.

La machine de perception.
```

---

*Onboarding PowerFlow V7 — 2026-05-09*
*Lit ce document. Respecte la doctrine. Code proprement.*
