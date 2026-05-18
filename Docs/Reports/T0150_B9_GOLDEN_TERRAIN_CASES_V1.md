# T0150 — B9 Golden Terrain Cases V1

**Projet :** PowerFlow / B9 MAX  
**Mission :** Mission parallèle 4 — Golden terrain cases  
**Date livrable :** 2026-05-18  
**Type :** documentaire uniquement — aucun code moteur, aucun dashboard, aucun Telegram, aucun ordre directionnel.

---

## 1. Résumé mission

Objectif : figer une première bibliothèque de cas terrain golden B9 à transformer plus tard en tests.

Doctrine appliquée :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Ne lis pas l’absorption comme une direction.
Lis où elle déplace la mémoire.
```

Le livrable ne propose pas de décision de trading. Il prépare des cas de validation pour vérifier si B9 sait lire :

- l’effort visible ;
- le résultat produit ;
- le progrès réel ;
- le centre déplacé ou non ;
- la zone habitée, défendue, consommée ou rejetée ;
- le rôle de scène au lieu du signal brut.

---

## 2. Sources lues

Sources internes du pack B9 MAX :

```text
00_START_HERE/00_START_HERE_B9_MAX_WORKSPACE_HANDOFF.md
01_CONTEXT_CORE/01_B9_MAX_CONTEXT_MASTER.md
02_ROADMAP_AND_STATUS/00_CURRENT_STATUS_T0113_T0136.md
02_ROADMAP_AND_STATUS/01_ROADMAP_B9_MAX_V2_T0137_T0157.md
03_MISSION_PROMPTS_PARALLEL/04_MISSION_GOLDEN_TERRAIN_CASES.md
05_SOURCE_DOCS/08_FIELD_MEMORY_GBPUSD_20260506_14.md
05_SOURCE_DOCS/09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md
05_SOURCE_DOCS/10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md
05_SOURCE_DOCS/12_LEXIQUE_FR_TRADER_POWERFLOW_V767.md
05_SOURCE_DOCS/ANALYSE_T009_B9_LONDON_GBPUSD_20260515_0800_1200.md
05_SOURCE_DOCS/ANALYSE_T009_B9_GBPUSD_20260515_1200_1400.md
05_SOURCE_DOCS/ANALYSE_T009_B9_GBPUSD_20260515_JOURNEE_COMPLETE.md
05_SOURCE_DOCS/VALIDATION_B9_SUMMARIZER_V01_V3_LONDON_0800_1400.md
```

Limite importante : les journées 2026-05-06 à 2026-05-14 sont disponibles surtout comme films B6 / field memory. Les horaires fins ne sont pas toujours fournis dans le pack. Les cas 2026-05-15 sont les plus directement testables en T009/B9 avec fenêtres horaires précises.

---

## 3. Verdict court

La bibliothèque V1 doit séparer deux niveaux :

```text
READY_T009_PRECISE = cas déjà horodaté finement, transformable en test de summarizer.
B6_TO_HORODATE = cas terrain validé comme film, mais à recaler sur replay avant test automatisé.
```

Les meilleurs cas immédiats pour tests unitaires / replay sont :

```text
08:00–08:14 2026-05-15 = effort sans résultat
10:00–10:23 2026-05-15 = absorption + centre montant / vague progressive
11:00–11:31 2026-05-15 = absorption + centre descendant
13:38–13:53 2026-05-15 = vague progressive réelle vers zone haute
13:53–14:57 2026-05-15 = haut projeté non accepté / rejet
17:20–18:45 2026-05-15 = retest haut échoué puis mémoire basse déplacée
```

Les cas 06–14 doivent rester en bibliothèque B6 comme familles de films à horodater : release acceptée, pullback absorbé, zone basse défendue, failed reintegration, second leg baissière.

---

## 4. Golden terrain cases V1

| ID | Statut | Date | Heure | Film FR | Preuve B9 attendue | Source limits | Label attendu | Risque technique de faux positif |
|---|---|---:|---|---|---|---|---|---|
| GTC_B9_001 | B6_TO_HORODATE | 2026-05-08 | Journée / clôture, heure fine à recaler | Zone basse → relâchement haussier → pullback absorbé → clôture haute. | Prix accepte plus haut, pullback ne casse pas la provenance, clôture proche des hauts, scène non consommée. | Film B6 enrichi ; pas de microfenêtre T009 dans le pack. À recaler avec replay / packets. | `RELEASE_UP_ACCEPTED` / `UP_CONTINUATION_ACCEPTED` | Confondre une hausse tardive consommée avec une release acceptée si le haut n’est pas jugé par clôture / retest. |
| GTC_B9_002 | B6_TO_HORODATE | 2026-05-11 | Après premier leg, heure fine à recaler | Fausses naissances → premier leg → pullback absorbé → deuxième jambe haussière. | B3/B2 seuls = empilement ; validation seulement si pullback absorbé + reprise du centre + deuxième jambe. | Film B6 ; besoin de retrouver la séquence exacte dans replay. | `PULLBACK_ABSORBED` / `SECOND_LEG_UP_AFTER_ABSORBED_PULLBACK` | Surclasser une simple respiration en pullback absorbé si le centre ne se reconstruit pas vraiment. |
| GTC_B9_003 | READY_T009_PRECISE | 2026-05-15 | 14:02–14:57 | Projection haute London refusée, migration descendante depuis 1.338–1.339 vers 1.3360. | Centres glissent par paliers après projection haute ; effort local autour du haut mais absence d’acceptation supérieure ; mémoire quitte la zone haute. | M1_BAR_PROXY / RECONSTRUCTED ; raw tick nécessaire pour parler de piège ou footprint exact. | `HIGH_ZONE_REJECTION` / `PROJECTION_REJECTED_MEMORY_SHIFTED` | Lire un pullback normal comme rejet haut avant que le retest / centre inférieur confirme la perte d’acceptation. |
| GTC_B9_004 | B6_TO_HORODATE | 2026-05-14 | Journée / session, heure fine à recaler | Rejet haut → réintégration échouée → deuxième jambe baissière. | Mouvement de réintégration qui ne réhabite pas la zone haute ; retour sous centre ; la respiration inverse devient rejetée. | Film B6 ; manque fenêtre T009 précise dans le pack. | `FAILED_REINTEGRATION` / `COUNTER_BREATH_REJECTED` | Confondre réintégration échouée et simple pause si la zone médiane n’est pas explicitement testée. |
| GTC_B9_005 | B6_TO_HORODATE | 2026-05-13 | Après tension inverse / dernier pic, heure fine à recaler | Extension haute → tension inverse avant dernier pic → rejet haut → deuxième jambe baissière. | Dernier pic non accepté, tension inverse visible avant le rejet, mouvement suivant requalifié en second leg et non `PAIR_DOWN` brut. | Film B6 ; à valider sur données fines et prix. | `SECOND_LEG_DOWN` / `POST_HIGH_REJECTION_SECOND_LEG_DOWN` | Prendre un déroulement post-high classique pour une vraie second leg si la respiration inverse rejetée n’est pas prouvée. |
| GTC_B9_006 | B6_TO_HORODATE | 2026-05-12 | Second test bas / rebond tardif, heure fine à recaler | Relâchement baissier → zone basse touchée → respiration inverse → second test bas défendu → rebond tardif. | Zone basse revisitée ; pression baissière ne produit plus de progrès ; second test défendu ; réaction visible après zone basse. | Film B6 ; pas de granularité B9 fournie. | `LOW_ZONE_DEFENDED` / `POST_LOW_REACTION` | Lire une zone basse défendue alors que le mouvement est seulement ralenti par manque de liquidité / late thin bounce. |
| GTC_B9_007 | READY_T009_PRECISE | 2026-05-15 | 08:00–08:14 | London open : effort visible, frein local, recollage, pas de progression propre. | Absorption élevée, failed displacement élevé, compression élevée, centre sans progrès durable. | M1_BAR_PROXY ; effort/résultat approximatif, pas de delta exact. | `T009_MOMENT_EFFORT_WITHOUT_RESULT` | Déclarer effort sans résultat trop tôt alors que la zone peut casser quelques minutes plus tard ; nécessite contexte de suite. |
| GTC_B9_008 | READY_T009_PRECISE | 2026-05-15 | 11:00–11:31 | Pression basse par paliers : absorption répétée + centre descendant. | Centres descendent progressivement malgré absorption/dwell élevés ; la mémoire basse est acceptée par paliers. | M1_BAR_PROXY ; absorption probable et non footprint exact. | `T009_MOMENT_CENTER_MIGRATION_DOWN` / `ABSORPTION_CENTER_DOWN` | Interpréter absorption comme retournement alors qu’elle accompagne le déplacement descendant de mémoire. |
| GTC_B9_009 | READY_T009_PRECISE | 2026-05-15 | 10:00–10:23 | Vraie vague progressive haussière : absorption + centre montant. | Centres montent de 1.33506 vers 1.33742 ; effort produit résultat et progrès ; zones absorbées successives mais plus hautes. | M1_BAR_PROXY ; progression claire mais source reconstruite. | `T009_MOMENT_PROGRESSIVE_WAVE` / `ABSORPTION_CENTER_UP` | Classer en effort sans résultat parce que l’absorption est élevée ; erreur centrale à éviter. |
| GTC_B9_010 | READY_T009_PRECISE | 2026-05-15 | 13:38–13:53 | Accélération depuis zone de décision vers zone haute 1.3391. | Centre progresse fortement de 1.33680 à 1.33915 ; la zone 1.3362–1.3366 ne rejette pas, elle sert de base de continuation. | Validation V0.1/V3 indique sous-détection actuelle de cette accélération ; besoin scène parent. | `T009_MOMENT_PROGRESSIVE_WAVE` / `FRESH_VOLUME_REACTION` | Fragmentation du summarizer : micro-moments isolés peuvent masquer la vague progressive réelle. |
| GTC_B9_011 | READY_T009_PRECISE | 2026-05-15 | 15:48–15:59 puis 16:00–17:00 | Pression basse puis rebond correctif, sans réparation durable des zones hautes. | Rebond vers 1.3355 visible, mais il ne reprend pas 1.338–1.339 ; la mémoire reste attirée vers les zones basses. | M1_BAR_PROXY ; confirmer par parent_scene 14:00–17:00. | `T009_MOMENT_CORRECTIVE_WAVE_NO_DURABLE_PROGRESS` | Confondre une petite vague progressive locale avec acceptation structurelle. |

---

## 5. Format cible futur pour tests

Chaque cas doit devenir un fixture terrain, pas une règle de décision.

Structure recommandée :

```json
{
  "case_id": "GTC_B9_008",
  "symbol": "GBPUSD",
  "date": "2026-05-15",
  "time_start": "11:00",
  "time_end": "11:31",
  "expected_label": "T009_MOMENT_CENTER_MIGRATION_DOWN",
  "expected_scene_role": "absorption_accompanying_pressure",
  "must_observe": [
    "center_path_down",
    "absorption_high",
    "failed_displacement_high",
    "memory_shift_lower"
  ],
  "must_not_say": [
    "ordre directionnel",
    "ordre directionnel",
    "signal certain",
    "footprint exact"
  ],
  "source_limits": [
    "M1_BAR_PROXY",
    "RECONSTRUCTED",
    "raw footprint non visible"
  ]
}
```

---

## 6. Assertions terrain par famille

### 6.1 Release UP acceptée

```text
Le test ne doit pas valider une release UP sur PAIR_UP seul.
Il doit demander : zone basse + relâchement + pullback absorbé + acceptation plus haute.
```

### 6.2 Pullback absorbé

```text
Le mouvement inverse après release UP reste pullback par défaut.
Il devient pullback absorbé seulement si la provenance n’est pas cassée et si un centre supérieur se reconstruit.
```

### 6.3 Rejet haut / failed reintegration

```text
Le haut n’est pas rejeté parce qu’il est touché.
Il est rejeté si le retest ne conserve pas le centre haut et si la mémoire commence à descendre.
```

### 6.4 Deuxième jambe baissière

```text
La second leg baissière exige une respiration inverse ou réintégration rejetée avant continuation basse.
Sans ce contexte, ce n’est qu’un POST_HIGH_UNWIND ou une migration descendante.
```

### 6.5 Zone basse défendue

```text
Une zone basse défendue exige test / retest / absence de progrès baissier.
Un simple ralentissement n’est pas suffisant.
```

### 6.6 Effort sans résultat

```text
Effort haut + compression + failed displacement haut + centre stable = effort sans résultat.
Si le centre migre par paliers, requalifier en migration de centre.
```

### 6.7 Absorption + centre descendant

```text
L’absorption ne bloque pas forcément le mouvement.
Si le centre descend, elle accompagne une pression qui avance.
```

### 6.8 Absorption + centre montant

```text
L’absorption ne doit pas être classée frein si le centre monte franchement.
Le label attendu devient vague progressive / mémoire déplacée vers le haut.
```

### 6.9 Rebond correctif sans progrès durable

```text
Une reprise locale peut être réelle mais corrective.
Elle ne devient acceptation structurelle que si les anciennes mémoires hautes sont réhabitées.
```

---

## 7. Risques techniques transversaux

```text
1. Horodatage replay shifted : risque de golden case impossible à rejouer si le remap n’est pas corrigé.
2. Segmentation trop fine : risque de perdre la scène parent et de mal lire 13:38–13:53.
3. Segmentation trop large : risque de fusionner correction, décision, rejet et migration.
4. M1_BAR_PROXY : absorption / delta / footprint doivent rester probables ou reconstruits.
5. Film B6 sans heure fine : les cas 06–14 doivent être horodatés avant test automatisé.
6. Vocabulaire trop directionnel : éviter PAIR_UP / PAIR_DOWN brut comme vérité.
7. Surclassement : ne pas transformer réaction locale en acceptation structurelle.
8. Sous-classement : ne pas classer une vraie vague progressive en effort sans résultat à cause d’absorption élevée.
```

---

## 8. Priorité d’implémentation future

```text
P0 — Transformer les READY_T009_PRECISE en fixtures de replay : GTC_B9_007 à GTC_B9_011.
P1 — Ajouter scènes parent pour GTC_B9_003, GTC_B9_010, GTC_B9_011.
P2 — Rejouer / horodater les cas B6 06–14 : GTC_B9_001 à GTC_B9_006.
P3 — Construire une Golden Terrain Library V1 officielle avec JSON fixtures.
```

---

## 9. Message final pour orchestrateur

Cette mission livre une base golden terrain exploitable immédiatement comme cahier de tests futurs.

Le cœur B9 à verrouiller :

```text
Effort ≠ direction.
Absorption ≠ retournement.
Progression = déplacement du centre + mémoire qui change de zone.
Rejet = zone testée puis non acceptée.
Rebond correctif ≠ acceptation structurelle.
```

Le prochain geste utile côté architecture : transformer les cas 2026-05-15 en fixtures replay read-only, puis recaler les cas B6 06–14 sur des horaires précis.
