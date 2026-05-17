# Contrat B9 ↔ Temporalité — PowerFlow

**Version :** V3.1 documentaire  
**Branche cible :** `docs/b9-temporality-contract`  
**Statut :** contrat read-only, testable par documentation  
**Portée :** B9 Sequence Summarizer → brique Temporalité  
**Commit proposé :** `docs(t009): add B9 temporality contract`

---

## 0. Phrase de cap

```text
B9 dit ce qui s’imprime dans la scène.
La Temporalité dit si cette scène est jeune, active, tardive ou consommée.
```

Ce contrat empêche deux dérives :

1. **B9 ne devient pas un moteur temporel.**  
   B9 reste la trace locale : effort, résultat, progrès, zone mémoire, retest, source.

2. **Temporalité ne répète pas B9.**  
   Temporalité reçoit les preuves B9 et qualifie la maturité de la fenêtre : naissance, activité, retard, fermeture, respiration, absorption, second leg ou exhaustion.

---

## 1. Responsabilités séparées

### 1.1 B9 — trace locale imprimée dans le prix

B9 fournit des preuves locales, reconstruites ou raw selon la source :

```text
moment_type
parent_scene
zone_memory
effort_role
retest_status
memory_state
source_profile
proxy_vs_raw_verdict
raw_coverage
center_path
time_start
time_end
limits
```

B9 répond à la question :

```text
Qu’est-ce que le flux local imprime dans le prix ?
```

Exemples de lectures B9 autorisées :

```text
centre qui migre par paliers
palier d’absorption actif
projection en perte d’efficacité
retest échoué
mémoire basse active
lecture reconstruite M1_BAR_PROXY
raw indisponible
```

B9 ne décide pas :

```text
pas d’ordre d’achat
pas d’ordre de vente
pas d’entrée
pas de target
pas de stop
pas de stratégie automatique
pas de fenêtre temporelle finale
```

### 1.2 Temporalité — maturité, phase et rôle temporel

Temporalité reçoit les preuves B9 et répond à la question :

```text
Cette scène est-elle jeune, active, tardive, fermée, en respiration, en absorption ou en second leg ?
```

Temporalité produit une qualification temporelle, pas une relecture de la scène locale.

Temporalité ne modifie pas :

```text
moment_type
zone_memory
parent_scene
source_profile
proxy_vs_raw_verdict
raw_coverage
```

Temporalité ne remplace jamais B9. Elle ajoute une couche de maturité.

---

## 2. Payload d’entrée minimal B9

```json
{
  "brique": "B9",
  "symbol": "GBPUSD",
  "scene_id": "B9S_GBPUSD_20260515_LONDON_001",
  "moment_id": "B9M_20260515_1100_001",
  "moment_type": "T009_MOMENT_CENTER_MIGRATION_DOWN",
  "parent_scene": {
    "scene_role": "projection_rejected_then_memory_shifted",
    "session_chapter": "Mémoire déplacée",
    "base": {"description_fr": "Mémoire haute préalable."},
    "reaction": {"description_fr": "Le centre glisse sous la zone."},
    "projection": {"description_fr": "Les reprises ne réparent pas le centre supérieur."},
    "judgment": {"retest_status": "failed_retest"}
  },
  "zone_memory": {
    "memory_state": "shifted",
    "retest_status": "failed_retest",
    "zone_low": 1.3346,
    "zone_high": 1.3364
  },
  "effort_role": "absorption_accompanying_pressure",
  "retest_status": "failed_retest",
  "memory_state": "shifted",
  "center_path": [1.33645, 1.33590, 1.33516, 1.33465],
  "time_start": "2026-05-15T11:00:00Z",
  "time_end": "2026-05-15T11:31:00Z",
  "source_profile": {
    "source_mode": "M1_BAR_PROXY",
    "data_visibility": "RECONSTRUCTED",
    "confidence_cap": 0.35
  },
  "proxy_vs_raw_verdict": "RAW_UNAVAILABLE",
  "raw_coverage": {
    "available": false,
    "coverage_ratio": 0.0,
    "source_mode": "M1_BAR_PROXY"
  },
  "limits": ["lecture reconstruite", "raw footprint non visible"]
}
```

---

## 3. Payload de sortie Temporalité

La sortie Temporalité doit rester compacte, stable et non décisionnelle.

```json
{
  "temporal_phase": "WINDOW_YOUNG | WINDOW_ACTIVE | WINDOW_LATE | WINDOW_CLOSED",
  "temporal_role": "BIRTH | REACTION | DIGESTION | RETEST | SECOND_LEG | ABSORPTION | EXHAUSTION",
  "watch_state": "WATCH_RETEST | WATCH_SECOND_LEG | WATCH_ABSORPTION | WATCH_INVALIDATION | HONEST_UNKNOWN",
  "phase_confidence": 0.0,
  "why_fr": "...",
  "limits": []
}
```

### 3.1 `temporal_phase`

| État | Sens | Utilisation |
|---|---|---|
| `WINDOW_YOUNG` | fenêtre jeune | naissance probable, microfilm récent, retest pas encore jugé |
| `WINDOW_ACTIVE` | fenêtre active | scène en cours, preuve locale vivante, arbitrage encore ouvert |
| `WINDOW_LATE` | fenêtre tardive | mouvement déjà avancé, chercher respiration, absorption ou second leg plutôt que naissance fraîche |
| `WINDOW_CLOSED` | fenêtre fermée | retest échoué, mémoire consommée, projection refusée ou phase déjà jugée |

### 3.2 `temporal_role`

| Rôle | Sens |
|---|---|
| `BIRTH` | naissance temporelle possible, non encore consommée |
| `REACTION` | réponse initiale à une zone ou mémoire |
| `DIGESTION` | flux travaille la zone sans expansion propre |
| `RETEST` | retour sur zone ou mémoire, en attente de jugement |
| `SECOND_LEG` | reprise après respiration, rejet ou absorption |
| `ABSORPTION` | effort opposé absorbé ou effort sans résultat proche d’une mémoire active |
| `EXHAUSTION` | projection tardive, effort consommé, fenêtre probablement finissante |

### 3.3 `watch_state`

| Watch | Quand l’utiliser |
|---|---|
| `WATCH_RETEST` | zone/mémoire active, retest pending/testing, besoin de jugement |
| `WATCH_SECOND_LEG` | vague progressive tardive, respiration absorbée, retest échoué de l’autre camp |
| `WATCH_ABSORPTION` | effort sans résultat, friction, mémoire active ou défendue |
| `WATCH_INVALIDATION` | retest échoué, projection decay, mémoire fragile/consumed |
| `HONEST_UNKNOWN` | source trop faible, raw absent, proxy contradictoire ou scène non classable |

---

## 4. Règles de mapping B9 → Temporalité

### 4.1 Raw coverage et confiance

```text
Si proxy_vs_raw_verdict = RAW_CONFIRMED
et raw_coverage.coverage_ratio >= 0.70
alors la Temporalité peut renforcer phase_confidence.
```

```text
Si proxy_vs_raw_verdict = RAW_UNAVAILABLE
ou raw_coverage.available = false
alors la Temporalité réduit phase_confidence et ajoute une limite.
```

```text
Si source_profile.source_mode = M1_BAR_PROXY
alors la sortie doit garder un vocabulaire prudent : probable, reconstruit, inféré, partiel.
```

### 4.2 Vague progressive tardive

```text
Si moment_type = T009_MOMENT_PROGRESSIVE_WAVE
et parent_scene.session_chapter indique une phase avancée
ou memory_state in [tested, shifted, consumed]
alors temporal_phase = WINDOW_LATE
et watch_state = WATCH_SECOND_LEG.
```

Raison : une vague progressive tardive est rarement une naissance fraîche. Elle peut indiquer une continuation, une deuxième jambe ou une fenêtre déjà avancée.

### 4.3 Effort sans résultat proche d’une mémoire active

```text
Si moment_type = T009_MOMENT_EFFORT_WITHOUT_RESULT
ou effort_role in [brake, absorption, friction]
et zone_memory.memory_state in [active, tested, defended]
alors temporal_role = ABSORPTION
et watch_state = WATCH_ABSORPTION ou WATCH_RETEST.
```

Raison : l’effort ne suffit pas. Temporalité demande si le temps travaille la zone ou si le retest juge la mémoire.

### 4.4 Retest échoué

```text
Si retest_status = failed_retest
ou zone_memory.retest_status = failed_retest
alors temporal_phase peut devenir WINDOW_CLOSED
pour la fenêtre précédente.
```

Raison : le retest juge la zone. Un retest échoué peut fermer une fenêtre antérieure et ouvrir une lecture de second leg ou d’invalidation.

### 4.5 Mémoire déplacée

```text
Si memory_state = shifted
et center_path montre une migration régulière
alors temporal_role = DIGESTION ou SECOND_LEG selon progression.
```

Raison : une mémoire déplacée n’est pas forcément une nouvelle naissance. Elle peut être une digestion active ou une reprise après jugement.

### 4.6 Projection decay

```text
Si moment_type = T009_MOMENT_PROJECTION_DECAY
ou effort_role = projection_decay
alors temporal_phase = WINDOW_LATE ou WINDOW_CLOSED
et watch_state = WATCH_INVALIDATION.
```

Raison : une projection qui ne tient pas est une preuve temporelle de fatigue ou de consommation.

### 4.7 Cas inconnus

```text
Si B9 manque de parent_scene
ou si source_profile est absent
ou si raw_coverage est inconnu
ou si les preuves se contredisent
alors watch_state = HONEST_UNKNOWN.
```

Temporalité doit préférer `HONEST_UNKNOWN` à une phase inventée.

---

## 5. Exemples attendus

### 5.1 Effort sans résultat sur mémoire active

Entrée B9 :

```json
{
  "moment_type": "T009_MOMENT_EFFORT_WITHOUT_RESULT",
  "effort_role": "absorption",
  "memory_state": "active",
  "retest_status": "pending",
  "source_profile": {"source_mode": "M1_BAR_PROXY", "confidence_cap": 0.35},
  "proxy_vs_raw_verdict": "RAW_UNAVAILABLE",
  "raw_coverage": {"available": false, "coverage_ratio": 0.0}
}
```

Sortie Temporalité :

```json
{
  "temporal_phase": "WINDOW_ACTIVE",
  "temporal_role": "ABSORPTION",
  "watch_state": "WATCH_ABSORPTION",
  "phase_confidence": 0.35,
  "why_fr": "Effort sans résultat sur mémoire active : Temporalité lit une absorption probable ou un retest à surveiller, sans redire la scène B9.",
  "limits": ["lecture reconstruite M1_BAR_PROXY", "raw indisponible"]
}
```

### 5.2 Vague progressive tardive

```json
{
  "temporal_phase": "WINDOW_LATE",
  "temporal_role": "SECOND_LEG",
  "watch_state": "WATCH_SECOND_LEG",
  "phase_confidence": 0.45,
  "why_fr": "La vague progressive arrive après déplacement de mémoire : lecture de second leg possible, pas naissance fraîche.",
  "limits": ["confirmer par retest ou propagation temporelle"]
}
```

### 5.3 Retest échoué

```json
{
  "temporal_phase": "WINDOW_CLOSED",
  "temporal_role": "RETEST",
  "watch_state": "WATCH_INVALIDATION",
  "phase_confidence": 0.55,
  "why_fr": "Le retest échoué ferme la fenêtre précédente et force une requalification temporelle.",
  "limits": ["B9 conserve la scène locale ; Temporalité ne modifie pas le retest"]
}
```

---

## 6. Contrat de confiance

### 6.1 Base recommandée

| Source / verdict | Effet sur `phase_confidence` |
|---|---|
| `RAW_CONFIRMED` + coverage >= 0.70 | +0.15 à +0.25 |
| `RAW_PARTIAL` + coverage 0.30–0.69 | neutre ou +0.05 |
| `RAW_CONFLICT` | -0.20 et `HONEST_UNKNOWN` possible |
| `RAW_UNAVAILABLE` | caper la confiance par `source_profile.confidence_cap` |
| `M1_BAR_PROXY` | confiance capée, langage prudent |

### 6.2 Règles de cap

```text
phase_confidence <= source_profile.confidence_cap
si source_mode = M1_BAR_PROXY et raw indisponible.
```

```text
phase_confidence ne doit jamais exprimer une certitude absolue.
```

---

## 7. Interdits

Temporalité ne doit jamais produire :

```text
BUY
SELL
buy
sell
achat immédiat
vente immédiate
entrée automatique
signal garanti
trade certain
```

Temporalité ne doit jamais :

```text
modifier la scène B9
réécrire zone_memory
écraser parent_scene
ignorer source_profile
ignorer raw_coverage
faire croire que proxy = raw
transformer second leg en ordre
transformer absorption en décision
```

---

## 8. Acceptance criteria documentaires

Les tests documentaires doivent vérifier :

```text
WINDOW_YOUNG / WINDOW_ACTIVE / WINDOW_LATE / WINDOW_CLOSED présents
WATCH_SECOND_LEG / WATCH_ABSORPTION présents
raw_coverage / proxy_vs_raw_verdict présents
BUY / SELL absents hors section d’interdiction contrôlée ou neutralisés par le test
séparation claire B9 vs Temporalité
```

Note test : le fichier peut mentionner BUY/SELL uniquement dans la section `Interdits`, jamais dans un exemple de sortie ni dans une recommandation.

---

## 9. Non-régression architecture

Ce contrat est documentaire :

```text
pas de DB write
pas de Telegram direct
pas de dashboard mutation
pas de fusion B8
pas de remplacement B9
pas de moteur runtime nouveau
```

---

## 10. Formule courte pour Claude

```text
B9 expose la scène locale : moment, zone, effort, retest, mémoire, source.
Temporalité ajoute la maturité : jeune, active, tardive, fermée ; puis indique quoi surveiller.
La sortie reste une perception, jamais une décision.
```
