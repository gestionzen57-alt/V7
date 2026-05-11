# LEXIQUE PATCH — PowerFlow V7.2.1 B1+ HMM MTF + Schema-Flex

**Date :** 2026-05-11  
**Version cible :** V7.2.1  
**Objet :** Termes nouveaux à intégrer dans `LEXIQUE_GRAMMAIRE_V72.md`  
**Contexte :** B1+ HMM MTF, B4+ Wavelet, introspection DB schema-flex  

---

## 1. REGIME_HMM_MTF

Régime détecté par B1+ HMM sur stack multi-timeframe tactique.

Contrairement à une lecture Daily-only, `REGIME_HMM_MTF` utilise H1 / M30 / M15 comme base de perception active. H4 / D enrichissent le contexte s'ils existent, mais ne bloquent pas l'activation.

Usage :

```json
{
  "regime_hmm": "TRANSITION",
  "mtf_timeframes": [60, 30, 15],
  "context_timeframes": [240, 1440]
}
```

---

## 2. MTF_OBSERVATION_WINDOW

Fenêtre d'observations agrégées sur plusieurs timeframes.

Remplace la logique trop rigide :

```text
TF1440 >= 50 rows
```

par :

```text
observations agrégées H1/M30/M15 >= 50
```

But : permettre au moteur de percevoir le régime tactique sans attendre la densité Daily.

---

## 3. MULTI_TF_TACTICAL

Scope de régime indiquant que B1+ HMM est actif sur le stack tactique MTF uniquement.

Timeframes typiques :

```text
H1  = 60
M30 = 30
M15 = 15
```

Signification :

```text
Le régime est lisible tactiquement.
Le contexte H4/D n'est pas indispensable à l'activation.
```

---

## 4. HTF_ENRICHED

Scope de régime indiquant que B1+ HMM a utilisé H1/M30/M15 pour respirer, et H4/D comme contexte additionnel.

Usage :

```json
{
  "regime_scope": "HTF_ENRICHED",
  "mtf_timeframes": [60, 30, 15],
  "context_timeframes": [240, 1440]
}
```

Important :

```text
HTF_ENRICHED ne veut pas dire HTF_REQUIRED.
H4/D enrichissent. Ils ne bloquent pas.
```

---

## 5. HMM_GAUSSIAN_FALLBACK_NUMPY

Méthode HMM fallback utilisée quand `hmmlearn` n'est pas disponible.

Contexte :

```text
Python 3.14 peut ne pas avoir de wheel hmmlearn.
Le build peut échouer sans Microsoft C++ Build Tools.
```

PowerFlow ne bloque pas : il utilise une approximation gaussienne NumPy pour maintenir B1+ actif.

Risque technique exposé :

```text
HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED
```

---

## 6. HMMLEARN_OPTIONAL

Règle d'intégration indiquant que `hmmlearn` améliore B1+ HMM mais ne conditionne pas son activation.

Comportement :

```text
hmmlearn disponible  -> GaussianHMM natif
hmmlearn absent      -> fallback NumPy
```

Doctrine :

```text
Pas de panne dure si la dépendance C++ n'est pas installable.
Le moteur qualifie techniquement et continue.
```

---

## 7. SCHEMA_FLEX

Capacité d'un moteur PowerFlow à introspecter la table `force_snapshots` pour trouver le schéma réel au lieu d'imposer des noms de colonnes fixes.

Modes supportés :

```text
wide_currency
long_currency
generic_numeric
```

But :

```text
Réduire le risque de schema drift.
Éviter les crashs no such column.
Maintenir la perception sur DB réelle.
```

---

## 8. WIDE_CURRENCY_SCHEMA

Schéma où chaque devise est une colonne numérique distincte.

Exemples acceptés :

```text
gbp, usd, eur, jpy
force_gbp, force_usd, force_eur, force_jpy
GBP, USD, EUR, JPY
```

Sortie observée :

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

---

## 9. LONG_CURRENCY_SCHEMA

Schéma où la devise et sa force sont stockées en lignes plutôt qu'en colonnes.

Exemple logique :

```text
timestamp | symbol | timeframe | currency | value
```

PowerFlow peut reconstruire une matrice devise/temps depuis ce format.

Usage :

```text
Fallback schema-flex si les colonnes devise wide ne sont pas présentes.
```

---

## 10. GENERIC_NUMERIC_SCHEMA

Mode de dernier recours quand aucune colonne devise explicite n'est détectée mais qu'une ou plusieurs colonnes numériques exploitables existent.

Usage :

```text
Permet une perception minimale du flux numérique.
Expose un risque technique de sémantique colonne moins claire.
```

Risque technique possible :

```text
GENERIC_NUMERIC_SCHEMA_USED
```

---

## 11. TIME_COLUMN_DETECTION

Détection automatique de la colonne temporelle dans la DB.

Ordre typique :

```text
timestamp
created_at
time
ts
datetime
date
rowid
```

Sortie observée :

```json
{
  "time_column": "created_at"
}
```

But :

```text
Éviter no such column: timestamp.
```

---

## 12. TIMEFRAME_COLUMN_DETECTION

Détection automatique de la colonne timeframe.

Noms acceptés :

```text
timeframe
tf
period
frame
```

Sortie observée :

```json
{
  "timeframe_column": "timeframe"
}
```

---

## 13. SYMBOL_COLUMN_DETECTION

Détection automatique de la colonne symbole.

Noms acceptés :

```text
symbol
pair
instrument
market
```

Sortie observée :

```json
{
  "symbol_column": "symbol"
}
```

---

## 14. FORCE_COLUMN_DETECTION

Détection automatique de la colonne de force pour une devise.

Exemples pour GBP :

```text
gbp
GBP
force_gbp
gbp_force
```

Sortie observée pour B4+ Wavelet :

```json
{
  "source_column": "force_gbp"
}
```

---

## 15. WAVELET_SCHEMA_FLEX

Adaptation de B4+ Wavelet au schéma réel de `force_snapshots`.

Le moteur détecte automatiquement la colonne source du signal, puis applique CWT Morlet sur la série.

Champs associés :

```json
{
  "schema_mode": "wide_currency",
  "source_column": "force_gbp",
  "method": "CWT_MORLET"
}
```

---

## 16. CWT_MORLET_SCHEMA_FLEX

Version schema-flex de la transformée ondelette continue Morlet.

Même logique comportementale que B4+ Wavelet, mais sans dépendre d'un nom de colonne fixe.

Usage :

```text
Détecter les cycles non-stationnaires sur la série force détectée.
```

---

## 17. HMM_MTF_ROWS_USED

Nombre total d'observations utilisées par B1+ HMM sur le stack multi-timeframe.

Exemple validé :

```json
{
  "rows_used": 973
}
```

Interprétation :

```text
Le moteur dispose d'une densité suffisante sur H1/M30/M15.
```

---

## 18. B1_HMM_SCHEMA_MODE

Champ diagnostic indiquant comment B1+ HMM a lu la DB.

Valeurs possibles :

```text
wide_currency
long_currency
generic_numeric
```

Usage dashboard :

```text
Afficher en diagnostic compact pour détecter les schema drifts.
```

---

## 19. B4_WAVELET_SOURCE_COLUMN

Colonne numérique utilisée par B4+ Wavelet comme signal.

Exemple :

```json
{
  "source_column": "force_gbp"
}
```

But :

```text
Tracer exactement quelle force alimente la perception wavelet.
```

---

## 20. HMM_FALLBACK_TECHNICAL_RISK

Risque technique exposé lorsque B1+ HMM utilise le fallback NumPy.

Libellé :

```text
HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED
```

Ce n'est pas une panne.
C'est une qualification de méthode.

---

## 21. DB_SCHEMA_DRIFT_GUARD

Principe de robustesse consistant à prévenir les erreurs runtime dues à un décalage entre le schéma attendu et le schéma réel.

Exemples d'erreurs évitées :

```text
no such column: timestamp
not enough currency columns
```

Méthode :

```text
PRAGMA table_info(force_snapshots)
détection colonnes
fallback contrôlé
technical_risks visibles
```

---

## 22. DUAL_REGIME_SCHEMA_FLEX

Extension de la dual perception B1/B1+ dans laquelle B1+ peut lire plusieurs formes de schéma DB sans compromettre la séparation avec B1 Legacy.

Règle :

```text
B1 Legacy reste indépendant.
B1+ HMM lit schema-flex.
Aucune fusion.
Trader arbitre.
```

---

## 23. DUAL_DENSITY_SCHEMA_FLEX

Extension de la dual perception B4/B4+ dans laquelle B4+ peut lire plusieurs formes de schéma DB sans compromettre la séparation avec B4 Rolling.

Règle :

```text
B4 Rolling reste indépendant.
B4+ Wavelet lit schema-flex.
Aucune fusion.
Trader arbitre.
```

---

## 24. LAG1_COMPRESSION_CONTEXT

Contexte où une période dominante de 1 barre n'est pas automatiquement considérée comme statique.

Nouvelle sémantique :

```text
dominant_period_bars = 1 + variance vivante + uniqueness réelle
-> LAG1_COMPRESSION
```

Au lieu de :

```text
dominant_period_bars = 1
-> STATIC_SIGNATURE
```

But :

```text
Ne pas bloquer les compressions rapides vivantes.
```

---

## 25. REGIME_TRANSITION_LOW_DOMINANCE

Situation où B1+ HMM donne `TRANSITION` comme état dominant mais avec une confiance inférieure à 0.5.

Exemple :

```json
{
  "regime_hmm": "TRANSITION",
  "regime_confidence_hmm": 0.460418
}
```

Lecture PowerFlow :

```text
Zone de bascule.
Aucun régime fortement dominant.
Information à exposer, pas à masquer.
```

---

## 26. MULTI_SCALE_WAVELET_FIELD

Champ wavelet où plusieurs bandes d'échelles sont actives simultanément.

État associé :

```text
WAVELET_MULTI_SCALE
```

Exemple validé :

```text
TF1 / TF5 / TF15 = WAVELET_MULTI_SCALE
```

Lecture PowerFlow :

```text
Plusieurs cycles coexistent.
Le flux est multi-échelle.
```

---

## 27. WAVELET_SCALE_DRIFT_DIRECTION

Direction du déplacement de l'échelle dominante dans le temps.

Valeurs :

```text
COMPRESSING
EXPANDING
STABLE
```

Exemple :

```json
{
  "scale_drift_direction": "COMPRESSING"
}
```

Usage :

```text
Voir si le cycle raccourcit, s'allonge ou reste stable.
```

---

## 28. DASHBOARD_SCHEMA_DIAGNOSTIC

Affichage compact recommandé dans le dashboard pour exposer le mode de lecture DB.

Champs :

```text
schema_mode
time_column
source_column
regime_scope
method
technical_risks
```

But :

```text
Traçabilité.
Debug rapide.
Pas de boîte noire.
```

---

## 29. NO_TF1440_BLOCKER

Règle V7.2.1 : TF1440 ne bloque pas l'activation de B1+ HMM.

Formulation :

```text
Daily enrichit la gravité supérieure.
Daily ne censure pas la perception MTF.
```

Usage :

```text
B1+ active dès que H1/M30/M15 ont assez de matière.
```

---

## 30. SCHEMA_FLEX_VALIDATION_PASS

État de validation indiquant que les moteurs B1+ HMM et B4+ Wavelet ont lu la DB réelle, produit leurs JSON, et passé les tests.

Sortie cible :

```text
B1+ HMM schema-flex once PASS
B4+ Wavelet schema-flex once PASS
dashboard surface outputs PASS
git push PASS
FINAL: PASS
```

---

*Lexique patch — PowerFlow V7.2.1 — B1+ HMM MTF Schema-Flex — 2026-05-11*
