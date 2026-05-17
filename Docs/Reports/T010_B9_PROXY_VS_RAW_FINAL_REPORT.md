# T010 — B9 Proxy vs Raw — Final Official Report

**Projet :** PowerFlow V7 / T009 / B9  
**Brique :** B9 Microfilm Battlefield Memory  
**Mission :** T010 — première validation proxy M1 vs raw MT5  
**Branche cible :** `docs/t010-b9-proxy-vs-raw-first-validation`  
**Commit proposé :** `docs(t010): add B9 proxy vs raw first validation report`  
**Statut :** rapport officiel final prêt à intégrer.

---

## 0. Résumé exécutif

Cette mission valide la première confrontation officielle entre :

```text
M1_BAR_PROXY / RECONSTRUCTED
```

et :

```text
MT5 HISTORICAL_RAW / MT5_RAW_ALIGNED
```

sur GBPUSD, le 2026-05-15, entre 08:00 et 23:00.

Le résultat est structurellement positif :

```text
78 moments proxy analysés
57 confirmés par le raw
15 à recalibrer
6 raw unavailable
0 proxy-only dur
74 108 ticks raw alignés
```

Phrase de cap :

```text
Le proxy M1 raconte la scène.
Le raw MT5 vérifie la texture.
```

Cette phrase doit devenir la règle T010. Le proxy n'est pas rejeté. Le raw ne remplace pas tout. Les deux couches ont des rôles différents.

---

## 1. Sources et périmètre

### 1.1 Source proxy T009/B9

```text
source_mode        : M1_BAR_PROXY
data_visibility    : RECONSTRUCTED
symbole            : GBPUSD
fenêtre            : 2026-05-15 08:00–23:00
moments proxy      : 78
rôle analytique    : scène, structure, migration du centre, zones mémoire, effort/résultat.
```

Le proxy M1 est une reconstruction à partir de barres. Il permet de raconter le film local, mais il ne doit jamais être présenté comme une lecture tick-by-tick parfaite.

### 1.2 Source raw MT5

```text
source_mode        : MT5 HISTORICAL_RAW
data_visibility    : MT5_RAW_ALIGNED
DB raw             : tick_archive.db
sauvegarde         : tick_archive_T010_GBPUSD_20260515_RAW_OFFSET_PLUS3_VALIDATED.db
broker raw MT5     : OneFunded Capital Ltd.
raw après shift    : 2026-05-15 08:00:01 → 2026-05-15 22:59:58
ticks raw alignés  : 74 108
```

### 1.3 Alignement temporel

Offset validé :

```text
raw_ts_mt5 + 180 minutes = proxy_ts_mt4_approx
```

L'alignement utilisé est donc :

```text
offset = +3h
shift = 180 minutes
```

Ce point est crucial : sans correction temporelle, les comparaisons proxy/raw produisent des conclusions fausses.

---

## 2. Résultats chiffrés officiels

| Élément | Résultat |
|---|---:|
| DB raw | `tick_archive.db` |
| Backup raw validée | `tick_archive_T010_GBPUSD_20260515_RAW_OFFSET_PLUS3_VALIDATED.db` |
| Broker raw MT5 | `OneFunded Capital Ltd.` |
| Offset détecté | `raw_ts_mt5 + 180 minutes = proxy_ts_mt4_approx` |
| Data visibility raw | `MT5_RAW_ALIGNED` |
| Fenêtre proxy | GBPUSD 2026-05-15 08:00–23:00 |
| Raw après shift | 08:00:01 → 22:59:58 |
| Ticks raw alignés | 74 108 |
| Moments proxy | 78 |
| Confirmés raw | 57 |
| Recalibrage nécessaire | 15 |
| Raw unavailable | 6 |
| Proxy-only dur | 0 |

Ratios utiles :

```text
confirmés raw        : 57 / 78 ≈ 73.1 %
recalibrage          : 15 / 78 ≈ 19.2 %
raw unavailable      : 6 / 78 ≈ 7.7 %
proxy-only dur       : 0 / 78 = 0 %
```

---

## 3. Ce que le raw confirme

Le raw MT5 aligné confirme que le proxy M1 raconte majoritairement une scène réelle.

Confirmations importantes :

```text
- les zones de migration du centre ne sont pas inventées ;
- les paliers d'absorption proxy correspondent souvent à de vraies textures tick ;
- les moments progressifs majeurs restent visibles après comparaison raw ;
- les zones de digestion basse ou haute existent bien comme champs travaillés ;
- les changements de mémoire active sont globalement cohérents ;
- le proxy n'a pas généré de proxy-only dur.
```

La validation la plus forte est :

```text
proxy-only dur = 0
```

Cela signifie que le proxy n'a pas fabriqué une architecture de journée totalement absente de la donnée raw disponible.

---

## 4. Ce qui demande recalibrage

Les 15 moments à recalibrer indiquent que le proxy voit la scène, mais qu'il peut simplifier trop fortement la texture.

Types de recalibrage :

```text
1. recalibrage de durée ;
2. recalibrage de center_range ;
3. recalibrage de classification fuel/brake/absorption ;
4. recalibrage des micro-retests ;
5. recalibrage des moments zéro durée ;
6. recalibrage du langage de confiance.
```

Lecture technique :

```text
Le proxy M1 doit rester un narrateur de scène.
Le raw MT5 doit devenir le juge de texture.
```

Conséquence pour T009/B9 :

```text
Un moment proxy confirmé raw peut garder son label.
Un moment proxy recalibré doit garder sa scène mais baisser sa prétention causale.
Un moment raw unavailable doit afficher une limite forte.
```

---

## 5. Moments zéro durée

Les moments zéro durée sont un cas important de T010.

Ils peuvent venir de :

```text
- bord de fenêtre ;
- condensation de plusieurs events sur un timestamp commun ;
- replay pack segmenté ;
- groupement trop agressif ;
- absence de granularité exportée ;
- micro-node réel très court.
```

Règle proposée :

```text
Moment zéro durée ≠ suppression automatique.
Moment zéro durée = moment à qualifier par raw ou à fusionner si la scène voisine est identique.
```

Champ de limite recommandé :

```text
ZERO_DURATION_PROXY_MOMENT
```

Rendu français recommandé :

```text
Moment condensé sur un point de temps proxy. Lecture utile comme trace locale, mais durée non suffisante pour affirmer une scène autonome.
```

---

## 6. Limites broker-relative

Même avec MT5 raw, la lecture reste broker-relative.

Source :

```text
OneFunded Capital Ltd.
```

Conséquence :

```text
MT5_RAW_ALIGNED ne signifie pas marché global absolu.
MT5_RAW_ALIGNED signifie texture tick broker-relative alignée à la fenêtre proxy.
```

B9 peut donc dire :

```text
La texture raw locale confirme la scène proxy.
```

B9 ne doit pas dire :

```text
Le footprint global exact confirme la vérité universelle du marché.
```

---

## 7. Règles de sécurité analytique

Règles obligatoires pour cette intégration :

```text
- aucune écriture powerflow.db ;
- aucune écriture tick_archive.db ;
- aucun dashboard ;
- aucun Telegram ;
- aucun langage BUY/SELL comme recommandation ;
- pas de footprint exact affirmé au-delà de la preuve raw ;
- pas de fusion B8 prématurée ;
- pas de langage décisionnel ;
- source quality toujours visible ;
- limites M1_BAR_PROXY et MT5 broker-relative toujours visibles.
```

Cette mission reste documentaire et analytique. Elle ne modifie pas la logique moteur.

---

## 8. Impact sur T009/B9

### 8.1 Ce que T010 valide

```text
B9 peut utiliser M1_BAR_PROXY pour raconter la scène.
B9 peut garder center_path, zone_memory, parent_scene et effort_role.
B9 peut continuer à produire une lecture française structurée.
B9 doit afficher ses limites de source.
```

### 8.2 Ce que T010 impose

```text
Toute future validation de texture doit passer par raw aligné.
Les timings doivent être corrigés par offset.
Les moments zéro durée doivent être marqués.
Les recalibrages doivent être visibles, pas cachés.
Le raw doit enrichir le proxy, pas le faire taire automatiquement.
```

### 8.3 Ce que T010 prépare

```text
- calibration symbol-specific ;
- calibration broker-specific ;
- seuils source-aware ;
- meilleure lecture fuel/brake ;
- validation des moments B9 V3.1 ;
- futur Raw Tick Battlefield sans casser le Summarizer proxy.
```

---

## 9. Recommandation technique

Priorité courte :

```text
1. Intégrer ce rapport officiellement.
2. Ajouter un champ t010_validation_status dans les futurs rapports, pas dans le moteur immédiatement.
3. Marquer les moments recalibrage/raw unavailable dans les validations offline.
4. Conserver M1_BAR_PROXY comme lecture de scène.
5. Utiliser MT5_RAW_ALIGNED comme texture de vérification.
```

Pas de nouveau gros module maintenant.

---

## 10. Verdict final

```text
T010 valide l'intuition B9 : le proxy M1 est imparfait mais utile.
Il raconte correctement la majorité de la scène.
Le raw MT5 confirme 57 moments sur 78.
15 moments demandent recalibrage.
6 moments n'ont pas de raw exploitable.
Aucun proxy-only dur n'est détecté.
```

La ligne officielle devient :

```text
Le proxy M1 raconte la scène.
Le raw MT5 vérifie la texture.
```

Ce rapport doit servir de référence pour les prochains travaux B9 Proxy vs Raw.
