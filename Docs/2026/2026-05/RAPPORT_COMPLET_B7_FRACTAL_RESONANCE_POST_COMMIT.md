# RAPPORT COMPLET — B7 Fractal Resonance Detection

**Projet :** PowerFlow V7.1  
**Brique :** B7 — Fractal Resonance Detection  
**Date du rapport :** 2026-05-10  
**Statut :** COMMIT LOCAL RÉUSSI — VALIDATION RUNTIME OK — AMÉLIORATION V0.2 IDENTIFIÉE  
**Commit réalisé :** `8c467c4 — B7: Fractal Resonance Detection`  
**Fichiers commités :**

```text
Core/pf_fractal_resonance.py
Core/run_fractal_resonance_once.py
```

---

## 1. Résumé exécutif

La mission B7 a été exécutée et commitée localement avec succès.

B7 ajoute à PowerFlow une mesure de synchronisation fractale entre timeframes adjacents. Elle répond à la question comportementale suivante :

```text
Est-ce que M1, M5, M15, M30 et H1 vibrent ensemble sur le même événement,
ou est-ce qu'un étage temporel est en avance / en retard / isolé ?
```

Le script PowerShell `commit_b7_fractal_resonance.ps1` a été lancé. Il a produit un JSON runtime valide, puis a créé le commit Git local :

```text
[main 8c467c4] B7: Fractal Resonance Detection
2 files changed, 704 insertions(+)
create mode 100644 Core/pf_fractal_resonance.py
create mode 100644 Core/run_fractal_resonance_once.py
```

Le moteur ne s'est pas écrasé. La DB a été lue correctement. Le résultat JSON est valide et `valid=true`.

Le snapshot réel a cependant produit un état :

```text
resonance_state = SILENT
resonance_score = 0.0
avg_signed_correlation = -0.517481
valid = true
```

Conclusion immédiate :

```text
B7 code      : OK
B7 runner    : OK
B7 commit    : OK
B7 runtime   : OK
B7 perception actuelle : SILENT
B7 amélioration logique : alignement temporel par timestamp recommandé en V0.2
```

---

## 2. Mission initiale

Objectif demandé : créer la brique **B7 — Fractal Resonance Detection** pour détecter si plusieurs timeframes vibrent ensemble.

Contrat comportemental :

```text
RESONANT  -> tous les étages temporels vibrent ensemble
LAGGED    -> tremblement en cascade, fenêtre temporelle ouverte
DISSONANT -> étage isolé ou faible synchronisation
SILENT    -> aucune vibration exploitable
```

Livrables demandés :

```text
Core/pf_fractal_resonance.py
Core/run_fractal_resonance_once.py
output/fractal_resonance.json
Git commit : "B7: Fractal Resonance Detection"
```

Les deux fichiers Core ont bien été commités. L'output JSON a été généré, mais non commité, ce qui est cohérent avec la règle PowerFlow : les fichiers `output/` sont des interfaces temporaires et ne doivent pas être versionnés par défaut.

---

## 3. Architecture respectée

### 3.1 Couche moteur

```text
Core/pf_fractal_resonance.py
```

Rôle : moteur pur de calcul fractal resonance.

Respect architectural :

```text
OK  aucun import cockpit_*
OK  aucun import dashboard_*
OK  aucun import telegram_*
OK  aucune écriture DB
OK  aucun BUY/SELL
OK  aucune décision de trade
OK  uniquement perception / mesure / qualification
```

### 3.2 Couche runner

```text
Core/run_fractal_resonance_once.py
```

Rôle : exécution CLI one-shot.

Respect architectural :

```text
OK  lecture SQLite read-only
OK  sortie JSON dans output/fractal_resonance.json
OK  arguments CLI : --db, --symbol, --tfs, --pretty, --output
OK  pas de dépendance cockpit
OK  pas d'écriture dans powerflow.db
```

### 3.3 Position dans PowerFlow

B7 s'insère naturellement après B3/B4 et avant le mapper ou le cockpit :

```text
force_snapshots DB
    ↓ read-only
B3 kinematics / force rolling disponible
    ↓
B7 fractal resonance
    ↓
output/fractal_resonance.json
    ↓ futur
behavioral_alert_mapper / cockpit cards / dashboard
```

B7 ne remplace pas B3 ni B4. Elle ajoute une dimension : la **synchronisation temporelle multi-TF**.

---

## 4. Fonctionnalités livrées

### 4.1 États produits

```text
RESONANT
LAGGED
DISSONANT
SILENT
```

### 4.2 Score global

```text
resonance_score : 0.0 à 1.0
```

Ce score représente la moyenne des corrélations positives exploitables entre paires adjacentes.

Important : une corrélation fortement négative ne renforce pas le `resonance_score`. Elle indique une opposition fractale ou une désynchronisation, pas une vibration commune.

### 4.3 Moyenne signée

```text
avg_signed_correlation : -1.0 à +1.0
```

Cette valeur garde l'information de polarité. Elle permet de distinguer :

```text
+0.85 -> résonance directionnelle commune
-0.85 -> opposition fractale forte
 0.00 -> champ non structuré / neutralisé
```

### 4.4 Corrélations par paire

Paires critiques traitées :

```text
(1, 5)
(5, 15)
(15, 30)
(30, 60)
(60, 240) si disponible
```

### 4.5 Lag detection

Le moteur scanne les décalages de `-max_lag` à `+max_lag`.

Convention :

```text
lag > 0 : le second timeframe traîne le premier
lag = 0 : synchronisation directe
lag < 0 : le second timeframe semble en avance
```

### 4.6 Risques techniques

Le module produit des risques techniques, sans jugement de marché :

```text
INSUFFICIENT_DATA
FLAT_SERIES
CORRELATION_UNSTABLE
LAGGED_MULTIPLE_TF
SILENT_HTF
```

Dans le run réel, les risques sortis sont :

```text
SILENT_HTF
LAGGED_MULTIPLE_TF
```

---

## 5. Résultat réel du run utilisateur

Commande lancée :

```powershell
.\commit_b7_fractal_resonance.ps1
```

Le runner a produit :

```json
{
  "timestamp": "2026-05-10T00:49:15Z",
  "symbol": "GBPUSD",
  "resonance_state": "SILENT",
  "resonance_score": 0.0,
  "avg_signed_correlation": -0.517481,
  "resonant_tfs": [],
  "lagged_tfs": [],
  "dissonant_tfs": [1, 5, 15, 30, 60],
  "pair_correlations": {
    "(1, 5)": -0.278398,
    "(5, 15)": -0.869968,
    "(15, 30)": -0.744471,
    "(30, 60)": -0.177088
  },
  "pair_states": {
    "(1, 5)": "SILENT",
    "(5, 15)": "SILENT",
    "(15, 30)": "SILENT",
    "(30, 60)": "SILENT"
  },
  "lag_detection": {
    "(1, 5)": 7,
    "(5, 15)": -3,
    "(15, 30)": -2,
    "(30, 60)": -3
  },
  "expected_amplification": false,
  "technical_risks": [
    "SILENT_HTF",
    "LAGGED_MULTIPLE_TF"
  ],
  "method": "cross_correlation_multi_tf",
  "valid": true,
  "source": {
    "db_path": "Core\\powerflow.db",
    "table": "force_snapshots",
    "force_column": "force_gbp",
    "requested_tfs": [1, 5, 15, 30, 60]
  }
}
```

---

## 6. Lecture comportementale du résultat

### 6.1 Résultat global

```text
SILENT
```

Cela signifie : aucune vibration fractale positive exploitable au moment exact du snapshot.

Ce n'est pas un échec runtime. C'est une perception : les étages temporels ne sont pas synchronisés positivement.

### 6.2 Paires observées

```text
M1 ↔ M5   : -0.278398  -> faible opposition / pas de résonance
M5 ↔ M15  : -0.869968  -> opposition fractale forte
M15 ↔ M30 : -0.744471  -> opposition fractale forte
M30 ↔ H1  : -0.177088  -> faible opposition / pas de résonance
```

### 6.3 Ce que PowerFlow voit

```text
M1/M5/M15/M30/H1 ne vibrent pas ensemble.
Le champ fractal est opposé ou désynchronisé.
Pas d'amplification positive attendue selon B7.
```

Traduction organique :

```text
Les étages ne tremblent pas ensemble.
Certains étages répondent même à contre-phase.
```

---

## 7. Diagnostic technique important

Le run réel révèle une limite analytique de la V0.1 : **la comparaison par nombre de barres n'est pas équivalente à une comparaison par fenêtre temporelle réelle**.

Actuellement, B7 compare les 50 dernières barres de chaque TF :

```text
TF1  : 50 barres = 50 minutes
TF5  : 50 barres = 250 minutes
TF15 : 50 barres = 750 minutes
TF30 : 50 barres = 1500 minutes
TF60 : 50 barres = 3000 minutes
```

Donc le moteur compare des fragments temporels de durées différentes.

Pour une vraie résonance fractale, la comparaison devrait idéalement aligner les séries par **timestamp** sur une même fenêtre horloge, par exemple :

```text
Fenêtre horloge : dernières 180 minutes
TF1  : jusqu'à 180 points
TF5  : jusqu'à 36 points
TF15 : jusqu'à 12 points
TF30 : jusqu'à 6 points
TF60 : jusqu'à 3 points
```

Puis il faudrait resampler / interpoler / agréger sur une grille commune avant corrélation.

### Conclusion technique

```text
B7 V0.1 = fonctionnelle, légère, exploitable comme première perception.
B7 V0.2 = nécessaire pour timestamp-aligned resonance.
```

Ce n'est pas une urgence de crash. C'est une amélioration de justesse comportementale.

---

## 8. Git — état après commit

### 8.1 Commit B7 réussi

```text
[main 8c467c4] B7: Fractal Resonance Detection
```

### 8.2 Branche locale

Git indique :

```text
Your branch is ahead of 'origin/main' by 1 commit.
```

Donc le commit est local, pas encore poussé sur GitHub.

Commande pour publier uniquement ce commit :

```powershell
git push
```

### 8.3 Warnings LF/CRLF

Git a affiché :

```text
LF will be replaced by CRLF the next time Git touches it
```

Ce n'est pas bloquant. C'est un avertissement de fin de ligne Windows. Le commit est passé.

### 8.4 Avertissement PowerShell

PowerShell a affiché un avertissement de sécurité avant exécution du script téléchargé.

Commande possible si tu veux éviter ce prompt à l'avenir sur ce fichier :

```powershell
Unblock-File .\commit_b7_fractal_resonance.ps1
```

### 8.5 Fichiers locaux non liés à B7

Git montre encore :

```text
deleted: anciens fichiers CLAUDE/GUIDE/RAPPORT
untracked: rapports, patches, HMM, outputs, scripts ps1, workspace docs...
```

Ces éléments ne sont pas dans le commit B7. Ne pas faire `git add .` maintenant.

Commande à éviter :

```powershell
git add .
```

Commande propre si seul B7 doit être publié :

```powershell
git push
```

Le cleanup Git doit être traité dans une mission séparée.

---

## 9. Validation effectuée par le script

Le script a bien exécuté :

```text
1. Compilation Python
2. Run B7 sur Core\powerflow.db
3. Écriture output/fractal_resonance.json
4. Git add ciblé sur les 2 fichiers Core
5. Git commit ciblé
6. Git status final
```

Validation observable :

```text
OK  module exécuté
OK  JSON produit
OK  valid=true
OK  commit créé
OK  seuls les fichiers Core B7 ont été commités
```

---

## 10. Interprétation PowerFlow du `SILENT`

`SILENT` ne veut pas dire que le marché est mort.

Dans B7, `SILENT` signifie :

```text
La vibration fractale positive multi-TF n'est pas lisible sur la fenêtre actuelle.
```

Avec `avg_signed_correlation = -0.517481`, la lecture est plus précise :

```text
Le champ n'est pas neutre.
Il est plutôt en contre-phase entre plusieurs étages.
```

Le bon terme de future V0.2 pourrait être :

```text
INVERSE_RESONANCE
```

Mais pour la V0.1, le contrat initial ne prévoyait que :

```text
RESONANT / LAGGED / DISSONANT / SILENT
```

La classification actuelle reste donc conforme au contrat.

---

## 11. Recommandation V0.2

### 11.1 Objectif

Créer une version `timestamp_aligned` sans alourdir le moteur.

Objectif : comparer les TF sur la même fenêtre horloge.

### 11.2 Nouveau paramètre proposé

```text
--clock-window-minutes 180
```

### 11.3 Méthode proposée

```text
1. Charger les snapshots depuis now - clock_window_minutes pour chaque TF
2. Convertir timestamp en index temporel
3. Resampler/interpoler chaque série sur grille commune
4. Corréler les séries alignées
5. Garder la classification actuelle
```

### 11.4 États additionnels possibles

Sans casser le contrat JSON existant, ajouter :

```json
{
  "alignment_mode": "bar_tail | timestamp_aligned",
  "clock_window_minutes": 180,
  "bar_window_mismatch": true
}
```

### 11.5 Risque technique ajouté

```text
TEMPORAL_WINDOW_MISMATCH
```

Définition : les timeframes ont été comparés sur un nombre égal de barres, mais ces barres couvrent des durées réelles différentes.

---

## 12. Commandes opérationnelles immédiates

### 12.1 Publier B7

```powershell
git push
```

### 12.2 Vérifier après push

```powershell
git status
```

Attendu : la branche ne doit plus être ahead de 1 commit. Les fichiers non suivis ou supprimés peuvent rester visibles, car ils sont hors mission B7.

### 12.3 Relancer B7 manuellement

```powershell
python Core\run_fractal_resonance_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --pretty
```

### 12.4 Valider JSON

```powershell
python -m json.tool .\output\fractal_resonance.json | Out-Null
```

---

## 13. Ne pas mélanger les missions

B7 est commitée.

Les éléments suivants sont hors scope B7 et doivent être traités séparément :

```text
anciens fichiers CLAUDE supprimés
rapports Markdown non suivis
HMM files
outputs JSON
PowerFlow_Workspace docs
scripts commit_*.ps1
README weekend/HMM
requirements_hmm.txt
```

Règle recommandée :

```text
1 mission = 1 commit
```

Donc :

```text
Commit B7       : déjà fait
Cleanup Git     : mission séparée
Docs / rapports : mission séparée
HMM             : mission séparée
```

---

## 14. Checkpoint final B7

```text
Date                  : 2026-05-10
Brique                : B7 Fractal Resonance Detection
Commit local          : 8c467c4
Commit message        : B7: Fractal Resonance Detection
Fichiers Core         : pf_fractal_resonance.py, run_fractal_resonance_once.py
Runner                : OK
DB read-only          : OK
JSON output           : OK
valid                 : true
Runtime state         : SILENT
Resonance score       : 0.0
Avg signed corr       : -0.517481
Technical risks       : SILENT_HTF, LAGGED_MULTIPLE_TF
Push remote           : à faire
V0.2 recommandée      : timestamp-aligned resonance
```

---

## 15. Phrase PowerFlow

```text
La machine ne prédit pas.
Elle mesure si les étages temporels vibrent ensemble.

Ici, ils ne vibrent pas ensemble.
Ils sont désynchronisés, parfois en contre-phase.

B7 voit cela.
Le trader filtre.
Le trader décide.
```
