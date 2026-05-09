# MISE À JOUR LEXIQUE — PowerFlow V6 — Personality Foundation → Radar

**Date :** 2026-05-03  
**Statut :** À intégrer dans `LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md`  
**Périmètre :** Personality Foundation, Zone Bridge, Coalitions, CoalitionRelations, BattlefieldRadar  
**Chantier validé :** `codex/personality-foundation-v01`

---

# 1. Nouvelle famille lexicale : PERSONALITY FOUNDATION

## DEVISE_PERSONALITY

**Définition :**  
Profil natif d’une devise dans PowerFlow. Une devise n’est plus seulement une courbe de force : c’est un acteur avec un tempo, une amplitude normale, un rôle, une classe de volatilité et éventuellement une relation follower/lag avec une autre devise.

**Champs principaux :**

```text
devise
tempo_tf
amplitude_norm
lag_ref
lag_bars
volatility_class
role
```

**Exemple :**

```text
JPY = rapide, ample, REFUGE, HIGH volatility
USD = pivot, tempo lent, PIVOT, MEDIUM volatility
CHF = refuge lent, LOW volatility, follower possible de JPY
```

**Règle Flow :**

```text
Une devise doit être lue selon sa respiration native.
Comparer JPY et CHF comme deux acteurs identiques crée du bruit.
```

---

## DEVISE_PROFILE

**Définition :**  
Instance concrète d’une `DevisePersonality`.

**Usage :**

```text
Permet de calibrer les moteurs sans imposer de seuil fixe universel.
```

**Exemples de profils :**

```text
JPY : tempo_tf=5, amplitude_norm=18, role=REFUGE, volatility_class=HIGH
EUR : tempo_tf=15, amplitude_norm=4, role=RISK, volatility_class=MEDIUM
GBP : tempo_tf=15, amplitude_norm=5, role=RISK, volatility_class=MEDIUM
USD : tempo_tf=30, amplitude_norm=3, role=PIVOT, volatility_class=MEDIUM
CAD : tempo_tf=15, amplitude_norm=4, role=PIVOT, lag_ref=USD
AUD : tempo_tf=5, amplitude_norm=6, role=RISK, volatility_class=HIGH
NZD : tempo_tf=15, amplitude_norm=5, role=RISK, lag_ref=AUD
CHF : tempo_tf=30, amplitude_norm=3, role=REFUGE, lag_ref=JPY
```

---

## TEMPO_TF

**Définition :**  
Timeframe natif approximatif où la devise exprime le mieux sa respiration comportementale.

**Lecture Flow :**

```text
JPY peut respirer vite.
USD peut peser plus lentement.
CHF peut réagir avec inertie.
```

**Usage :**

```text
Le tempo_tf ne décide pas seul.
Il calibre la lecture temporelle.
```

---

## AMPLITUDE_NORM

**Définition :**  
Amplitude comportementale normale d’une devise sur son tempo natif.

**Rôle :**

```text
Distinguer une devise naturellement nerveuse d’une devise réellement en tension.
```

**Exemple :**

```text
Un mouvement fort sur EUR peut être plus significatif qu’un mouvement équivalent sur JPY,
car JPY a une amplitude native plus élevée.
```

---

## VOLATILITY_CLASS

**Définition :**  
Classe qualitative de volatilité native.

**Valeurs :**

```text
HIGH
MEDIUM
LOW
```

**Usage :**

```text
Aide à calibrer les compatibilités de coalition.
```

**Exemple :**

```text
JPY / AUD = HIGH
EUR / GBP / USD / CAD / NZD = MEDIUM
CHF = LOW
```

---

## ROLE

**Définition :**  
Rôle comportemental principal d’une devise dans le champ PowerFlow.

**Valeurs :**

```text
RISK
REFUGE
PIVOT
```

**Lecture :**

```text
RISK   = acteur de mouvement / appétit / rotation
REFUGE = acteur défensif / refuge / absorption
PIVOT  = acteur gravitationnel / axe de comparaison
```

---

## PIVOT_ROLE

**Définition :**  
Rôle d’une devise qui sert de centre gravitationnel ou d’axe relationnel.

**Exemples :**

```text
USD
CAD dans certains contextes
```

**Règle Flow :**

```text
Un antagoniste PIVOT ne se lit pas comme un simple opposant.
Il peut peser sur tout le champ.
```

---

## REFUGE_ROLE

**Définition :**  
Rôle d’une devise défensive, souvent associée à protection, absorption ou rotation refuge.

**Exemples :**

```text
JPY
CHF
```

**Règle Flow :**

```text
Une coalition RISK contre un REFUGE peut ouvrir une bataille structurelle lisible.
```

---

## RISK_ROLE

**Définition :**  
Rôle d’une devise orientée mouvement, rotation, appétit ou extension.

**Exemples :**

```text
EUR
GBP
AUD
NZD
```

**Règle Flow :**

```text
Une coalition RISK cohérente peut devenir un bloc moteur.
```

---

## LAG_REF

**Définition :**  
Devise de référence suivie par une autre devise avec retard comportemental.

**Exemples :**

```text
NZD peut suivre AUD
CAD peut suivre USD
CHF peut suivre JPY
```

**Règle Flow :**

```text
Un lag_ref ne crée pas un signal.
Il indique une relation comportementale spéciale à surveiller.
```

---

## LAG_BARS

**Définition :**  
Nombre approximatif de barres de retard entre une devise follower et sa référence.

**Usage :**

```text
Permet de repérer une réponse différée.
```

---

# 2. Nouvelle famille lexicale : PERSONALITY BRIDGE

## PERSONALITY_BRIDGE

**Définition :**  
Connexion légère entre `pf_personalities.py` et une autre brique moteur.

**Règle fondamentale :**

```text
Personality calibre.
Personality ne domine pas.
```

**Briques actuellement branchées :**

```text
pf_zone_dynamics.py
pf_coalitions.py
pf_coalition_relations.py
pf_battlefield_radar.py
```

---

## PERSONALITY_CALIBRATION

**Définition :**  
Ajustement léger d’un score existant grâce aux profils natifs des devises.

**Principe :**

```text
Le score brut reste maître.
La personnalité ajoute une correction bornée.
```

**Exemples :**

```text
cohesion coalition : ajustement environ ±0.08
field_score relation : ajustement environ ±0.07
strategic_score radar : ajustement environ ±0.08
```

---

## PERSONALITY_DOES_NOT_DOMINATE

**Définition :**  
Règle de protection architecturale.

**Formule :**

```text
Personality n’a pas le droit de transformer la nature d’une scène.
Elle ne fait que mieux calibrer son intensité.
```

**Exemple :**

```text
Une coalition faible ne devient pas une bataille active juste parce que ses rôles sont compatibles.
```

---

## PROFILE_SAFE_ACCESS

**Définition :**  
Accès robuste au profil d’une devise.

**Comportement :**

```text
devise inconnue → None
erreur profil → None
devise lowercase → uppercase
```

**Usage :**

```text
Évite qu’un module moteur casse sur une devise absente ou future.
```

---

# 3. Nouvelle famille lexicale : COALITION PERSONALITY

## COALITION_PERSONALITY_COMPATIBILITY

**Définition :**  
Score de compatibilité native entre deux devises dans une coalition.

**Sous-composants :**

```text
volatility_compatibility_score
role_compatibility_score
tempo_compatibility_score
```

**Règle Flow :**

```text
Deux devises qui respirent avec un rôle, un tempo ou une volatilité compatible
peuvent former une coalition plus lisible.
```

---

## VOLATILITY_COMPATIBILITY_SCORE

**Définition :**  
Mesure la compatibilité des classes de volatilité entre deux devises.

**Lecture :**

```text
HIGH/HIGH ou MEDIUM/MEDIUM = compatible
HIGH/LOW = plus difficile
MEDIUM/HIGH ou MEDIUM/LOW = intermédiaire
```

---

## ROLE_COMPATIBILITY_SCORE

**Définition :**  
Mesure la compatibilité des rôles natifs dans une coalition.

**Lecture :**

```text
RISK + RISK = bloc moteur cohérent
REFUGE + REFUGE = bloc défensif cohérent
RISK + PIVOT = relation structurelle intermédiaire
RISK + REFUGE = coalition plus ambiguë
```

---

## TEMPO_COMPATIBILITY_SCORE

**Définition :**  
Mesure l’écart entre les tempos natifs de deux devises.

**Lecture :**

```text
tempo proche = meilleure coalition
tempo très éloigné = coalition moins naturelle
```

---

## PERSONALITY_COMPATIBILITY_SCORE

**Définition :**  
Score agrégé `[0..1]` de compatibilité entre deux devises.

**Formule actuelle :**

```text
0.35 * volatility
+ 0.35 * role
+ 0.30 * tempo
```

**Usage :**

```text
Calibrer légèrement la cohesion dans pf_coalitions.py.
```

---

## COALITION_PERSONALITY_CALIBRATION

**Définition :**  
Ajustement de la cohésion d’une coalition par sa compatibilité native.

**Principe :**

```text
base cohesion = z/slope/curvature/tags
personality ajuste légèrement
```

**Règle :**

```text
Une coalition compatible devient plus lisible.
Une coalition incompatible reste possible, mais moins forte.
```

---

# 4. Nouvelle famille lexicale : RELATION PERSONALITY

## RELATION_PERSONALITY_SCORE

**Définition :**  
Score de compatibilité/opposition comportementale entre une coalition et son antagoniste.

**Sous-composants :**

```text
role_opposition_score
pivot_gravity_score
refuge_opposition_score
lag_relation_score
```

**Usage :**

```text
Calibrer légèrement le field_score dans pf_coalition_relations.py.
```

---

## ROLE_OPPOSITION_SCORE

**Définition :**  
Mesure la qualité structurelle de l’opposition entre les rôles de la coalition et de l’antagoniste.

**Exemples :**

```text
RISK coalition vs REFUGE antagonist
REFUGE coalition vs RISK antagonist
RISK coalition vs PIVOT antagonist
```

**Lecture Flow :**

```text
Toutes les oppositions numériques ne se valent pas.
Le rôle des acteurs donne une qualité de bataille.
```

---

## PIVOT_GRAVITY_SCORE

**Définition :**  
Score qui mesure le poids gravitationnel d’un antagoniste PIVOT.

**Règle :**

```text
USD antagoniste reçoit une gravité spécifique.
```

**Lecture :**

```text
USD n’est pas seulement une devise adverse.
Il est souvent l’axe du champ.
```

---

## REFUGE_OPPOSITION_SCORE

**Définition :**  
Score qui mesure l’opposition entre acteurs RISK et REFUGE.

**Lecture :**

```text
Une bataille RISK vs REFUGE peut signaler rotation, protection, fuite ou rééquilibrage.
```

---

## LAG_RELATION_SCORE

**Définition :**  
Score qui détecte une relation follower/leader à travers la frontière coalition-antagoniste.

**Exemple :**

```text
Si CAD suit USD,
ou si CHF suit JPY,
la relation peut être plus structurée.
```

**Règle :**

```text
Le lag n’est pas un signal.
C’est une mémoire comportementale.
```

---

## FIELD_SCORE_PERSONALITY_CALIBRATION

**Définition :**  
Correction légère du field_score par `personality_relation_score`.

**Formule actuelle :**

```text
base_field_score = opposition_score * 0.55 + timing_score * 0.45
field_score = base_field_score + ((personality_score - 0.5) * 0.14)
```

**Bornage :**

```text
[0, 1]
```

**Règle :**

```text
Opposition + timing restent dominants.
Personality ajoute la qualité structurelle de la bataille.
```

---

# 5. Nouvelle famille lexicale : RADAR PERSONALITY

## RADAR_PERSONALITY_WEIGHT

**Définition :**  
Poids léger utilisé par le BattlefieldRadar pour calibrer le `strategic_score`.

**Sous-composants :**

```text
antagonist_role_weight
coalition_role_mix_weight
timeframe_personality_weight
```

**Bornage :**

```text
[-0.08, +0.08]
```

---

## ANTAGONIST_ROLE_WEIGHT

**Définition :**  
Poids radar associé au rôle de l’antagoniste principal.

**Lecture :**

```text
PIVOT antagoniste = poids stratégique plus fort
USD = gravité spéciale
REFUGE = poids défensif
RISK = poids dynamique
```

---

## COALITION_ROLE_MIX_WEIGHT

**Définition :**  
Poids radar lié à la cohérence de rôle dans la coalition principale.

**Lecture :**

```text
coalition majoritairement RISK = bloc moteur plus clair
coalition majoritairement REFUGE = bloc défensif plus clair
coalition mixte = plus ambiguë
```

---

## TIMEFRAME_PERSONALITY_WEIGHT

**Définition :**  
Poids radar qui compare le timeframe de la scène au tempo natif moyen des acteurs.

**Lecture :**

```text
scène proche du tempo natif = plus lisible
scène très éloignée du tempo natif = calibration plus faible
```

---

## STRATEGIC_SCORE_PERSONALITY_CALIBRATION

**Définition :**  
Ajustement léger du strategic_score radar selon les profils natifs.

**Principe relation active :**

```text
base = 1.0 + field_score
+ radar_personality_weight
```

**Principe coalition isolée :**

```text
base = formule V0.2 existante
+ radar_personality_weight
+ léger biais bas
```

---

## RELATION_FIRST_PRIORITY

**Définition :**  
Règle radar V0.2 préservée.

**Formule Flow :**

```text
Une relation active moyenne vaut plus qu’une coalition isolée forte.
```

**Raison :**

```text
Une relation contient une confrontation lisible.
Une coalition seule est une scène d’intérêt, pas encore une bataille complète.
```

---

## COALITION_ONLY_BIAS_DOWN

**Définition :**  
Petit biais négatif appliqué aux scènes `COALITION_STRONG` pour préserver la priorité des relations actives.

**Règle :**

```text
Une coalition forte reste visible.
Elle ne doit pas masquer une bataille relationnelle active.
```

---

# 6. Clarifications de grammaire Flow

## ACTEUR

**Définition :**  
Devise lue comme entité comportementale, pas seulement comme série numérique.

**Phrase :**

```text
PowerFlow ne lit plus seulement des forces.
Il lit des acteurs.
```

---

## IDENTITÉ COMPORTEMENTALE

**Définition :**  
Ensemble des propriétés natives d’une devise :

```text
tempo
amplitude
rôle
volatilité
lag éventuel
```

---

## QUALITÉ STRUCTURELLE

**Définition :**  
Dimension qualitative d’un mouvement ou d’une bataille, issue des rôles des acteurs.

**Exemple :**

```text
EUR+GBP vs USD n’est pas seulement un z-score opposé.
C’est un bloc RISK face à un PIVOT.
```

---

## GRAVITÉ USD

**Définition :**  
Poids spécifique d’USD comme antagoniste PIVOT.

**Règle :**

```text
USD peut organiser le champ autour de lui.
```

---

## BLOC RISK

**Définition :**  
Coalition majoritairement composée de devises `RISK`.

**Exemples :**

```text
EUR+GBP
AUD+GBP
EUR+AUD
```

**Lecture :**

```text
Bloc moteur / rotation / appétit / extension.
```

---

## BLOC REFUGE

**Définition :**  
Coalition majoritairement composée de devises `REFUGE`.

**Exemples :**

```text
JPY+CHF
```

**Lecture :**

```text
Bloc défensif / absorption / protection / rééquilibrage.
```

---

## BATAILLE STRUCTURELLE

**Définition :**  
Relation où les scores numériques et les rôles natifs se renforcent.

**Exemple :**

```text
RISK coalition vs PIVOT antagonist
RISK coalition vs REFUGE antagonist
REFUGE coalition vs RISK antagonist
```

---

## SCÈNE D’INTÉRÊT

**Définition :**  
Zone radar visible mais pas forcément fenêtre active.

**Exemple :**

```text
COALITION_FIELD_STRONG
COALITION_FIELD_VISIBLE
BATTLE_PREPARING
BATTLE_FORMING
```

---

## FENÊTRE ACTIVE

**Définition :**  
État non encore codé dans ce chantier.

**Règle :**

```text
BattlefieldRadar ne déclare pas la fenêtre active.
Il prépare le cockpit à la voir.
```

---

# 7. Corrections conceptuelles à retenir

## Avant

```text
Une coalition était surtout évaluée par proximité z/slope/curvature/tags.
Une relation était surtout évaluée par opposition/timing.
Le radar classait surtout par field_score/cohesion.
```

## Maintenant

```text
Une coalition est aussi calibrée par compatibilité native.
Une relation est aussi calibrée par rôle/pivot/refuge/lag.
Le radar est aussi calibré par rôle de l’antagoniste, mix de coalition et tempo.
```

---

# 8. Nouvelles phrases de doctrine

```text
Personality donne l’identité.
Zone donne l’état.
Coalition donne le bloc.
Relation donne la bataille.
Radar donne la priorité cockpit.
```

```text
Une devise n’est pas une ligne.
C’est un acteur avec un tempo, un rôle et une mémoire.
```

```text
Une coalition n’est pas seulement une synchronisation.
C’est un bloc d’acteurs compatibles ou temporairement alignés.
```

```text
Une relation n’est pas seulement une opposition.
C’est une bataille entre rôles.
```

```text
Un radar ne prédit pas l’entrée.
Il hiérarchise le champ de bataille.
```

---

# 9. Nouvelles entrées courtes pour lexique principal

```text
DEVISE_PERSONALITY
Profil natif d’une devise : tempo, amplitude, rôle, volatilité, lag.

PERSONALITY_BRIDGE
Connexion légère entre le profil devise et une brique moteur.

PERSONALITY_CALIBRATION
Ajustement borné d’un score existant par la personnalité native.

ROLE_COMPATIBILITY_SCORE
Mesure la compatibilité de rôles entre deux devises.

TEMPO_COMPATIBILITY_SCORE
Mesure l’alignement entre tempos natifs.

VOLATILITY_COMPATIBILITY_SCORE
Mesure l’alignement des classes de volatilité.

PERSONALITY_COMPATIBILITY_SCORE
Score agrégé de compatibilité entre deux devises.

ROLE_OPPOSITION_SCORE
Mesure la qualité structurelle d’une opposition coalition/antagoniste.

PIVOT_GRAVITY_SCORE
Poids d’un antagoniste PIVOT, surtout USD.

REFUGE_OPPOSITION_SCORE
Qualité d’une opposition impliquant des rôles REFUGE.

LAG_RELATION_SCORE
Mesure une relation follower/leader entre coalition et antagoniste.

PERSONALITY_RELATION_SCORE
Score de calibration d’une relation par rôles/pivot/refuge/lag.

RADAR_PERSONALITY_WEIGHT
Poids léger injecté dans le strategic_score radar.

ANTAGONIST_ROLE_WEIGHT
Poids radar lié au rôle de l’antagoniste.

COALITION_ROLE_MIX_WEIGHT
Poids radar lié à la cohérence de rôle dans une coalition.

TIMEFRAME_PERSONALITY_WEIGHT
Poids radar lié à l’alignement timeframe/tempo natif.

RELATION_FIRST_PRIORITY
Règle : une relation active moyenne reste prioritaire sur une coalition isolée forte.

COALITION_ONLY_BIAS_DOWN
Biais léger pour éviter qu’une coalition seule masque une relation active.

STRUCTURAL_BATTLE
Bataille où scores numériques et rôles natifs se renforcent.

USD_GRAVITY
Poids spécifique d’USD comme pivot du champ.

RISK_BLOCK
Coalition majoritairement RISK.

REFUGE_BLOCK
Coalition majoritairement REFUGE.
```

---

# 10. Statut d’intégration

Cette mise à jour correspond aux commits validés :

```text
ca79492 — Personality Foundation
39a2b86 — Coalition Personality Bridge
3f052a6 — CoalitionRelations Personality Bridge
03f08ca — BattlefieldRadar Personality Bridge
```

Statut :

```text
À intégrer dans le lexique principal PowerFlow.
Compatible avec le checkpoint Personality → Radar V01.
```
