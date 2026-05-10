# PATCH LEXIQUE — Gravity / Zones / Structural Footprints — PowerFlow V7.2

**Date :** 2026-05-10  
**Statut :** Patch lexique V0.1 — à intégrer avant Lab Engine V7.2

---

## 1. B5_SPEARMAN_RELATIONAL_COHERENCE

Nouveau nom sémantique recommandé pour B5.

Définition :

```text
Capteur statistique de cohérence relationnelle entre devises,
basé sur Spearman rho rolling.
```

Produit :

```text
spearman_rho
SYNCHRO
DIVERGENT
NEUTRAL
CODEPENDANT_EXTREME
DIVERGENT_EXTREME
MIXED_PROBABILISTE
avg_rho
```

Ne produit pas :

```text
leader
follower
direction de trade
flux institutionnel certain
```

---

## 2. GRAVITY_ORGANIQUE

Organisation vivante du groupe de devises.

Inclut :

```text
relation
lead / lag
coalition
antagonisme
fragmentation
centre de gravité
compression orchestrale
```

Ne doit pas être réduite à Spearman.

---

## 3. LEAD_LAG_GRAVITY

Sous-couche de Gravity mesurant l’avance ou le retard comportemental d’une devise.

Mesures possibles :

```text
première inflexion
première accélération
propreté de pente
rattrapage
décrochage
B7 LAGGED
M1/M5 desync
```

---

## 4. FIELD_STRUCTURE_GRAVITY

Structure globale du champ de devises.

États possibles :

```text
FIELD_ALIGNED
FIELD_FRAGMENTED
FIELD_NEUTRAL
FIELD_FRICTIONAL
FIELD_COALITION_ACTIVE
FIELD_ANTAGONIST_ACTIVE
```

---

## 5. DYNAMIC_ZONE

Espace de tension comportemental.

Ne pas confondre avec support/résistance.

Une dynamic zone peut :

```text
se charger
respirer
absorber
rejeter
libérer
fatiguer
devenir node
```

---

## 6. BATTLEFIELD_ZONE

Zone dynamique située dans une hiérarchie multi-TF.

Mapping :

```text
H4  = champ de bataille stratégique
H1  = traducteur
M15 = battle window
M5  = relais tactique
M1  = ignition / microfilm
```

---

## 7. ZONE_REACTION

Réaction du flux dans une zone.

Types :

```text
ZONE_ABSORPTION
ZONE_REPULSION
ZONE_BREATH
ZONE_STALL
ZONE_RELEASE
ZONE_RETEST
```

---

## 8. EIE_ACTIVE_ZONE

Zone où l’élastique est actif.

Croisement :

```text
zone z-score
TF1/TF5 elastic
fractalité TF15/30/60
```

États liés :

```text
EIE
EWZ
ENZ
ZNE
```

---

## 9. NODE_AS_ZONE_MEMORY

Un node est une zone qui commence à avoir une mémoire comportementale.

Le node accumule :

```text
réactions répétées
absorptions
rejets
compressions
micro-inflexions
```

---

## 10. STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE

Empreinte comportementale compatible avec un flux structuré.

Remplace les termes trop affirmatifs :

```text
institution detected
smart money detected
bank buying
```

Conditions possibles :

```text
zone dynamique active
B1 cohérent
B3 noise faible
B4 compression réelle
B5 relation non neutre
EIE actif
B7 propagation
B6 scènes similaires
```

---

## 11. ABSORPTION_FOOTPRINT

Empreinte d’absorption.

Signature :

```text
pullback absorbé
retour sans reprise adverse propre
B3 noise contrôlé
zone active
B5 relation non neutre
```

---

## 12. ZONE_DEFENSE_FOOTPRINT

Empreinte de défense de zone.

Signature :

```text
réactions répétées autour d’une zone
absence de passage propre
contre-flux absorbé
node actif
```

---

## 13. CLEAN_REPULSION_FOOTPRINT

Empreinte de répulsion propre.

Signature :

```text
EIE actif
B3 retournement propre
B3 noise faible
B5 confirme
B4 stable ou expanding après compression
```

---

## 14. DELAYED_CATCH_UP_FOOTPRINT

Empreinte de retard prix puis rattrapage.

Signature :

```text
B5 / B3 bougent avant le prix
B7 LAGGED
B4 compressing puis expanding
prix rattrape ensuite
```

---

## 15. LEADER_ACCUMULATION_FOOTPRINT

Empreinte d’accumulation d’un leader.

Signature :

```text
une devise inflecte avant les autres
B3 pente propre
B5 relation non neutre
followers en retard
B7 lag ou résonance progressive
```

---

## 16. RELATIONAL_PRESSURE_FOOTPRINT

Pression relationnelle visible dans le champ.

Signature :

```text
B5 DIVERGENT_EXTREME
ou CODEPENDANT_EXTREME
mais uniquement qualifiée par B1/B3/B4/EIE
```

---

## 17. COMPRESSION_REAL_CANDIDATE

Compression possiblement structurelle.

Conditions :

```text
B4 CYCLE_COMPRESSING
B1 COMPRESSION ou TRANSITION
B5 non neutre / extrême
EIE actif
B3 noise faible
```

---

## 18. COMPRESSION_FAKE_RISK

Compression possiblement fausse ou bruitée.

Conditions :

```text
B4 CYCLE_COMPRESSING
B1 RANGE
B5 NEUTRAL
EIE absent
B3 noise élevé
```

---

## 19. INFERENCE_ONLY

Risque technique obligatoire quand une empreinte structurée est détectée sans volume/orderbook.

Usage :

```text
STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE + INFERENCE_ONLY
```

---

## 20. RÈGLE ANTI-BLUFF INSTITUTIONNEL

Interdit :

```text
INSTITUTION_DETECTED
BANKS_BUYING
SMART_MONEY_SELLING
```

Autorisé :

```text
STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE
INFERENCE_ONLY
NO_VOLUME_DATA
NO_ORDERBOOK_DATA
```

---

## 21. RÈGLE LEXIQUE LAB V7.2

Le futur Lab doit dire :

```text
observed
measured
candidate
footprint
technical_risks
outcome observed
```

Il ne doit pas dire :

```text
trade valid
signal certain
institution confirmed
direction guaranteed
```

---

## 22. Phrase lexique

```text
Gravity organise le groupe.
Zone concentre la tension.
B3 montre la réaction.
B4 montre la respiration.
B5 montre la relation.
EIE montre l’élastique.
B6 se souvient.
B7 montre la propagation.

Le flux structuré laisse des empreintes.
PowerFlow les nomme comme candidates.
Le trader juge.
```
