# AUDIT SÉMANTIQUE — Gravity / Zones / Footprints — PowerFlow V7.2

**Date :** 2026-05-10  
**Statut :** Audit sémantique V0.1 — avant codage du Lab Engine V7.2  
**Objectif :** Verrouiller la grammaire PowerFlow autour de Gravity, Zones dynamiques, champ de bataille et empreintes de flux structurés avant de construire le nouveau Lab.

---

## 1. Décision d’audit

Le nouveau Lab Engine V7.2 ne doit pas être codé avant clarification sémantique.

Raison :

```text
Un Lab peut mesurer très proprement une mauvaise grammaire.
Si Gravity, Zone ou Institutional Footprint sont mal définis,
le Lab donnera des rapports propres mais conceptuellement faux.
```

Décision :

```text
Audit Gravity/Zones/Footprints d’abord.
Lab Engine V7.2 ensuite.
```

---

## 2. Sources doctrinales

Le Manifeste PowerFlow V7 définit PowerFlow comme un moteur de perception, pas de décision. Il mesure, nomme, alerte et laisse le trader décider.

Il définit aussi cinq niveaux de perception :

```text
Niveau 1 — Cinématique
Niveau 2 — Zone
Niveau 3 — Densité Temporelle
Niveau 4 — Gravité Relationnelle
Niveau 5 — Régime HTF
```

Points fondamentaux :

```text
Zone = espace de tension.
Densité = comportement des cycles.
Gravité relationnelle = organisation des devises entre elles.
Régime = contexte HTF qui change le sens d’un même signal.
```

---

## 3. Diagnostic principal

La couche Gravity actuelle risque d’avoir été réduite à B5 Spearman.

Or :

```text
B5 Spearman = capteur relationnel statistique.
Gravity organique = organisation vivante du groupe de devises.
```

Il faut donc séparer :

```text
1. Corrélation / relation paire-à-paire
2. Leadership / follower / lag
3. Structure de champ / coalitions / antagonistes
4. Confluence zone + régime + relation + cinématique
```

---

## 4. Audit Gravity — séparation nécessaire

### 4.1 B5 Spearman Relation

Rôle correct :

```text
Mesurer la cohérence relationnelle entre deux devises.
```

Sorties correctes :

```text
spearman_rho
SYNCHRO
DIVERGENT
NEUTRAL
CODEPENDANT_EXTREME
DIVERGENT_EXTREME
MIXED_PROBABILISTE
avg_rho multi-TF
```

B5 peut dire :

```text
GBP et USD bougent ensemble.
GBP et CAD sont en opposition.
La relation est extrême.
La relation est neutre.
```

B5 ne doit PAS dire seul :

```text
GBP est leader.
USD est follower.
Une institution achète.
Le flux va dans telle direction.
Le trade est valide.
```

### 4.2 Lead / Lag Gravity

Couche à séparer ou auditer.

Elle doit mesurer :

```text
qui inflecte en premier
qui accélère en premier
qui garde la pente la plus propre
qui rattrape
qui décroche
qui impose la séquence temporelle
```

Sources possibles :

```text
B3 angle_kalman
B3 speed_magnitude
B3 noise_ratio
B7 lag / resonance
B5 relation
Multi-TF timing
```

### 4.3 Field Structure Gravity

Couche plus large.

Elle doit représenter :

```text
coalitions
antagonistes
centre de gravité
fragmentation du champ
champ neutre
champ frictionnel
champ aligné
```

Cette couche ne doit pas être confondue avec une simple paire Spearman.

### 4.4 Confluence Gravity

Elle fusionne :

```text
EIE × B1 × B5 × RG
```

Elle doit donc être lue comme une couche de synthèse, pas comme une source primaire unique.

---

## 5. Audit Zones dynamiques

### 5.1 Définition

Une zone dynamique PowerFlow n’est pas un support/résistance classique.

Définition :

```text
Une zone dynamique est un espace de tension où le flux réagit,
se charge,
respire,
absorbe,
rejette,
ou libère.
```

Elle doit être comportementale, pas graphique.

### 5.2 Position dans l’architecture

Les zones dynamiques ne sont pas dans un B unique.

Elles sont transversales :

```text
Niveau 2 — Zone
pf_zone_dynamics.py
pf_temporal_node_state.py
pf_confluence_elastic.py
pf_confluence_gravity.py
```

Mapping correct :

```text
B1 = climat du champ
B2 = rythme événementiel autour du champ
B3 = réaction cinématique dans la zone
B4 = respiration temporelle autour de la zone
B5 = relation des forces autour de la zone
B6 = mémoire des réactions de zone
B7 = propagation / résonance de la réaction
EIE / Node = zone active / élastique / champ de bataille
```

### 5.3 États à vérifier

L’audit code doit vérifier si les états suivants existent réellement ou sont seulement conceptuels :

```text
ZONE_NEUTRAL
PRE_EXTREME
EARLY_EXTREME
ACCUMULATING
RUPTURE
EIE
EWZ
ENZ
ZNE
NODE_BIRTH
NODE_ACTIVE
NODE_REJECTED
ZONE_BREATH
ZONE_ABSORPTION
ZONE_REPULSION
```

---

## 6. Champ de bataille multi-TF

La hiérarchie stabilisée :

```text
W       mémoire profonde / biais structurel
D       cycle dominant
H4      zone de gravité / champ de bataille stratégique
H1      traducteur intraday
M30     scénario court
M15     battle window
M5      relais tactique
M1      microfilm / ignition / naissance
```

Le futur Lab V7.2 doit afficher la réaction du champ selon cette hiérarchie.

Questions à résoudre par audit :

```text
Comment une zone H4 descend-elle vers H1/M15/M5/M1 ?
Comment M1 peut-il alerter vite sans perdre le contexte H4 ?
Comment M5 confirme, relaie ou infirme M1 ?
Comment M15 devient battle window ?
Quelle couche nomme le champ de bataille actif ?
```

---

## 7. Empreintes de flux structurés / institutionnels

### 7.1 Règle anti-bluff

Ne jamais coder :

```text
INSTITUTION_DETECTED
SMART_MONEY_BUYING
BANKS_SELLING
```

PowerFlow ne voit pas directement les institutions.

Il peut seulement détecter des empreintes comportementales compatibles avec un flux structuré.

### 7.2 Terme recommandé

```text
STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE
```

Sous-types :

```text
ABSORPTION_FOOTPRINT
ZONE_DEFENSE_FOOTPRINT
CLEAN_REPULSION_FOOTPRINT
DELAYED_CATCH_UP_FOOTPRINT
LEADER_ACCUMULATION_FOOTPRINT
RELATIONAL_PRESSURE_FOOTPRINT
```

### 7.3 Conditions typiques

Une empreinte structurée candidate doit croiser plusieurs dimensions :

```text
zone dynamique active
B1 HTF cohérent
B3 noise faible ou contrôlé
B4 compression réelle ou expansion structurée
B5 relation non neutre
EIE actif ou pré-extrême
B7 propagation multi-TF
réactions répétées au même node
pullback absorbé
B6 retrouve des scènes similaires
```

### 7.4 Risques techniques obligatoires

```text
NO_VOLUME_DATA
NO_ORDERBOOK_DATA
SPREAD_NOT_AVAILABLE
INFERENCE_ONLY
LOW_SAMPLE_SIZE
LOW_TF_ALIGNMENT
B5_RELATION_UNCLEAR
EIE_ABSENT
B3_NOISE_HIGH
```

---

## 8. Doctrine B4 dans l’audit

B4 seul est insuffisant.

### Compression réelle

```text
B4 CYCLE_COMPRESSING
B1 COMPRESSION
B5 DIVERGENT_EXTREME ou relation non neutre
EIE actif
B3 noise faible

=> COMPRESSION_REAL_CANDIDATE
```

### Compression fake

```text
B4 CYCLE_COMPRESSING
B1 RANGE
B5 NEUTRAL
EIE absent
B3 noise élevé

=> COMPRESSION_FAKE_RISK
```

Règle :

```text
B4 voit la respiration.
B1 donne le climat.
B3 donne la propreté cinématique.
B5 donne le champ relationnel.
EIE donne l’élastique et la zone.
La scène naît dans le croisement.
```

---

## 9. Fichiers à auditer côté code

### Gravity

```text
Core/pf_spearman_gravity.py
Core/run_spearman_gravity_once.py
Core/pf_relational_gravity_bridge.py
Core/pf_relational_gravity_probe.py
Core/pf_orchestral_gravity_v02.py
Core/pf_confluence_gravity.py
Core/run_confluence_alert.py
```

Questions :

```text
B5 déduit-il leader/follower à tort ?
B5 utilise-t-il rho comme direction ?
B5 confond-il DIVERGENT avec signal exploitable ?
RG Bridge garde-t-il les TF details ?
Confluence Gravity distingue-t-elle EIE/B1/B5/RG ?
Orchestral Gravity est-il encore V6 ou intégré V7.2 ?
```

### Zones / Nodes

```text
Core/pf_zone_dynamics.py
Core/pf_temporal_node_state.py
Core/pf_confluence_elastic.py
Core/pf_flow_nodes.py
Core/pf_currency_energy_probe.py
```

Questions :

```text
Quels états de zone existent réellement ?
La zone est-elle comportementale ou simple seuil ?
EIE dépend-il bien de TF15 + TF1/TF5 + fractalité ?
Le Node Engine expose-t-il capture_quality / relay_quality / release_state ?
Les zones sont-elles reliées à B1/B3/B4/B5/B6/B7 ?
```

### Alertes / Mémoire / Dashboard

```text
Core/pf_behavioral_alert_mapper.py
Core/pf_memory_engine.py
Core/pf_scene_registry.py
Core/pf_memory_scene_enrichment.py
dashboard_live_v7.2.html
```

Questions :

```text
Les alertes reçoivent-elles bien regime_context ?
Les alertes exposent-elles les risques techniques ?
La mémoire reçoit-elle scene_id ?
Le dashboard affiche-t-il la scène et la compression réelle/fake ?
```

---

## 10. Red flags à chercher dans le code

### Gravity red flags

```text
rho -> leader
rho -> follower
rho -> BUY/SELL
rho -> trade direction
DIVERGENT -> opportunity
SYNCHRO -> valid
NEUTRAL -> ignore
institution detected
smart money
bank buying
```

### Zone red flags

```text
support
resistance
order block
supply demand
overbought / oversold
fixed threshold as truth
zone = price line only
```

### Architecture red flags

```text
pf_* importe cockpit_*
pf_* écrit dans powerflow.db
cockpit modifie queue
Lab écrit DB
module filtre une alerte précoce
```

---

## 11. Ce que le Lab V7.2 devra exiger après audit

Le Lab devra afficher :

```text
timeline multi-TF
zone active par TF
B1 / B3 / B4 / B5 / B7 au moment de la zone
scene_id
compression_qualification
memory_context B6
cause window -15m
event t0
consequence +5/+15/+30m
outcome observé
technical_risks
structural_flow_footprint_candidate si conditions réunies
```

Le Lab ne devra jamais produire :

```text
BUY
SELL
trade valid
trade invalid
should enter
should avoid
```

---

## 12. Décisions provisoires

### Décision 1

```text
B5 doit être renommé mentalement :
B5 Spearman Relational Coherence
```

Pas “Gravity totale”.

### Décision 2

```text
Gravity organique = B5 + lead/lag + field structure + confluence zone/régime.
```

### Décision 3

```text
Zone dynamique = couche transversale Niveau 2, pas support/résistance.
```

### Décision 4

```text
Institutionnel = empreinte candidate, jamais certitude.
```

### Décision 5

```text
Nouveau Lab V7.2 seulement après scan code et patch lexique.
```

---

## 13. Livrables audit attendus

```text
1. AUDIT_SEMANTIQUE_GRAVITY_ZONES_V72.md
2. PATCH_LEXIQUE_GRAVITY_ZONES_FOOTPRINT_V72.md
3. output/semantic_audit_gravity_zones_report.json
4. output/semantic_audit_gravity_zones_report.md
```

---

## 14. Phrase finale

```text
Gravity n’est pas une corrélation.
Zone n’est pas une ligne.
Institutionnel n’est pas une certitude.

PowerFlow doit mesurer des empreintes comportementales,
pas projeter des concepts classiques sur le flux.

Le Lab V7.2 ne doit pas expliquer le passé avec une mauvaise langue.
Il doit rejouer le champ avec la bonne grammaire.
```
