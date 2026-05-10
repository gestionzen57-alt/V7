# PATCH LEXIQUE — Memory Engine V1 / B6
**Projet : PowerFlow V7.1**  
**Date : 2026-05-10**  
**Commit associé : `dc0eee1` — `Memory: V1 pattern indexing engine`**  
**Fichier cible : `LEXIQUE_GRAMMAIRE_V7.1.md`**

---

## Instruction d'intégration

Ajouter ce bloc à la fin de `LEXIQUE_GRAMMAIRE_V7.1.md`, après la section :

```text
## 18. REPLAY ENGINE ET FILM HISTORIQUE (V7.1)
```

Nouvelle section proposée :

```text
## 19. MEMORY ENGINE ET MÉMOIRE COMPORTEMENTALE (V7.1 / B6)
```

---

## Bloc à ajouter

```markdown
---

## 19. MEMORY ENGINE ET MÉMOIRE COMPORTEMENTALE (V7.1 / B6)

### MEMORY_ENGINE_V1
Module (`pf_memory_engine.py`) de mémoire comportementale PowerFlow.
Il lit `behavioral_alert_queue.json`, transforme chaque alerte en signature comportementale, indexe les occurrences historiques, puis retourne un contexte de fréquence : occurrences, outcomes, distribution et durée médiane.

Il ne prédit pas.
Il ne conseille pas.
Il ne filtre pas.
Il expose la mémoire du flux.

### B6_MEMORY_ENGINE
Nom de brique pour la première mémoire comportementale de PowerFlow.
B6 complète B1/B2/B3/B4/B5 en ajoutant une dimension passée : non pas "que se passe-t-il maintenant ?", mais "quand cette signature s'est déjà produite, qu'a enregistré la machine ensuite ?".

### BEHAVIORAL_PATTERN
Signature comportementale extraite d'une alerte.
Elle condense l'événement en dimensions stables permettant de retrouver les occurrences passées.
Un pattern n'est pas une figure chartiste. C'est une empreinte de flux.

### PATTERN_TUPLE_6D
Tuple comportemental à 6 dimensions utilisé par Memory V1 :

```python
(
    alert_type,
    regime,
    session,
    eie_state,
    b4_state,
    b5_direction,
)
```

Dimensions :
- `alert_type` : type d'alerte (`FIRST_DETACHMENT_MICRO`, `EIE_LEADER_CONFIRMED`, etc.)
- `regime` : contexte B1 (`COMPRESSION`, `TENDANCE`, `RANGE`, `TRANSITION`)
- `session` : contexte sessionnel (`ASIAN`, `LONDON`, `NY`, `OVERLAP`)
- `eie_state` : état élastique (`ELASTIC_IN_EXTREME`, `NEUTRAL`, `LEAKING`, etc.)
- `b4_state` : état de densité temporelle (`CYCLE_COMPRESSING`, `CYCLE_EXPANDING`, etc.)
- `b5_direction` : direction relationnelle Spearman (`SYNCHRO`, `DIVERGENT`, `NEUTRAL`)

### PATTERN_HASH_64
Identifiant déterministe 64-bit du `PATTERN_TUPLE_6D`.
Memory V1 utilise un hash stable basé sur `hashlib.blake2b`, et non le `hash()` natif Python, car le `hash()` Python peut changer entre processus.

Règle :

```text
Même pattern comportemental = même pattern_hash entre deux exécutions.
```

### DETERMINISTIC_PATTERN_HASH
Propriété technique garantissant que deux alertes ayant les mêmes 6 dimensions produisent toujours le même `pattern_hash`.
Indispensable pour que la mémoire soit fiable entre deux runs, deux sessions ou deux jours.

### MEMORY_INDEX
Index interne du Memory Engine :

```text
pattern_hash -> liste des alertes historiques correspondantes
```

Il permet de retrouver toutes les occurrences passées d'un même comportement.

### MEMORY_QUERY
Interrogation de la mémoire pour une alerte donnée.
Elle répond à :

```text
Combien de fois ce pattern s'est-il déjà produit ?
Quels outcomes ont été enregistrés ensuite ?
Quelle durée médiane en bars a été observée ?
Quels risques techniques limitent la lecture ?
```

### HISTORICAL_CONTEXT
Bloc JSON produit par Memory V1 pour enrichir une alerte avec sa mémoire historique.

Exemple :

```json
{
  "occurrences": 7,
  "outcomes": [
    {
      "outcome": "RELEASE_CONFIRMED",
      "count": 5,
      "median_bars_to_move": 14
    },
    {
      "outcome": "REJECTION",
      "count": 2,
      "median_bars_to_move": 8
    }
  ],
  "outcome_distribution": {
    "RELEASE_CONFIRMED": 0.7143,
    "REJECTION": 0.2857
  },
  "sample_size": 7,
  "median_bars_to_move": 13
}
```

### MEMORY_OCCURRENCE
Une alerte historique partageant le même `pattern_hash` que l'alerte interrogée.
Le nombre d'occurrences mesure la profondeur de mémoire disponible pour cette signature.

### OUTCOME
Ce que la machine a enregistré après une alerte historique.
Exemples :

```text
RELEASE_CONFIRMED
REJECTION
UNKNOWN
```

Un outcome absent reste valide : il devient `UNKNOWN`.
Cela permet d'utiliser la mémoire même si toute la chaîne d'annotation post-événement n'est pas encore complète.

### OUTCOME_DISTRIBUTION
Distribution fréquentielle des outcomes historiques pour un pattern donné.
Elle se lit comme une fréquence observée, jamais comme une probabilité de succès.

Exemple :

```json
{
  "RELEASE_CONFIRMED": 0.7143,
  "REJECTION": 0.2857
}
```

Lecture PowerFlow :

```text
Ce pattern a été observé 7 fois : 5 release, 2 rejection.
```

Interdiction de lecture :

```text
Ce pattern a 71% de chance de réussir.
```

### MEDIAN_BARS_TO_MOVE
Durée médiane observée, en nombre de bars, entre l'alerte et l'outcome enregistré.
Ce n'est pas une cible temporelle. C'est une mémoire de durée typique observée.

### SAMPLE_SIZE
Nombre d'occurrences utilisées pour construire le contexte historique.
Un `sample_size` faible rend la lecture fragile et déclenche `SMALL_SAMPLE_SIZE`.

### MEMORY_QUERY_RESULT
Bloc complet retourné par `query_pattern(alert)`.
Contient :

```text
pattern
pattern_hash
timestamp
historical_context
technical_risks
```

### NO_ALERTS_IN_QUEUE
Risque technique émis quand la queue existe mais ne contient aucune alerte.
Cas normal pendant un week-end, avant daemon, ou si aucun événement n'a été produit.

Ce n'est pas une erreur moteur.
C'est une absence de matière à indexer.

### NO_HISTORICAL_DATA
Risque technique émis quand aucune occurrence historique n'existe pour un pattern donné.
Le pattern est nouveau, absent de l'historique, ou la queue ne couvre pas encore assez de sessions.

### SMALL_SAMPLE_SIZE
Risque technique émis quand le nombre d'occurrences est inférieur à 5.
La mémoire existe, mais elle est statistiquement mince.
La fréquence est affichée, mais qualifiée comme fragile.

### INCOMPLETE_HISTORY
Risque technique indiquant que l'historique disponible ne couvre pas suffisamment la profondeur attendue.
Peut apparaître si les données sont trop anciennes, trop courtes, ou si la queue n'a pas encore accumulé assez de sessions.

### SELF_TEST_SAMPLE_NOT_LIVE_MARKET
Risque technique émis lorsque `run_memory_query_once.py` est lancé avec `--self-test`.
Indique que les résultats proviennent d'une queue synthétique de validation et non du marché live.

### WEEKEND_SELF_TEST_MODE
Mode de validation hors marché ouvert.
Il génère une queue de test contrôlée pour valider : chargement JSON, index, hash déterministe, occurrences, outcomes, médianes, risques techniques et sortie JSON.

Commande :

```powershell
python run_memory_query_once.py --self-test --pretty
```

### MEMORY_QUEUE_PATH_RESOLUTION
Mécanisme de résolution de chemin permettant au runner de fonctionner depuis `Core/` ou depuis la racine du projet.
Si la queue live n'est pas détectée automatiquement, le chemin peut être forcé :

```powershell
python run_memory_query_once.py --queue "..\output\behavioral_alert_queue.json" --pretty
```

### MEMORY_OUTPUT_JSON
Fichier produit par le runner Memory :

```text
output/memory_query_results.json
```

Il contient les résultats de mémoire des dernières alertes interrogées.
Le cockpit ou dashboard peut le lire sans importer le moteur.

### MEMORY_CONTEXT_NOT_PREDICTION
Règle doctrinale de Memory V1.
Le contexte historique n'est jamais une prédiction.
Une fréquence passée ne devient jamais un ordre, un conseil ou une certitude.

Formulation correcte :

```text
Ce pattern s'est produit 7 fois : 5 RELEASE_CONFIRMED, 2 REJECTION.
```

Formulation interdite :

```text
Ce pattern va release.
```

### MEMORY_ENGINE_TECHNICAL_RISKS
Famille de risques techniques spécifiques à la mémoire :

```text
NO_ALERTS_IN_QUEUE
NO_HISTORICAL_DATA
SMALL_SAMPLE_SIZE
INCOMPLETE_HISTORY
SELF_TEST_SAMPLE_NOT_LIVE_MARKET
```

Ils qualifient la lisibilité de la mémoire.
Ils ne censurent pas l'alerte.
Ils ne jugent pas le trade.
```

---

## Patch checkpoint docs

Ajouter aussi dans `CLAUDE.md` ou document de checkpoint :

```markdown
2026-05-10 — Mission 3 Memory Engine V1 ✅
Core/pf_memory_engine.py créé
Core/run_memory_query_once.py créé
Pattern hash déterministe 64-bit
Index behavioral_alert_queue par 6 dimensions
Outcomes + distribution + median_bars_to_move
Risques techniques : NO_ALERTS_IN_QUEUE / SMALL_SAMPLE_SIZE / NO_HISTORICAL_DATA / SELF_TEST_SAMPLE_NOT_LIVE_MARKET
Mode self-test week-end validé
JSON valide
Git : dc0eee1 — Memory: V1 pattern indexing engine
Remote : main poussé sur GitHub
```

---

## Commit conseillé pour ce patch documentaire

```powershell
git add RAPPORT_MEMORY_ENGINE_V1_20260510.md PATCH_LEXIQUE_MEMORY_ENGINE_V1.md
git commit -m "Docs: Memory V1 report and lexique patch"
git push
```
