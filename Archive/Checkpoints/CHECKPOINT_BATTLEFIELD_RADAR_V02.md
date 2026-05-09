# CHECKPOINT_BATTLEFIELD_RADAR_V02

**Projet :** PowerFlow V6  
**Brique :** Battlefield Radar / Vue globale des batailles en préparation  
**Version validée :** V0.2  
**Statut :** VALIDÉE terrain sur `powerflow.db`  
**Nature :** Lecture cockpit read-only des scènes d’intérêt stratégique

---

## 1. Résumé court

`pf_battlefield_radar.py V0.2` transforme les sorties coalition/relation en vue globale cockpit.

Il ne dit pas :

```text
la fenêtre temporelle est ouverte
```

Il dit :

```text
ici, une bataille se prépare
ici, une coalition forte mérite surveillance
```

Phrase noyau :

```text
BattlefieldRadar ne dit pas “la fenêtre est ouverte”.
Il dit “ici, une bataille se prépare”.
```

---

## 2. Brique validée

Fichiers actifs attendus :

```text
pf_battlefield_radar.py              ← V0.2
run_battlefield_radar_once.py        ← V0.2
test_pf_battlefield_radar_v02.py
```

Dépendances déjà validées :

```text
run_zone_context_logger_once.py      ← V0.1.1 basket
run_coalition_relations_once.py      ← V0.3
pf_coalitions.py                     ← V0.1
pf_coalition_relations.py            ← V0.1
```

---

## 3. Position dans l’écosystème

```text
pf_personalities.py
→ identité comportementale individuelle

pf_zone_dynamics.py
→ respiration de zone

pf_zone_context_logger.py
→ mémoire DB

pf_coalitions.py
→ familles de devises

pf_coalition_relations.py
→ coalition vs antagoniste

pf_battlefield_radar.py
→ batailles en préparation / scènes d’intérêt cockpit

pf_temporal_density.py
→ future compression / extension du temps

pf_temporal_window_active.py
→ future fenêtre active
```

---

## 4. Commandes validées

### Test module

```bat
python test_pf_battlefield_radar_v02.py
```

Résultat validé :

```text
OK pf_battlefield_radar V0.2
Radar: bataille relationnelle prioritaire — [TF15] AUD+CAD vs JPY
```

### Radar global

```bat
python run_battlefield_radar_once.py --db powerflow.db --scan 240
```

### Radar ciblé

```bat
python run_battlefield_radar_once.py --db powerflow.db --timeframes 1,15,30 --scan 240
```

---

## 5. Résultat terrain principal

Sortie validée :

```text
Radar: bataille relationnelle prioritaire —
[TF30] AUD+GBP vs EUR —
BATTLE_FORMING /
COALITION_VS_ANTAGONIST_OPPOSITION /
field=0.60
```

Top relations actives :

```text
TF30 — AUD+GBP vs EUR — field=0.60
TF15 — AUD+CAD vs JPY — field=0.57
TF15 — CAD+GBP vs JPY — field=0.54
TF15 — CHF+GBP vs JPY — field=0.52
```

Coalitions fortes ensuite :

```text
TF1  — GBP+JPY — HIGH_PRESSURE_COALITION_EXPANDING — cohesion=0.90
TF1  — CHF+EUR — HIGH_PRESSURE_COALITION_FOLDING — cohesion=0.94
TF15 — AUD+GBP — HIGH_COALITION_FALLING — cohesion=0.92
TF15 — AUD+CHF — HIGH_COALITION_FALLING — cohesion=0.89
```

---

## 6. Correction V0.2 vs V0.1

V0.1 voyait bien les scènes, mais classait trop haut les coalitions fortes seules.

V0.2 corrige :

```text
1. Relations actives prioritaires devant coalitions isolées.
2. Déduplication des familles répétées.
3. Ajout de strategic_score.
4. Lecture cockpit plus propre.
```

Doctrine corrigée :

```text
Relation active moyenne > coalition isolée forte
```

Parce qu’une relation active contient :

```text
coalition
+ antagoniste
+ opposition de champ
```

Alors qu’une coalition forte seule dit seulement :

```text
famille synchronisée, bataille incomplète
```

---

## 7. États radar

```text
BATTLE_WATCH
BATTLE_PREPARING
BATTLE_FORMING
BATTLE_PRESSURIZED
COALITION_FIELD_WATCH
COALITION_FIELD_VISIBLE
COALITION_FIELD_STRONG
```

---

## 8. Types de scènes

```text
RELATION_ACTIVE
COALITION_STRONG
```

---

## 9. Scores

```text
field_score
→ force relationnelle coalition vs antagoniste

cohesion
→ force interne d’une coalition

strategic_score
→ score radar pour tri cockpit
```

Règle V0.2 :

```text
relation active prioritaire dans le tri
coalition forte conservée mais rangée après
```

---

## 10. Limites connues

La brique ne fait pas encore :

```text
- TemporalDensity
- TemporalWindowActive
- compression du temps
- ouverture de fenêtre
- alerte Telegram
- écriture DB
```

Elle prépare seulement :

```text
la carte des scènes d’intérêt stratégique
```

---

## 11. Prochaine suite naturelle

Pas coder tout de suite si non stabilisé.

Mais la suite logique future :

```text
pf_temporal_density.py
→ mesurer si les scènes radar se compressent dans le temps

pf_temporal_window_active.py
→ déclarer plus tard la fenêtre active si densité + champ + cohérence s’alignent
```

---

## 12. Verdict

```text
pf_battlefield_radar.py V0.2 = VALIDÉE
```

Le cockpit peut maintenant avoir une vue globale des batailles en préparation.

Fin du checkpoint.
