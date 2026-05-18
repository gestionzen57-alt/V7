# LEXIQUE FR TRADER B9 — T0137M3

**Mission** : Mission parallèle 3 — Lexique FR trader B9  
**Projet** : PowerFlow / B9 MAX  
**Date** : 2026-05-18  
**Statut** : livrable documentaire prêt à installer  
**Nature** : lexique de formulation, pas moteur de décision  

---

## 0. Doctrine de formulation

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Ne lis pas l'absorption comme une direction.  
Lis où elle déplace la mémoire.

Ce lexique sert à transformer les enums techniques B9 en français trader exploitable, sans durcir une scène en ordre d'exécution, sans taux de réussite, sans certitude artificielle.

Format recommandé dans les rapports :

```text
Français trader lisible (ENUM_TECHNIQUE)
```

Exemple :

```text
Effort sans résultat (EFFORT_WITHOUT_RESULT)
```

---

## 1. Règles du lexique

1. Le français trader passe avant l'enum.
2. L'enum reste visible pour le code, les tests et l'audit.
3. La phrase B9 doit décrire : zone, effort, résultat, progrès, retest, mémoire, source.
4. Une absorption n'est jamais lue seule comme une direction.
5. Une source proxy reste proxy.
6. Un raw qui nuance ne devient pas une confirmation dure.
7. Les limites source doivent rester lisibles dans le brief.
8. Aucun ordre d'exécution, aucune promesse de répétition, aucun taux de réussite.

---

## 2. Table prioritaire — ENUM_TECHNIQUE → Français trader → phrase B9 → interdits

| ENUM_TECHNIQUE | Français trader | Exemple de phrase B9 | Interdits de formulation |
|---|---|---|---|
| `EFFORT_WITHOUT_RESULT` | Effort sans résultat | Le flux dépense de l'énergie sur la zone, mais ne gagne pas de terrain utile. | Ne pas écrire : signal fort, direction certaine, ordre évident, cassure validée. |
| `FAILED_DISPLACEMENT` | Déplacement refusé | Le prix tente de sortir de la zone, mais le déplacement ne tient pas et revient dans le champ travaillé. | Ne pas écrire : faux signal, retournement certain, échec définitif. |
| `PROGRESSIVE_WAVE` | Vague progressive | Le centre avance par paliers ; chaque palier laisse une mémoire plus loin que le précédent. | Ne pas écrire : tendance garantie, continuation certaine, accélération sûre. |
| `ABSORPTION_WITH_PROGRESS` | Absorption avec progrès | L'absorption ne bloque pas le mouvement ; elle accompagne une progression par paliers. | Ne pas écrire : absorption = retournement, absorption = direction opposée. |
| `ABSORPTION_WITHOUT_PROGRESS` | Absorption sans progrès | L'effort est visible, mais le centre reste bloqué ; la zone freine plus qu'elle ne transporte. | Ne pas écrire : force cachée certaine, retournement confirmé. |
| `CORRECTIVE_BREATH` | Respiration corrective | Le prix respire contre la scène active, mais ne répare pas encore la mémoire précédente. | Ne pas écrire : nouvelle phase confirmée, reprise validée. |
| `COUNTER_BREATH` | Respiration inverse | Le mouvement revient contre le film dominant ; il doit être jugé par son retest et par sa capacité à déplacer la mémoire. | Ne pas écrire : inversion, signal inverse, prise de contrôle. |
| `COUNTER_BREATH_REJECTED` | Respiration inverse rejetée | La respiration revient vers la zone, mais le prix ne reprend pas le centre ; la scène précédente reste active. | Ne pas écrire : piège garanti, signal contraire validé. |
| `CENTER_MIGRATION_DOWN` | Centre de gravité qui descend | Le centre glisse par paliers ; les reprises ne réinstallent pas la mémoire plus haut. | Ne pas écrire : chute certaine, direction short, vente. |
| `CENTER_MIGRATION_UP` | Centre de gravité qui monte | Le centre se réinstalle plus haut par paliers ; les retours ne reprennent pas l'ancienne mémoire basse. | Ne pas écrire : achat, signal long, continuation garantie. |
| `CENTER_LOCKED` | Centre bloqué | Le marché dépense de l'énergie, mais le centre ne quitte pas sa zone de gravité. | Ne pas écrire : compression qui va forcément casser. |
| `STAIR_STEP_PROGRESS_DOWN` | Progression descendante par paliers | Le flux accepte des zones de plus en plus basses ; chaque palier devient le nouveau point de travail. | Ne pas écrire : certitude baissière, vente évidente. |
| `STAIR_STEP_PROGRESS_UP` | Progression ascendante par paliers | Le flux accepte des zones de plus en plus hautes ; chaque palier confirme une mémoire plus élevée. | Ne pas écrire : achat évident, hausse certaine. |
| `ROUND_TRIP_NO_PROGRESS` | Aller-retour sans progrès | Le prix parcourt la zone, mais revient sans déplacer le centre utile. | Ne pas écrire : volatilité exploitable par défaut, breakout imminent. |
| `SPIKE_AND_RETRACE` | Pic puis retour | Le pic imprime une trace locale, mais le retour empêche de le traiter comme mémoire acceptée. | Ne pas écrire : breakout validé, rejet définitif sans retest. |
| `RETEST_FAILED` | Retest échoué | Le prix revient tester la zone, mais le retest ne reprend pas le centre et refuse la reprise. | Ne pas écrire : entrée, confirmation définitive, invalidation totale. |
| `RETEST_ACCEPTED` | Retest accepté | Le retour sur zone tient ; le prix réhabite la zone au lieu de la traverser en bruit. | Ne pas écrire : zone sûre, support/résistance garanti. |
| `RETEST_PENDING` | Retest en attente | La zone est identifiée, mais elle n'a pas encore été jugée proprement par un retour prix. | Ne pas écrire : validé, confirmé, tradable. |
| `FAILED_REINTEGRATION` | Réintégration échouée | Le prix rentre dans l'ancienne zone, puis ressort sans l'habiter ; la mémoire ne se réinstalle pas. | Ne pas écrire : fausse cassure certaine, signal de rejet automatique. |
| `REINTEGRATION_ATTEMPT` | Tentative de réintégration | Le prix tente de revenir dans l'ancienne zone, mais B9 attend de voir si le centre s'y réinstalle. | Ne pas écrire : réintégration validée avant acceptation. |
| `PULLBACK_ABSORBED` | Pullback absorbé | Le recul revient sur la zone, se fait absorber, et la scène garde son centre actif. | Ne pas écrire : continuation certaine, validation définitive. |
| `POST_RELEASE_PULLBACK` | Pullback après relâchement | Après le relâchement, le retour est d'abord lu comme respiration de contrôle, pas comme nouvelle scène. | Ne pas écrire : retournement, signal opposé. |
| `ZONE_DEFENDED` | Zone défendue | La zone répond ; l'effort adverse ne déplace pas encore la mémoire. | Ne pas écrire : support/résistance garanti, défense définitive. |
| `LOW_ZONE_DEFENDED` | Zone basse défendue | La zone basse absorbe l'effort et empêche le centre de s'installer plus bas pour l'instant. | Ne pas écrire : bas garanti, reprise certaine. |
| `HIGH_ZONE_DEFENDED` | Zone haute défendue | La zone haute reste travaillée ; le prix refuse de s'en éloigner proprement. | Ne pas écrire : cassure haussière validée, sommet garanti. |
| `ZONE_CONSUMED` | Zone consommée | La zone a déjà travaillé ; au retest elle ne freine plus avec la même qualité. | Ne pas écrire : zone encore fraîche, niveau garanti. |
| `HIGH_ZONE_CONSUMED` | Zone haute consommée | Après extension, la zone haute a perdu de la fraîcheur ; les mouvements qui y reviennent deviennent tardifs. | Ne pas écrire : poursuite validée, haut propre. |
| `LOW_ZONE_CONSUMED` | Zone basse consommée | La zone basse a absorbé plusieurs passages ; son rôle doit être re-jugé au prochain retest. | Ne pas écrire : plancher durable. |
| `MEMORY_SHIFTED` | Mémoire déplacée | La scène n'habite plus l'ancienne zone ; le nouveau centre travaille ailleurs. | Ne pas écrire : prédiction de suite, répétition certaine. |
| `MEMORY_NOT_SHIFTED` | Mémoire non déplacée | Le prix bouge, mais la mémoire active reste attachée à la zone précédente. | Ne pas écrire : mouvement inutile, absence de risque technique. |
| `MEMORY_LOWER_ACTIVE` | Mémoire basse active | Le marché continue de revenir travailler la zone basse ; les reprises ne déplacent pas encore le centre. | Ne pas écrire : biais directionnel dur, ordre d'exécution. |
| `MEMORY_HIGH_ACTIVE` | Mémoire haute active | Le marché continue de travailler la zone haute ; les retours ne suffisent pas encore à effacer cette mémoire. | Ne pas écrire : poursuite certaine, breakout validé. |
| `SOURCE_PROXY` | Source proxy | La scène est lisible, mais l'image vient d'une source proxy ; B9 garde une lecture plafonnée. | Ne pas écrire : confirmé raw, footprint réel, vérité tick. |
| `FORCE_SNAPSHOT_DERIVED` | Snapshot de force dérivé | La scène est reconstruite depuis `force_snapshots_v2` ; elle éclaire le film sans devenir un résumé natif retrouvé. | Ne pas écrire : summary récupéré, donnée native confirmée. |
| `M1_BAR_PROXY` | Proxy bar M1 | Le microfilm vient d'une approximation bar M1 ; utile pour le contexte, insuffisant pour durcir l'empreinte. | Ne pas écrire : tick raw, absorption prouvée. |
| `RAW_NUANCED` | Raw nuancé | Le raw nuance la scène sans la transformer en fait dur ; il ajoute de la texture, pas une certitude. | Ne pas écrire : raw confirmé, validation définitive. |
| `NUANCED_BY_RAW` | Nuancé par raw | La donnée raw module la lecture initiale, mais ne remplace pas le verdict prix. | Ne pas écrire : confirmé par raw, preuve absolue. |
| `RAW_UNAVAILABLE` | Raw indisponible | B9 ne dispose pas du raw nécessaire ; la lecture doit rester hors mémoire active dure. | Ne pas écrire : invisible donc faux, proxy donc certain. |

---

## 3. Table complémentaire — rôles de scène B9

| ENUM_TECHNIQUE | Français trader | Exemple de phrase B9 | Interdits de formulation |
|---|---|---|---|
| `SCENE_BUILDING` | Scène en construction | Les traces s'accumulent, mais la scène n'a pas encore été jugée par un retest propre. | Ne pas écrire : scène validée, signal mature. |
| `SCENE_TESTING` | Scène en test | Le prix revient juger la zone ; le rôle du mouvement dépend de la réponse sur ce retour. | Ne pas écrire : décision prise, confirmation automatique. |
| `SCENE_ACCEPTED` | Scène acceptée | Le prix réhabite la zone et laisse un centre cohérent avec la scène en cours. | Ne pas écrire : certitude, répétition garantie. |
| `SCENE_REJECTED` | Scène rejetée | La tentative de scène ne tient pas au contact de la zone ; la mémoire refuse de se déplacer dans ce sens. | Ne pas écrire : faux signal, piège certain. |
| `SCENE_DECONSTRUCTING` | Scène en déconstruction | Les preuves anciennes perdent leur rôle ; la mémoire active se fragilise. | Ne pas écrire : inversion confirmée. |
| `SCENE_REBUILDING` | Scène en reconstruction | Après le choc, le marché tente de reconstruire une mémoire lisible. | Ne pas écrire : nouveau cycle validé. |
| `SCENE_MEMORY_SHIFTED` | Scène avec mémoire déplacée | Le centre utile a changé de zone ; B9 lit maintenant le nouveau point de gravité. | Ne pas écrire : prochaine direction certaine. |
| `PRESSURE_WITHOUT_PROGRESS` | Pression sans progrès | La pression est visible, mais elle ne renouvelle pas d'extrême utile. | Ne pas écrire : cassure imminente. |
| `REACTION_NOT_RELEASE` | Réaction, pas relâchement | Le mouvement répond à une zone, mais ne prouve pas encore une libération structurelle. | Ne pas écrire : release validée. |
| `LATE_THIN_BOUNCE` | Rebond tardif fragile | La reprise arrive tard, avec peu de mémoire déplacée ; elle reste fragile dans le film. | Ne pas écrire : reprise validée, retournement propre. |
| `POST_LOW_REACTION` | Réaction après zone basse | Le prix répond depuis la zone basse ; B9 surveille si la réaction déplace vraiment la mémoire. | Ne pas écrire : bas confirmé, achat. |
| `POST_HIGH_UNWIND` | Déroulement après rejet haut | Après rejet de zone haute, le prix déroule la mémoire construite plus bas. | Ne pas écrire : vente, chute certaine. |
| `SECOND_LEG_DOWN` | Deuxième jambe descendante | Après respiration rejetée, le marché reprend le travail de mémoire plus bas. | Ne pas écrire : signal directionnel automatique. |
| `SECOND_LEG_UP` | Deuxième jambe ascendante | Après pullback absorbé, le marché reprend le travail de mémoire plus haut. | Ne pas écrire : continuation garantie. |
| `HIGH_ZONE_REJECTION` | Rejet de zone haute | La zone haute a été testée, mais le prix ne l'habite pas ; elle devient un repère de refus. | Ne pas écrire : sommet définitif. |
| `LOWER_LOCK` | Verrouillage bas | Le prix accepte une mémoire basse et les reprises sont d'abord jugées comme respirations. | Ne pas écrire : direction durable garantie. |
| `EVENT_STACK_ONLY` | Empilement d'événements seulement | B9 voit de l'activité, mais pas encore une naissance de scène. | Ne pas écrire : naissance validée, impulsion confirmée. |
| `FALSE_BIRTH` | Fausse naissance | L'activité ressemble à un départ, mais le prix ne confirme pas le déplacement de mémoire. | Ne pas écrire : faux signal, échec certain. |

---

## 4. Table complémentaire — visibilité source et prudence technique

| ENUM_TECHNIQUE | Français trader | Exemple de phrase B9 | Interdits de formulation |
|---|---|---|---|
| `FULL_STACK_VISIBLE` | Lecture complète | Les couches nécessaires sont visibles ; B9 peut lire la scène avec moins d'angle mort technique. | Ne pas écrire : certitude totale. |
| `TACTICAL_OK` | Lecture tactique exploitable | La scène est lisible pour le brief, mais les limites source restent affichées. | Ne pas écrire : donnée parfaite. |
| `READING_PARTIAL` | Lecture partielle | B9 voit une partie du film ; les zones manquantes empêchent de durcir la conclusion. | Ne pas écrire : scène invalide, scène confirmée. |
| `MICROFILM_MISSING` | Microfilm manquant | Le microfilm local manque ; B9 doit éviter de raconter l'intérieur du mouvement. | Ne pas écrire : absorption prouvée, retest prouvé. |
| `PACKETS_STALE` | Packets périmés | Les packets ne suivent plus le prix récent ; la lecture doit être marquée comme vieillissante. | Ne pas écrire : état live confirmé. |
| `CENTER_PATH_VISIBLE` | Chemin du centre visible | B9 voit le chemin interne du centre, pas seulement le début et la fin. | Ne pas écrire : chaque tick est connu. |
| `CENTER_PATH_START_END_ONLY` | Chemin réduit début-fin | B9 ne voit que le début et la fin ; le trajet interne reste incertain. | Ne pas écrire : progression linéaire prouvée. |
| `CENTER_PATH_PROXY_EXTREMES` | Chemin proxy par extrêmes | B9 déduit les extrêmes, mais ne possède pas la chronologie raw complète. | Ne pas écrire : trajectoire native visible. |
| `CENTER_PATH_NOT_VISIBLE` | Chemin du centre non visible | Le chemin interne manque ; B9 limite son commentaire au résultat observable. | Ne pas écrire : chemin confirmé. |
| `HONEST_UNKNOWN` | Inconnu honnête | La donnée ne permet pas de trancher proprement ; B9 doit le dire. | Ne pas écrire : hypothèse forte sans preuve. |
| `SOURCE_QUALITY_HARD_GATE` | Barrière qualité source | La source est trop faible pour entrer en mémoire active dure. | Ne pas écrire : filtré par prudence morale ; dire limite technique. |

---

## 5. Phrases prêtes pour brief B9

### Effort / résultat / progrès

```text
Le flux dépense de l'énergie, mais le centre ne gagne pas de terrain utile.
```

```text
Le mouvement existe, mais le progrès réel reste faible : la mémoire ne s'est pas déplacée.
```

```text
L'absorption accompagne la progression : elle ne bloque pas le mouvement, elle le transporte par paliers.
```

### Retest / réintégration

```text
Le retest juge la zone défavorablement : le prix revient, mais ne reprend pas le centre.
```

```text
La réintégration reste une tentative : le prix entre dans l'ancienne zone, sans encore l'habiter.
```

```text
Le pullback est absorbé : le recul travaille la zone sans casser la mémoire active.
```

### Zone / mémoire

```text
La zone répond encore : elle est défendue, mais pas définitivement validée.
```

```text
La zone semble consommée : elle a déjà travaillé et doit être re-jugée au prochain contact.
```

```text
La mémoire active se déplace : l'ancienne zone n'est plus le centre du film.
```

### Source / raw

```text
Lecture proxy : B9 voit la forme générale, mais ne durcit pas l'empreinte comme raw.
```

```text
Raw nuancé : la donnée ajoute de la texture, sans transformer la scène en fait définitif.
```

```text
Microfilm incomplet : B9 peut lire le résultat, pas toute la mécanique interne.
```

---

## 6. Interdits globaux de formulation

Éviter dans les rapports B9 :

```text
vrai signal
faux signal
direction certaine
validation définitive
ordre évident
niveau garanti
reprise sûre
cassure sûre
retournement confirmé
répétition certaine
taux de réussite
```

Préférer :

```text
lecture dominante
lecture alternative
hypothèse forte
scène en construction
scène en test
retest favorable / défavorable
mémoire déplacée / non déplacée
source proxy
raw nuancé
limite technique visible
```

---

## 7. Contrôle qualité pour futurs rapports

Avant de publier un brief B9, vérifier :

- Le français trader est en premier.
- L'enum technique reste entre parenthèses ou en champ adjacent.
- La phrase décrit le rôle dans le film, pas une direction brute.
- Le retest et la mémoire sont mentionnés quand ils sont disponibles.
- La source est visible si elle est proxy, reconstruite, périmée ou partielle.
- Aucun ordre d'exécution n'est introduit.
- Aucun taux de réussite n'est introduit.
- Aucun proxy n'est transformé en raw confirmé.

---

## 8. Phrase de verrouillage

```text
B9 parle en français trader : effort, résultat, progrès, retest, zone, mémoire, source.
L'enum sert au code ; la phrase sert au trader.
```
