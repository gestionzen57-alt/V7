# B9 Proxy vs Raw — First Validation

**Projet :** PowerFlow / T009 / B9 — Microfilm Battlefield Memory  
**Mission :** T010 / B9 Proxy vs Raw  
**Version :** First official validation  
**Statut :** prêt pour intégration documentaire  
**Branche cible :** `docs/t010-b9-proxy-vs-raw-first-validation`  
**Nature :** rapport de validation documentaire, read-only, sans modification moteur.

---

## 0. Phrase de cap

```text
Le proxy M1 raconte la scène.
Le raw MT5 vérifie la texture.
```

Cette validation ne transforme pas B9 en système de décision. Elle vérifie la qualité du récit `M1_BAR_PROXY` en le confrontant à une source MT5 brute alignée.

---

## 1. Sources validées

### 1.1 Source proxy

```text
source_mode      : M1_BAR_PROXY
data_visibility  : RECONSTRUCTED
symbole          : GBPUSD
fenêtre proxy    : 2026-05-15 08:00–23:00
rôle             : raconter la scène, la migration du centre, les zones mémoire, l'effort/résultat.
```

Le proxy M1 reste une reconstruction. Il est utile pour lire les scènes, mais il ne doit pas prétendre fournir un footprint exact.

### 1.2 Source raw

```text
source_mode      : MT5 HISTORICAL_RAW
data_visibility  : MT5_RAW_ALIGNED
DB raw           : tick_archive.db
sauvegarde       : tick_archive_T010_GBPUSD_20260515_RAW_OFFSET_PLUS3_VALIDATED.db
broker raw MT5   : OneFunded Capital Ltd.
symbole          : GBPUSD
raw après shift  : 2026-05-15 08:00:01 → 2026-05-15 22:59:58
ticks alignés    : 74 108
```

### 1.3 Offset temporel validé

```text
raw_ts_mt5 + 180 minutes = proxy_ts_mt4_approx
```

L'offset détecté est donc `+3h`. Le raw MT5 devient comparable au proxy MT4 approximatif après shift de 180 minutes.

---

## 2. Résultats chiffrés

| Mesure | Valeur |
|---|---:|
| Fenêtre proxy GBPUSD | 2026-05-15 08:00–23:00 |
| Raw aligné après shift | 08:00:01 → 22:59:58 |
| Ticks raw alignés | 74 108 |
| Moments proxy B9 | 78 |
| Moments confirmés raw | 57 |
| Moments nécessitant recalibrage | 15 |
| Moments raw unavailable | 6 |
| Proxy-only dur | 0 |

Lecture rapide :

```text
57 / 78 moments proxy sont confirmés par la texture raw.
15 / 78 demandent recalibrage.
6 / 78 manquent de disponibilité raw exploitable.
0 / 78 sont proxy-only durs.
```

---

## 3. Ce que le raw confirme

Le raw MT5 aligné confirme l'essentiel de la lecture B9 issue du proxy M1 :

```text
- la structure générale de la journée ;
- les migrations de centre ;
- les zones où le proxy raconte une scène cohérente ;
- les paliers de digestion ;
- les moments où l'effort devient visible ;
- les passages où le prix change de mémoire active.
```

Le résultat le plus important est l'absence de proxy-only dur :

```text
proxy-only dur = 0
```

Cela signifie que le proxy M1 ne fabrique pas une scène totalement déconnectée de la texture raw disponible. Il simplifie, reconstruit et compresse, mais il reste exploitable comme couche de lecture de scène.

---

## 4. Ce qui demande recalibrage

Les 15 moments en recalibrage ne doivent pas être lus comme échec. Ils indiquent des zones où le proxy M1 raconte correctement l'idée générale, mais pas assez finement la texture.

Causes probables :

```text
- compression excessive par bucket M1 ;
- durée trop courte du moment ;
- center_path interne plus violent que le net final ;
- micro-retours invisibles dans la bougie M1 ;
- delta proxy trop pauvre ;
- moment classé par endpoint alors que le raw montre un trajet interne plus riche.
```

Règle B9 :

```text
Si le raw montre une texture plus complexe que le proxy, on ne jette pas le proxy.
On baisse la prétention du label et on enrichit les limites visibles.
```

---

## 5. Moments zéro durée

Certains moments peuvent apparaître avec une durée nulle ou quasi nulle. Ils ne doivent pas être automatiquement supprimés.

Interprétation :

```text
moment zéro durée = point de condensation du proxy ou bord de fenêtre
```

Traitement recommandé :

```text
- garder le moment si la zone est informative ;
- ajouter une limite ZERO_DURATION_PROXY_MOMENT ;
- éviter de lui attribuer une causalité forte ;
- le fusionner seulement si la zone voisine raconte la même scène.
```

Le raw peut aider à déterminer si le moment zéro durée est un vrai micro-nœud ou seulement un artefact de découpage.

---

## 6. Limites broker-relative

Le raw provient de :

```text
OneFunded Capital Ltd.
```

Sur Forex, même en raw MT5 historique, la donnée reste broker-relative. Elle est beaucoup plus fine que le proxy M1, mais elle ne représente pas le marché interbancaire global.

Langage obligatoire :

```text
MT5_RAW_ALIGNED = texture broker-relative alignée.
M1_BAR_PROXY = scène reconstruite.
```

Langage interdit :

```text
footprint global exact
vérité absolue du marché
ordre agressif confirmé universellement
barrière limite confirmée sans preuve directe
```

---

## 7. Règles d'intégration T010

```text
- aucune écriture powerflow.db ;
- aucune écriture tick_archive.db ;
- aucun dashboard ;
- aucun Telegram ;
- aucun langage BUY/SELL comme recommandation ;
- pas de footprint exact affirmé au-delà de la preuve raw ;
- pas de fusion B8 prématurée ;
- source_mode, data_visibility, confidence_cap et limites doivent rester visibles.
```

---

## 8. Conséquences pour B9

### 8.1 Ce que B9 peut conserver du proxy

```text
- lecture de scène ;
- center migration ;
- effort / résultat ;
- progressive vs corrective wave ;
- zone_memory ;
- parent_scene ;
- effort_role ;
- memory_state ;
- retest_status prudent.
```

### 8.2 Ce que B9 doit renforcer avec le raw

```text
- durée réelle des micro-moments ;
- texture intra-minute ;
- distinction fuel / brake ;
- micro-retest ;
- center_path interne ;
- moments zéro durée ;
- recalibrage des seuils de center_range.
```

### 8.3 Ce que B9 ne doit pas faire

```text
- remplacer la prudence source-aware par un label trop affirmatif ;
- appeler footprint exact une lecture M1 proxy ;
- affirmer une causalité passive directe sans preuve raw ;
- convertir la validation raw en recommandation directionnelle.
```

---

## 9. Verdict officiel

```text
Le M1_BAR_PROXY raconte correctement la scène majoritaire.
Le MT5 HISTORICAL_RAW aligné confirme 57 moments sur 78.
15 moments demandent recalibrage.
6 moments restent raw unavailable.
Aucun proxy-only dur n'est détecté.
```

Conclusion :

```text
B9 peut continuer à utiliser M1_BAR_PROXY comme lecteur de scène,
mais T010 doit devenir la couche de vérification texture raw.
```

Phrase finale :

```text
Le proxy M1 raconte la scène.
Le raw MT5 vérifie la texture.
PowerFlow doit garder les deux : récit + preuve.
```
