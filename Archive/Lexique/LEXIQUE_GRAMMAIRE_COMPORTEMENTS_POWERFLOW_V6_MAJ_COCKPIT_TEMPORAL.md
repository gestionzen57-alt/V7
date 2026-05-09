# LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW_V6.md

## Mise à jour : Cockpit Field + Temporal Patterns

Cette mise à jour ajoute la grammaire consolidée autour de la brique :

```text
Cockpit Field
+
Battlefield Map
+
Bipolar Field
+
Temporal Patterns
```

Elle formalise les termes apparus pendant la consolidation de `run_cockpit_field.py`, `pf_cockpit_field.py` et `pf_temporal_patterns_cockpit.py`.

---

# 1. Principes généraux

## 1.1 Zone dynamique

Une zone dynamique n'est pas une ligne fixe.
C'est un champ comportemental.

Elle peut être :
- basse ;
- haute ;
- extrême ;
- pré-extrême ;
- centrale ;
- en accumulation ;
- en respiration ;
- en release ;
- en contestation.

Une zone peut être travaillée sur plusieurs timeframes.
Plusieurs timeframes dans la même zone peuvent signaler une accumulation d'intérêt, une mémoire de session ou une structure institutionnelle/fractale.

---

## 1.2 Antagoniste d'une zone extrême

L'antagoniste naturel d'une zone dynamique extrême est l'équilibre.

Un extrême n'appelle pas automatiquement un retournement.
Il appelle une question :

```text
L'énergie va-t-elle être absorbée, relâchée, rechargée, ou ramenée vers l'équilibre ?
```

L'équilibre n'est donc pas une zone morte.
C'est souvent :
- la cible de retour ;
- la zone de validation ;
- la zone de croisement ;
- la zone où le marché révèle si la structure a payé.

---

## 1.3 Fractalité des zones

Une zone M1 ou M5 ne doit pas être lue seule.
Elle peut être :
- une naissance locale ;
- un relais ;
- une micro-release ;
- une contestation ;
- le symptôme visible d'une scène HTF.

Les profils temporels consolidés :

```text
SHORT = M1 / M5 / M15
MEDIUM = M15 / M30 / H1
LONG = H4 / D1 / W
```

Nuance :
- M1 est spécial : microfilm, rafraîchi par la DB toutes les quelques secondes selon contexte ;
- M5/M15 donnent le relais et le profil court terme ;
- M15/M30/H1 structurent la scène ;
- H4/D1/W donnent la gravité.

---

# 2. Cockpit Field

## 2.1 `COCKPIT FIELD`

Sortie synthétique principale.

Mission :
- afficher le champ dominant ;
- afficher la coalition ;
- afficher la contestation ;
- afficher le focus bipolaire ;
- afficher les patterns temporels utiles.

Le cockpit ne doit pas tout raconter.
Il doit montrer ce qui compte maintenant.

---

## 2.2 `TACTICAL_RELEASE_BATTLEFIELD`

Champ tactique où une ou plusieurs devises libèrent déjà de l'énergie sur les petits timeframes.

Signature :
- présence de release sur M1/M5 ;
- coalition HIGH ou LOW active ;
- préparation encore visible autour ;
- champ souvent lié au microfilm.

Exemple validé :

```text
TACTICAL_RELEASE_BATTLEFIELD:
release=CAD HIGH/GBP HIGH
prep=EUR HIGH/CHF HIGH/AUD HIGH/JPY HIGH
```

Lecture :
une coalition micro travaille ou relâche l'énergie.

---

## 2.3 `HTF_PREPARATION_FIELD`

Champ supérieur en préparation.

Signature :
- M15/M30/H1 actifs ;
- pas forcément de release immédiate ;
- tension portée ;
- possible opposition au microfilm.

Exemple validé :

```text
HTF_PREPARATION_FIELD:
LOW=EUR/GBP/CHF/CAD/JPY
```

Lecture :
la scène supérieure prépare ou maintient une tension opposée.

---

## 2.4 `CONTESTED_WINDOW`

Fenêtre temporelle contestée.

Définition :
zone où les deux côtés HIGH et LOW existent simultanément dans le champ.

Exemple :

```text
CONTESTED_WINDOW:
HIGH=CAD/GBP/EUR/CHF/AUD/JPY
vs
LOW=EUR/GBP/CHF/CAD/JPY
```

Lecture :
le marché n'est pas unidirectionnel.
Il travaille une contradiction de forces.

---

## 2.5 `BIPOLAR_CONTESTED_RELEASE_WINDOW`

Fenêtre contestée où une release existe d'un côté pendant que l'autre côté prépare ou porte une tension.

C'est une situation prioritaire cockpit, car elle indique :
- release visible ;
- opposition active ;
- possibilité de rotation ;
- possibilité de piège ;
- possible micro contre HTF.

---

## 2.6 `BIPOLAR_FOCUS`

Devise centrale de la contradiction.

Exemple validé :

```text
BIPOLAR_FOCUS:
EUR | MICRO_VS_HTF_ROTATION_CONTEST | HIGH_TF=M1,M5 vs LOW_TF=M15,M30
```

Lecture :
EUR est travaillée simultanément :
- en HIGH sur microfilm ;
- en LOW sur scénario supérieur.

---

## 2.7 `BIPOLAR_LIST`

Liste compacte des devises contradictoires.

Format :

```text
EUR:PREPH/PREPL
GBP:RELH/PREPL
CAD:RELH/PREPL
CHF:PREPH/PREPL
```

Lecture :
- `PREPH` = préparation HIGH ;
- `PREPL` = préparation LOW ;
- `RELH` = release HIGH ;
- `RELL` = release LOW.

---

# 3. Temporal Patterns

## 3.1 `TEMPORAL_PATTERNS`

Bloc cockpit qui ajoute la perception temporelle fine au champ global.

Il condense :
- respiration ;
- pullures ;
- densité ;
- angle ;
- cibles temporelles.

Sortie type :

```text
TEMPORAL_PATTERNS:
BREATHING: ...
PULLURE: ...
DENSITY: ...
ANGLE: ...
TEMPORAL_TARGETS: ...
TEMPORAL_ROWS: ...
```

---

## 3.2 `BREATHING`

Respiration dominante détectée.

Elle indique qu'une devise travaille une zone par micro-oscillations.

Exemple :

```text
BREATHING:
USD M1 LOW PULLURE_ABSORPTION_FIELD
```

Lecture :
USD est en bas M1 et absorbe des tentatives de sortie.

---

## 3.3 `PULLURE`

Tentative de sortie / fuite / échappée qui est reprise ou absorbée par la zone.

Dans PowerFlow, une pullure n'est pas un simple bruit.
C'est une tentative comportementale.

Quand plusieurs pullures sont absorbées, la zone gagne en énergie.

---

## 3.4 `PULLURE_ABSORPTION_FIELD`

Champ où des pullures sont absorbées.

Signature :
- pullures non nulles ;
- compressions internes ;
- énergie maintenue ;
- zone qui refuse de lâcher immédiatement.

Exemple validé :

```text
USD M1 LOW PULLURE_ABSORPTION_FIELD
score=12.595
energy=5.745
pullures=7
comp=209
```

Lecture :
USD travaille la zone basse, tente de sortir, mais la zone absorbe.

---

## 3.5 `EXTREME_BREATHING_FIELD`

Champ de respiration extrême.

Signature :
- compressions élevées ;
- peu ou pas de pullures ;
- énergie accumulée ;
- devise maintenue dans une zone extrême.

Exemple :

```text
AUD M1 LOW EXTREME_BREATHING_FIELD
```

Lecture :
AUD respire en bas, énergie stockée, pas forcément encore release.

---

## 3.6 `SOFT_BREATHING_FIELD`

Respiration plus faible ou moins décisive.

Elle est utile comme contexte secondaire, mais ne doit pas dominer le cockpit si des champs plus forts sont présents.

---

## 3.7 `TEMPORAL_DENSITY_FIELD`

Champ de densité temporelle.

Formule :

```text
densité = sum(abs(delta_force)) / window
```

Rôle :
- mesurer la vitesse de mouvement par barre ;
- distinguer compression rapide et mouvement lent ;
- détecter les zones où le flux devient nerveux.

Exemple validé :

```text
EUR M30 TEMPORAL_DENSITY_FIELD
density=4.379
cutoff=2.882
```

Lecture :
EUR porte une densité temporelle sur M30, donc le mouvement n'est pas seulement micro.

---

## 3.8 `HIGH_TEMPORAL_COMPRESSION_FIELD`

Version forte de densité temporelle.

Signature :
- densité très élevée ;
- compression rapide ;
- souvent visible en M15/M30 ;
- peut précéder une release ou signaler une phase de force déjà engagée.

---

## 3.9 `SOFT_TEMPORAL_DENSITY_FIELD`

Densité faible ou modérée.

À garder comme contexte, mais à filtrer dans le cockpit via percentile pour éviter la noyade M1.

---

## 3.10 `ANGULAR_ALIGNMENT_NODE`

Node où plusieurs devises présentent un angle commun ou proche.

Signature :
- plusieurs devises alignées ;
- angle commun ;
- qualité d'alignement ;
- parfois changement de direction simultané.

Exemple validé :

```text
CHF,EUR,GBP M1 ANGULAR_ALIGNMENT_NODE
angle=-78.22
q=0.843
changes=1
```

Lecture :
CHF, EUR et GBP changent d'inclinaison ensemble sur le microfilm.

---

## 3.11 `SAME_ANGLE_INTENTION_NODE`

Version forte de l'alignement angulaire.

Signature :
- qualité élevée ;
- plusieurs changements de direction ;
- même angle ou angle très proche ;
- convergence d'intention.

Lecture :
les devises ne bougent pas seulement ensemble, elles changent d'intention ensemble.

---

## 3.12 `TEMPORAL_TARGETS`

Liste des cibles temporelles prioritaires.

Exemple :

```text
USD/M1/LOW/PULLURE_ABSORPTION_FIELD/score=12.59
CHF/M1/HIGH/PULLURE_ABSORPTION_FIELD/score=11.88
AUD/M1/LOW/EXTREME_BREATHING_FIELD/score=10.24
```

Lecture :
le cockpit donne une hiérarchie de champs temporels.

---

## 3.13 `TEMPORAL_ROWS`

Nombre de lignes DB utilisées par timeframe.

Exemple validé :

```text
TEMPORAL_ROWS:
M1=181 | M5=37 | M15=13 | M30=7 | H1=4
```

Lecture :
le cockpit montre la profondeur réelle utilisée dans la fenêtre récente.

---

# 4. Concepts fractals consolidés

## 4.1 `MICRO_VS_HTF_ROTATION_CONTEST`

Conflit entre microfilm et scène supérieure.

Exemple :

```text
EUR HIGH_TF=M1,M5
vs
EUR LOW_TF=M15,M30
```

Lecture :
le microfilm travaille le haut alors que la scène supérieure prépare le bas.

C'est une zone de rotation potentielle ou de contestation.
Ce n'est pas une vérité directionnelle.
C'est un champ à surveiller.

---

## 4.2 `HIGH_COALITION`

Ensemble de devises travaillant ou préparant le côté haut.

Exemple :

```text
HIGH=CAD/GBP/EUR/CHF/AUD/JPY
```

---

## 4.3 `LOW_COALITION`

Ensemble de devises travaillant ou préparant le côté bas.

Exemple :

```text
LOW=EUR/GBP/CHF/CAD/JPY
```

---

## 4.4 `DUAL_SIDE_FIELD`

Champ où HIGH et LOW sont simultanément actifs.

Ce champ est important parce qu'il montre :
- contestation ;
- rotation possible ;
- contradiction interne ;
- bataille non résolue.

---

## 4.5 `RELEASE_PRESENT`

La carte détecte qu'une release est déjà visible dans au moins une partie du champ.

---

## 4.6 `PREPARATION_PRESENT`

La carte détecte qu'une préparation existe encore dans une autre partie du champ.

---

## 4.7 `MICROFILM_PRESENT`

La scène contient M1/M5.

Rappel :
M1 est un microfilm, pas seulement une bougie M1 classique.
La DB peut capter plusieurs rafraîchissements dans la minute selon le flux disponible.

---

## 4.8 `HTF_ANCHOR_PRESENT`

La scène contient M15/M30/H1 ou supérieur.
Cela donne de la structure au champ.

---

# 5. Grammaire cockpit recommandée

## 5.1 Phrase de lecture compacte

Format futur :

```text
ORION_FIELD_SENTENCE:
[release micro] + [préparation HTF] + [bipolaire] + [temporal patterns]
```

Exemple :

```text
ORION_FIELD_SENTENCE:
CAD/GBP release HIGH microfilm, EUR contested micro HIGH vs HTF LOW, USD absorbs LOW pullures, EUR carries M30 density.
```

---

## 5.2 Priorité d'affichage

Ordre recommandé :

```text
1. FIELD
2. DOMINANT
3. OPPOSITE/CONTEXT
4. CONTESTED_WINDOW
5. BIPOLAR_FOCUS
6. TEMPORAL_PATTERNS
7. TEMPORAL_TARGETS
```

---

## 5.3 Lecture PowerFlow

Le cockpit ne dit pas :

```text
acheter / vendre
```

Il dit :

```text
où est la bataille
où est la release
où est la préparation
où est la contradiction
où l'énergie respire
où les pullures sont absorbées
où l'angle collectif change
```

---

# 6. Statut de cette mise à jour

Termes ajoutés ou consolidés :

```text
TEMPORAL_PATTERNS
BREATHING
PULLURE
PULLURE_ABSORPTION_FIELD
EXTREME_BREATHING_FIELD
SOFT_BREATHING_FIELD
TEMPORAL_DENSITY_FIELD
HIGH_TEMPORAL_COMPRESSION_FIELD
SOFT_TEMPORAL_DENSITY_FIELD
ANGULAR_ALIGNMENT_NODE
SAME_ANGLE_INTENTION_NODE
TEMPORAL_TARGETS
TEMPORAL_ROWS
TACTICAL_RELEASE_BATTLEFIELD
HTF_PREPARATION_FIELD
CONTESTED_WINDOW
BIPOLAR_CONTESTED_RELEASE_WINDOW
BIPOLAR_FOCUS
BIPOLAR_LIST
MICRO_VS_HTF_ROTATION_CONTEST
HIGH_COALITION
LOW_COALITION
DUAL_SIDE_FIELD
RELEASE_PRESENT
PREPARATION_PRESENT
MICROFILM_PRESENT
HTF_ANCHOR_PRESENT
```

Verdict :

```text
Lexique Cockpit Field + Temporal Patterns mis à jour.
```
