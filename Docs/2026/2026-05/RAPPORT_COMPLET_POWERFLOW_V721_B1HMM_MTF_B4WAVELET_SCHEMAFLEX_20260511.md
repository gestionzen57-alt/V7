# RAPPORT COMPLET — PowerFlow V7.2.1 B1+ HMM MTF + B4+ Wavelet Schema-Flex

**Date :** 2026-05-11  
**Version cible :** PowerFlow V7.2.1  
**Mission :** Déploiement dual B1+ HMM MTF et B4+ Wavelet Morlet schema-flex  
**Repo :** `https://github.com/gestionzen57-alt/V7.git`  
**Branche :** `main`  
**Commit initial pack :** `6a320d4`  
**Commit hotfix final :** `71c2f91`  
**Statut final :** `PASS`  
**Posture :** Production live / extension validée  

---

## 1. Résumé exécutif

La mission B1+ HMM et B4+ Wavelet a été livrée, corrigée, validée et poussée dans Git.

La première version a livré les fichiers attendus, mais elle contenait trois problèmes techniques :

1. `hmmlearn` ne s'installait pas sous Python 3.14 sans toolchain C++.
2. Le moteur attendait initialement un schéma DB trop strict.
3. Le script one-click marquait certaines étapes en `PASS` malgré des erreurs runtime.

Le hotfix final `71c2f91` corrige ces points.

Résultat final :

```text
B1+ HMM MTF      : ACTIVE
B4+ Wavelet      : ACTIVE
Schema DB        : wide_currency
Time column      : created_at
Force source     : force_gbp
HMM method       : HMM_GAUSSIAN_FALLBACK_NUMPY
Wavelet method   : CWT_MORLET
Commit pushed    : 71c2f91
Final status     : PASS
```

Le point architectural central est validé :

```text
TF1440 n'est plus un blocker.
B1+ HMM respire via H1 / M30 / M15.
H4 / D enrichissent le contexte s'ils sont disponibles.
```

---

## 2. Objectif fonctionnel

### Demande initiale

Livrer un pack complet avec deux upgrades duals :

```text
UPGRADE 1 — B1+ HMM REGIME ENGINE
UPGRADE 2 — B4+ WAVELET MORLET DENSITY ENGINE
```

Ces briques doivent coexister avec leurs versions legacy :

```text
B1  Legacy heuristic    : pf_regime_engine.py
B1+ HMM Gaussian        : pf_hmm_regime_engine.py

B4  Rolling autocorr    : pf_temporal_density.py
B4+ Wavelet Morlet CWT  : pf_wavelet_density.py
```

Règle maintenue :

```text
Jamais fusionner B1 + B1+
Jamais fusionner B4 + B4+
Dual architecture = exposition parallèle, pas moyenne, pas arbitrage machine.
```

### Correction doctrinale demandée

La première version bloquait B1+ HMM sur :

```text
TF1440 < 50 rows -> INSUFFICIENT_DATA
```

Correction demandée :

```text
C'est multi-timeframe.
Pas besoin d'attendre H4 / D / TF1440.
On peut travailler en H1, M30, M15.
```

Correction appliquée :

```text
B1+ HMM MTF active sur timeframes 60 / 30 / 15.
TF240 / TF1440 deviennent contextuels, non bloquants.
```

---

## 3. Architecture finale livrée

### B1+ HMM MTF

**Fichier :** `Core/pf_hmm_regime_engine.py`  
**Runner :** `Core/run_hmm_regime_once.py`  
**Output :** `Core/output/dashboard_surface/regime_hmm.json`  

Stack actif :

```text
MTF core       : 60, 30, 15
HTF context    : 240, 1440
Activation     : >= 50 observations MTF agrégées
Fallback       : B1_LEGACY uniquement si MTF insuffisant
```

États produits :

```text
COMPRESSION
TENDANCE
RANGE
TRANSITION
```

Champs clés :

```json
{
  "regime_hmm": "TRANSITION",
  "regime_confidence_hmm": 0.460418,
  "state_probabilities": {
    "COMPRESSION": 0.147249,
    "TENDANCE": 0.209628,
    "RANGE": 0.182705,
    "TRANSITION": 0.460418
  },
  "method": "HMM_GAUSSIAN_FALLBACK_NUMPY",
  "status": "ACTIVE",
  "rows_used": 973,
  "mtf_timeframes": [60, 30, 15],
  "context_timeframes": [240, 1440],
  "regime_scope": "HTF_ENRICHED",
  "schema_mode": "wide_currency"
}
```

### B4+ Wavelet Morlet

**Fichier :** `Core/pf_wavelet_density.py`  
**Runner :** `Core/run_wavelet_density_once.py`  
**Output :** `Core/output/dashboard_surface/wavelet.json`  

Stack actif :

```text
Timeframes : 1, 5, 15
Wavelet    : Morlet CWT
Méthode    : CWT_MORLET
Signal     : auto-détecté depuis force_gbp
```

États produits :

```text
WAVELET_COMPRESSING
WAVELET_EXPANDING
WAVELET_MULTI_SCALE
WAVELET_TRANSITIONING
WAVELET_SILENT
```

Sortie validée :

```text
TF1  : WAVELET_MULTI_SCALE | dominant_scale=21 | drift=COMPRESSING
TF5  : WAVELET_MULTI_SCALE | dominant_scale=53 | drift=EXPANDING
TF15 : WAVELET_MULTI_SCALE | dominant_scale=54 | drift=EXPANDING
```

---

## 4. Évolution des scripts de déploiement

### Pack initial

Livré :

```text
powerflow_v72_b1hmm_b4wavelet.zip
```

Puis corrigé vers :

```text
powerflow_v721_b1hmm_mtf_b4wavelet.zip
powerflow_v721_b1hmm_mtf_b4wavelet_oneclick.zip
```

### One-click initial

Script :

```text
powerflow_v721_oneclick_deploy.ps1
```

Problème :

```text
Le script marquait PASS même quand des commandes Python avaient échoué.
```

### Hotfix git-root

Script :

```text
powerflow_v721_hotfix_gitroot_oneclick.ps1
```

Correction :

```text
Détection de la racine Git via git rev-parse --show-toplevel.
```

### Hotfix schema-flex final

Script :

```text
powerflow_v721_schemaflex_hotfix_oneclick.ps1
```

Résultat :

```text
[PASS] run B1+ HMM schema-flex once
[PASS] run B4+ Wavelet schema-flex once
[PASS] git push
FINAL: PASS
```

---

## 5. Problèmes rencontrés et corrections appliquées

### 5.1 hmmlearn indisponible sous Python 3.14

Erreur observée :

```text
error: Microsoft Visual C++ 14.0 or greater is required
Failed building wheel for hmmlearn
```

Cause :

```text
hmmlearn n'avait pas de wheel directement utilisable dans l'environnement Python 3.14.
pip tentait de compiler une extension C++.
```

Correction :

```text
hmmlearn devient optionnel.
Si hmmlearn est absent, B1+ HMM utilise un fallback interne NumPy.
```

Sortie finale :

```text
"HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED"
"No module named 'hmmlearn'"
```

Statut :

```text
Non bloquant.
B1+ HMM reste ACTIVE.
```

### 5.2 Colonne timestamp absente

Erreur observée :

```text
sqlite3.OperationalError: no such column: timestamp
```

Cause :

```text
La DB réelle utilise created_at au lieu de timestamp.
```

Correction :

```text
Détection automatique de colonne temporelle.
Ordre de recherche :
timestamp, created_at, time, ts, datetime, date, rowid
```

Sortie finale :

```text
"time_column": "created_at"
```

### 5.3 Colonnes devises nommées différemment

Erreur observée :

```text
RuntimeError: not enough currency columns in force_snapshots
```

Cause :

```text
Le schéma réel utilise force_gbp, force_usd, force_eur...
au lieu de gbp, usd, eur...
```

Correction :

```text
Introspection schema-flex.
Modes supportés :
- wide_currency
- long_currency
- generic_numeric
```

Sortie finale :

```json
{
  "schema_mode": "wide_currency",
  "observed_columns": [
    "force_gbp",
    "force_usd",
    "force_eur",
    "force_jpy",
    "force_cad",
    "force_chf",
    "force_aud"
  ]
}
```

### 5.4 Faux PASS du script

Erreur observée :

```text
[PASS] run B1+ HMM MTF once - ok
```

malgré crash Python.

Correction :

```text
Le script final vérifie explicitement les exit codes.
Si runner ou test échoue, le commit/push est bloqué.
```

Statut final :

```text
Corrigé.
```

### 5.5 SQLite temporaire verrouillé sous Windows

Erreur observée :

```text
PermissionError: WinError 32
TemporaryDirectory cleanup failed on pf.db
```

Cause :

```text
Windows garde parfois un handle SQLite quelques millisecondes après fermeture.
```

Correction :

```text
Connexions SQLite fermées explicitement.
Tests adaptés pour ignorer les erreurs de cleanup non critiques.
```

Statut final :

```text
Tests PASS.
```

---

## 6. Validation finale

### Tests

```text
test_hmm_regime PASS
test_wavelet_density PASS
py_compile PASS
architecture guards PASS
```

### Runners

#### B1+ HMM

Commande :

```powershell
python run_hmm_regime_once.py --db powerflow.db --symbol GBPUSD --tfs 60,30,15 --pretty
```

Résultat :

```text
status       : ACTIVE
rows_used    : 973
regime_hmm   : TRANSITION
confidence   : 0.460418
scope        : HTF_ENRICHED
schema       : wide_currency
```

#### B4+ Wavelet

Commande :

```powershell
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
```

Résultat :

```text
status       : ACTIVE
schema       : wide_currency
source       : force_gbp
TF1          : WAVELET_MULTI_SCALE / COMPRESSING
TF5          : WAVELET_MULTI_SCALE / EXPANDING
TF15         : WAVELET_MULTI_SCALE / EXPANDING
```

### Git

Commits produits :

```text
6a320d4 — B1+: HMM MTF regime engine + B4+: Wavelet Morlet density - dual architecture
71c2f91 — Hotfix: make B1+ HMM and B4+ Wavelet schema-flexible
```

Push final :

```text
main -> origin/main
```

---

## 7. Fichiers modifiés / ajoutés

### Moteurs

```text
Core/pf_hmm_regime_engine.py
Core/pf_wavelet_density.py
```

### Runners

```text
Core/run_hmm_regime_once.py
Core/run_wavelet_density_once.py
```

### Tests

```text
Core/test_hmm_regime.py
Core/test_wavelet_density.py
```

### Docs / patchs déjà livrés dans pack

```text
Core/INSTALL_REQUIREMENTS.txt
Core/INTEGRATION_GUIDE.md
Core/LEXIQUE_PATCH_B1HMM_B4WAVELET.md
Core/REGISTRE_BRIQUES_PATCH_B1HMM_B4WAVELET.md
Core/dashboard_surface_dual_patch.html
Core/validation_checklist.md
Core/PACK_MANIFEST.json
```

---

## 8. Doctrine PowerFlow respectée

### Respecté

```text
B1 Legacy conservé.
B1+ HMM ajouté en parallèle.
B4 Rolling conservé.
B4+ Wavelet ajouté en parallèle.
Aucune fusion.
Aucun BUY/SELL.
Aucune écriture DB depuis pf_*.
Aucun import cockpit/dashboard/telegram depuis pf_*.
M1/M5/M15 non censurés.
TF1440 non bloquant.
Risques techniques exposés.
```

### Risques techniques restants

```text
HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED
```

Impact :

```text
Le modèle utilise le fallback NumPy.
Pas de blocage runtime.
Qualité suffisante pour perception duale immédiate.
```

Amélioration future possible :

```text
Installer Python 3.12/3.13 ou Microsoft C++ Build Tools
pour permettre hmmlearn natif.
```

---

## 9. Lecture comportementale actuelle

### Régime B1+ HMM

```text
TRANSITION 0.460418
```

Interprétation PowerFlow :

```text
Le champ MTF ne donne pas encore une dominance nette.
La probabilité TRANSITION est la plus haute mais sous 0.5.
Cela expose une zone de bascule plutôt qu'un régime affirmé.
```

### Wavelet

```text
TF1  compressing
TF5  expanding
TF15 expanding
```

Lecture comportementale :

```text
Le microfilm TF1 compresse.
Les relais M5/M15 respirent plus large.
Cette divergence multi-échelle est une information de flux :
compression locale dans un champ MTF encore ouvert.
```

Pas d'arbitrage machine.

---

## 10. Commandes opérationnelles

### B1+ HMM MTF

```powershell
python run_hmm_regime_once.py --db powerflow.db --symbol GBPUSD --tfs 60,30,15 --pretty
```

### B4+ Wavelet

```powershell
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty
```

### Tests

```powershell
python test_hmm_regime.py
python test_wavelet_density.py
```

### Validation P0

```powershell
.un_p0_final_auto.ps1 -Symbol GBPUSD
```

### Dashboard hydration

```powershell
.un_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
```

---

## 11. Décision architecte

```text
PowerFlow V7.2.1 — B1+ HMM MTF + B4+ Wavelet Schema-Flex : VALIDÉ.

Le moteur ne dépend plus de TF1440 pour activer B1+.
Le moteur lit le schéma réel de force_snapshots.
B1+ et B4+ produisent leurs surfaces dashboard.
Le dual est préservé.
La DB reste read-only.
Le trader voit les deux perceptions.
La machine ne décide pas.
```

---

## 12. Prochaines actions recommandées

### Immédiat

```text
Ajouter ce rapport au Git.
Ajouter le patch lexique schema-flex au Git.
Relancer P0 final auto après commit docs.
```

### Court terme

```text
Intégrer visuellement regime_scope dans dashboard.
Afficher schema_mode et source_column en diagnostic compact.
Ajouter badge HMM_FALLBACK_NUMPY si hmmlearn absent.
```

### Moyen terme

```text
Tester B1+ HMM avec hmmlearn natif sur Python compatible.
Comparer HMM fallback vs hmmlearn sur même fenêtre.
Ajouter métrique DUAL_REGIME_DIVERGENCE entre Legacy et HMM.
```

---

*Rapport complet — PowerFlow V7.2.1 — B1+ HMM MTF + B4+ Wavelet Schema-Flex — 2026-05-11*
