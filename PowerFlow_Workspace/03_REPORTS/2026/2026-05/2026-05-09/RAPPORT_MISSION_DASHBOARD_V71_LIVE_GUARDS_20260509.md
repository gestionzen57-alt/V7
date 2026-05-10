# RAPPORT MISSION — Dashboard V7.1 Live Guard Cards

**Projet :** PowerFlow V7.1  
**Date :** 2026-05-09  
**Branche Git :** `main`  
**Commit final :** `18d0b28`  
**Message commit :** `Dashboard: add V7.1 live guard cards`  
**Statut :** ✅ Mission intégrée et poussée sur GitHub

---

## 1. Résumé exécutif

La mission consistait à ajouter au cockpit `dashboard_live.html` quatre nouvelles cards V7.1 destinées à visualiser les états runtime suivants :

1. **Data Quality**
2. **Market Validator**
3. **Entropy**
4. **Session Overlay**

L’intégration a été réalisée directement dans `dashboard_live.html`, en JavaScript vanilla, avec lecture de fichiers JSON depuis `output/` via `fetch()` et polling toutes les 30 secondes.

Deux runners compatibles dashboard ont également été ajoutés pour produire les JSON manquants côté cockpit :

- `run_entropy_engine_once.py`
- `run_session_overlay_dashboard_once.py`

La mission a été commitée et poussée sur GitHub avec succès.

---

## 2. Objectif fonctionnel

Ajouter une section dédiée dans le dashboard live permettant au trader de visualiser rapidement l’état de santé et de contexte de PowerFlow V7.1.

Ces cards ne prennent aucune décision. Elles affichent une perception technique du système :

- qualité des données ;
- validation du marché ouvert ;
- entropie / saturation des alertes ;
- contexte de session active.

Conformément à la doctrine PowerFlow :

```text
La machine perçoit.
La machine mesure.
La machine nomme.
La machine alerte.
Le trader filtre.
Le trader décide.
```

Aucune logique de trading, aucun BUY/SELL, aucune censure d’alerte, aucun filtre décisionnel n’a été ajouté.

---

## 3. Périmètre de la mission

### Inclus

- Modification de `dashboard_live.html`.
- Ajout d’une section HTML responsive contenant les 4 cards.
- Ajout du CSS dédié aux cards V7.1.
- Ajout du JS vanilla avec :
  - `fetch()` ;
  - polling toutes les 30 secondes ;
  - gestion des JSON absents ;
  - rendu dynamique des statuts ;
  - badges couleur ;
  - barres de progression pour l’entropie.
- Ajout du runner Entropy dashboard.
- Ajout d’un runner Session Overlay dashboard séparé pour ne pas écraser le runner existant.
- Validation JSON des sorties générées.
- Commit Git propre limité aux fichiers de mission.

### Exclu

- Aucune modification de `capture_bridge.py`.
- Aucune écriture dans `powerflow.db`.
- Aucune modification de `pf_temporal_node_state.py`.
- Aucune modification du runner existant `run_session_overlay_once.py` après restauration.
- Aucun commit de `output/*.json`.
- Aucun commit des fichiers hors mission : `reports/`, `run_powerflow_cycle_once.py`, `PowerFlow_Workspace/...`.

---

## 4. Fichiers modifiés ou ajoutés

### 4.1 Fichier modifié

```text
Core/dashboard_live.html
```

Rôle : interface cockpit live.

Modifications intégrées :

- CSS V7.1 entre marqueurs :

```html
<!-- PFV71_LIVE_GUARDS_STYLE_START -->
<!-- PFV71_LIVE_GUARDS_STYLE_END -->
```

- Section HTML entre marqueurs :

```html
<!-- PFV71_LIVE_GUARDS_HTML_START -->
<!-- PFV71_LIVE_GUARDS_HTML_END -->
```

- JS entre marqueurs :

```html
<!-- PFV71_LIVE_GUARDS_JS_START -->
<!-- PFV71_LIVE_GUARDS_JS_END -->
```

Ces marqueurs permettent de retrouver facilement l’intégration dans le fichier.

---

### 4.2 Fichier ajouté

```text
Core/run_entropy_engine_once.py
```

Rôle : produire `output/entropy_engine.json` pour la card Entropy.

Comportement :

- lit la queue d’alertes PowerFlow ;
- calcule un état d’entropie synthétique ;
- expose :
  - `alert_entropy_state` ;
  - `normalized_entropy` ;
  - `duplication_ratio` ;
  - `burst_score` ;
  - `alerts_count` ;
  - `technical_risks`.

Ce runner est compatible cockpit. Il ne modifie pas la DB.

---

### 4.3 Fichier ajouté

```text
Core/run_session_overlay_dashboard_once.py
```

Rôle : produire `output/session_overlay.json` pour la card Session Overlay.

Comportement :

- calcule la session FX active à partir d’un timestamp UTC ;
- expose :
  - `session` ;
  - `session_phase` ;
  - `minutes_since_open` ;
  - `session_bias` ;
  - `overlap` ;
  - `technical_risks`.

Ce fichier a été créé sous un nom séparé afin de ne pas écraser le runner existant `run_session_overlay_once.py`, qui avait une fonction différente.

---

## 5. Cards intégrées

## 5.1 Card 1 — Data Quality

**Source JSON :**

```text
output/data_quality_guard.json
```

**Affichage :**

- statut global : `OK`, `DEGRADED`, `CRITICAL` ;
- tableau par timeframe ;
- `rows_count` ;
- `last_timestamp` ;
- `is_stale` ;
- `gap_count`.

**Alerte visuelle :**

Une ligne passe en alerte visuelle si :

```text
is_stale = true
ou
gap_count > 0
```

**Couleurs :**

```text
OK        → vert
DEGRADED  → orange
CRITICAL  → rouge
No data   → gris
```

---

## 5.2 Card 2 — Market Validator

**Source JSON :**

```text
output/market_open_validator.json
```

**Affichage :**

- B4 : `PASS`, `PARTIAL`, `FAIL` ;
- B5 : `PASS`, `PARTIAL`, `FAIL` ;
- EIE : `PASS`, `PARTIAL`, `FAIL` ;
- verdict global :
  - `MARKET_OPEN_VALIDATED` ;
  - `PENDING` ;
  - `STATIC_WARNING`.

**Couleurs :**

```text
PASS       → vert
PARTIAL    → orange
FAIL       → rouge
PENDING    → orange
STATIC_WARNING → rouge
No data    → gris
```

---

## 5.3 Card 3 — Entropy

**Source JSON :**

```text
output/entropy_engine.json
```

**Affichage :**

- `alert_entropy_state` ;
- `normalized_entropy` avec barre de progression ;
- `duplication_ratio` avec barre de progression ;
- `burst_score` si présent.

**États supportés :**

```text
NORMAL_ALERT_FLOW
BURST_ACTIVE
SATURATED
SATURATED_DUPLICATE_BURST
```

**Couleurs :**

```text
NORMAL_ALERT_FLOW → vert
BURST_ACTIVE      → orange
SATURATED         → rouge
No data           → gris
```

---

## 5.4 Card 4 — Session Overlay

**Source JSON :**

```text
output/session_overlay.json
```

**Affichage :**

- `session` ;
- `session_phase` ;
- `minutes_since_open` ;
- `session_bias` ;
- `overlap`, si présent.

**Sessions supportées :**

```text
ASIAN
LONDON
NY
OVERLAP
DEAD
```

**Couleurs :**

```text
ASIAN   → bleu
LONDON  → orange
NY      → vert
OVERLAP → rouge
DEAD    → gris
```

---

## 6. Validation effectuée

### 6.1 Injection dashboard

Commande de contrôle utilisée :

```powershell
Select-String -Path .\dashboard_live.html -Pattern "data_quality_guard|market_open_validator|entropy_engine|session_overlay|DATA QUALITY|MARKET VALIDATOR|ENTROPY|SESSION OVERLAY|pfv71"
```

Résultat : les marqueurs, CSS, HTML, IDs, chemins JSON et fonctions JS ont été retrouvés dans `dashboard_live.html`.

Conclusion :

```text
Intégration dashboard confirmée ✅
```

---

### 6.2 Sources JSON

Sources vérifiées :

```text
output/data_quality_guard.json       ✅ présent
output/market_open_validator.json    ✅ présent
output/entropy_engine.json           ✅ généré
output/session_overlay.json          ✅ généré
```

Validation JSON effectuée :

```powershell
python -m json.tool .\output\entropy_engine.json > $null
python -m json.tool .\output\session_overlay.json > $null
```

Conclusion :

```text
JSON valides ✅
```

---

### 6.3 Génération Entropy

Commande utilisée :

```powershell
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty --output .\output\entropy_engine.json
```

Sortie observée :

```json
{
  "engine": "pf_entropy_engine_standalone",
  "version": "V7.1-runner-compat",
  "alert_entropy_state": "NORMAL_ALERT_FLOW",
  "normalized_entropy": 0.0,
  "duplication_ratio": 0.0,
  "burst_score": 0.0,
  "alerts_count": 0,
  "technical_risks": [
    "NO_ALERTS_IN_WINDOW"
  ],
  "symbol": "GBPUSD"
}
```

Interprétation technique :

```text
Aucune alerte dans la fenêtre observée.
État normal en contexte week-end / marché fermé.
```

---

### 6.4 Génération Session Overlay

Commande utilisée :

```powershell
python .\run_session_overlay_dashboard_once.py --timestamp now --pretty --output .\output\session_overlay.json
```

Sortie attendue / observée dans le contexte courant :

```json
{
  "engine": "pf_session_overlay_standalone",
  "version": "V7.1-runner-compat",
  "session": "DEAD",
  "session_phase": "DEAD_ZONE",
  "minutes_since_open": 37,
  "session_bias": "COMPRESSION",
  "overlap": null,
  "technical_risks": []
}
```

Interprétation technique :

```text
Session morte cohérente avec samedi soir / marché fermé.
```

---

## 7. Gestion Git

### 7.1 État avant commit

État Git observé :

```text
 M dashboard_live.html
 M run_session_overlay_once.py
?? reports/
?? run_entropy_engine_once.py
?? run_powerflow_cycle_once.py
?? run_session_overlay_dashboard_once.py
?? ../PowerFlow_Workspace/...
```

Risque détecté :

```text
run_session_overlay_once.py avait été remplacé par une version simplifiée.
```

Action corrective :

```powershell
Copy-Item .\run_session_overlay_once.py .\run_session_overlay_dashboard_once.py -Force
git restore -- .\run_session_overlay_once.py
```

Résultat :

```text
Ancien runner session restauré ✅
Version dashboard conservée sous nouveau nom ✅
```

---

### 7.2 Nettoyage avant commit

Fichiers temporaires supprimés :

```powershell
Remove-Item .\patch_dashboard_live_v71_cards.py -ErrorAction SilentlyContinue
Remove-Item .\powerflow_v71_cards.js -ErrorAction SilentlyContinue
Remove-Item .\powerflow_v71_cards_section.html -ErrorAction SilentlyContinue
Remove-Item .\docs\run_entropy_engine_once.py -ErrorAction SilentlyContinue
Remove-Item .\docs\run_session_overlay_once.py -ErrorAction SilentlyContinue
```

But : ne pas polluer Git avec des fichiers de patch temporaires.

---

### 7.3 Fichiers stagés

Commande utilisée :

```powershell
git diff --cached --name-only
```

Résultat :

```text
Core/dashboard_live.html
Core/run_entropy_engine_once.py
Core/run_session_overlay_dashboard_once.py
```

Conclusion :

```text
Seuls les fichiers de mission ont été commités ✅
```

---

### 7.4 Commit et push

Commande utilisée :

```powershell
git commit -m "Dashboard: add V7.1 live guard cards"
git push
```

Résultat :

```text
[main 18d0b28] Dashboard: add V7.1 live guard cards
3 files changed, 758 insertions(+)
create mode 100644 Core/run_entropy_engine_once.py
create mode 100644 Core/run_session_overlay_dashboard_once.py

To https://github.com/gestionzen57-alt/V7.git
c7f50b0..18d0b28 main -> main
```

Conclusion :

```text
Commit local OK ✅
Push GitHub OK ✅
```

---

## 8. Éléments volontairement non commités

Les éléments suivants sont restés hors commit :

```text
reports/
run_powerflow_cycle_once.py
../PowerFlow_Workspace/00_CURRENT/CLAUDE_md_V7.1.md
../PowerFlow_Workspace/03_REPORTS/2026/2026-05/2026-05-09/RAPPORT_FIN_SPRINT_V7.md
../PowerFlow_Workspace/04_CHECKPOINTS/2026/2026-05/2026-05-09/
```

Raison : ils ne faisaient pas partie de la mission cockpit live guard cards.

Action recommandée : traiter ces fichiers dans une mission séparée :

```text
Mission possible : nettoyage / archivage / commit documentaire V7.1
```

---

## 9. Commandes utiles après mission

### Générer Entropy

```powershell
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty --output .\output\entropy_engine.json
```

### Générer Session Overlay dashboard

```powershell
python .\run_session_overlay_dashboard_once.py --timestamp now --pretty --output .\output\session_overlay.json
```

### Vérifier les JSON

```powershell
python -m json.tool .\output\entropy_engine.json > $null
python -m json.tool .\output\session_overlay.json > $null
```

### Vérifier Git

```powershell
git status --short
```

### Voir le dernier commit

```powershell
git log --oneline -5
```

---

## 10. Risques techniques identifiés

### 10.1 Chemin JSON côté dashboard

Si une card reste sur `No data` alors que le JSON existe dans `output/`, le risque est :

```text
JSON non servi par dashboard_server
ou
chemin relatif différent entre fichier HTML et serveur Flask
```

Action : vérifier le serveur `dashboard_server.py` et la route statique pour `output/`.

---

### 10.2 Runner session existant

Risque évité : remplacement involontaire de `run_session_overlay_once.py`.

Correction appliquée :

```text
Ancien runner restauré.
Runner dashboard isolé sous run_session_overlay_dashboard_once.py.
```

---

### 10.3 Fichiers runtime

Les fichiers `output/*.json` ne doivent pas être commités.

Raison : ce sont des interfaces runtime temporaires, générées par runners.

---

### 10.4 Fichiers hors mission

Des fichiers non suivis restent présents dans le workspace.

Ils ne sont pas problématiques tant qu’ils ne sont pas ajoutés par erreur au prochain commit.

Action conseillée avant chaque commit :

```powershell
git status --short
git diff --cached --name-only
```

---

## 11. État final

```text
Dashboard cards V7.1 intégrées        ✅
CSS intégré                           ✅
HTML intégré                          ✅
JS vanilla polling 30s intégré        ✅
Gestion No data                       ✅
Data Quality source disponible        ✅
Market Validator source disponible    ✅
Entropy JSON générable                ✅
Session Overlay JSON générable        ✅
Runner session original préservé      ✅
Commit Git effectué                   ✅
Push GitHub effectué                  ✅
```

---

## 12. Prochaines actions recommandées

### P0 — Validation visuelle cockpit

Ouvrir / recharger le dashboard :

```text
Ctrl + F5
```

Vérifier visuellement :

```text
Data Quality      → badge + rows par TF
Market Validator  → B4/B5/EIE + verdict global
Entropy           → NORMAL_ALERT_FLOW + progress bars
Session Overlay   → DEAD / DEAD_ZONE actuellement
```

---

### P1 — Validation serveur

Si une card reste `No data` malgré JSON présent :

```text
vérifier dashboard_server.py
vérifier que output/ est servi correctement
vérifier l’URL réelle fetchée par le navigateur
```

---

### P2 — Intégration cycle runtime

Ajouter à terme dans le cycle PowerFlow :

```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty --output .\output\data_quality_guard.json
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty --output .\output\market_open_validator.json
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty --output .\output\entropy_engine.json
python .\run_session_overlay_dashboard_once.py --timestamp now --pretty --output .\output\session_overlay.json
```

Objectif : que les 4 JSON soient produits automatiquement avant / pendant l’ouverture du dashboard.

---

## 13. Verdict architectural

L’intégration respecte les frontières PowerFlow :

```text
capture_*  non touché
pf_*       non modifié
DB         non écrite
cockpit    enrichi en lecture JSON
trader     reste décisionnaire
```

Cette mission ajoute une couche de perception cockpit sans altérer la logique moteur.

Verdict :

```text
MISSION DASHBOARD V7.1 LIVE GUARD CARDS — VALIDÉE ✅
```

