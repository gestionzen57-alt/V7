# RAPPORT — Analyse PowerFlow V7.2 — GBPUSD — 2026-05-08 07:00→15:00

**Source :** `powerflow.db` fourni dans la conversation  
**Fenêtre analysée :** `2026-05-08T07:00:00+00:00` → `2026-05-08T15:00:00+00:00`  
**Symbole :** GBPUSD  
**Attention horaire :** analyse faite sur les timestamps DB en `+00:00`.  
**Contexte utilisateur :** NFP annoncé après la fenêtre, vers 15:30 selon ton repère ; l’analyse s’arrête volontairement à 15:00.

---

## 1. Résumé exécutif

La séquence 07:00→15:00 est une **journée de construction / distribution / repositionnement pré-news**.

Lecture PowerFlow :

```text
07:00–09:00  : mise sous tension London, premières respirations, opposition GBP/USD active
09:00–10:30  : compression + absorption + contre-souffles, M1 très vif
10:30–11:45  : release principale, GBP prend le dessus, prix suit
11:45–12:45  : price lag / distribution, le prix fait encore un haut pendant que la force M1 se retourne
12:45–13:45  : refroidissement / champ moins propre
13:45–15:00  : pré-NFP coil, repositionnement, désynchronisation M1/M5/M15
```

Le point central :

```text
Le mouvement visible du prix est haussier sur la fenêtre complète :
+55 à +59 pips selon le TF.

Mais la structure interne n’est pas une tendance lisse.
C’est une bataille GBP/USD avec plusieurs respirations, absorptions et inversions internes.
```

La couche M1 est effectivement très vive. Elle ne doit pas être lue comme film principal. Elle sert surtout à voir :

```text
- les ignitions
- les absorptions
- les micro-retournements
- les moments où le prix lag la force
- les zones où le tick volume confirme une vraie interaction
```

---

## 2. Cartographie DB

Tables détectées :

```text
force_snapshots
force_snapshots_v2
signals
context_htf
nodes_v6
zone_diagnostics
```

Pour cette analyse, la source principale est :

```text
force_snapshots_v2
```

car elle contient :

```text
OHLC
tick_volume
pip_range
pip_change
spread_points
forces GBP/USD/EUR/JPY/CAD/CHF/AUD/NZD
```

Disponibilité sur 07:00→15:00 :

| tf_label   |   n |   price_delta_pips |   range_pips_total |   sum_tick_vol |   pair_diff_start |   pair_diff_end |   pair_diff_delta |   rho_gbp_usd |
|:-----------|----:|-------------------:|-------------------:|---------------:|------------------:|----------------:|------------------:|--------------:|
| M1         | 481 |               55.8 |               73.5 |          33368 |            -11.4  |           26.19 |             37.59 |        -0.682 |
| M5         |  97 |               56.4 |               73.5 |          33790 |            -15.25 |          -17.73 |             -2.49 |        -0.878 |
| M15        |  33 |               54.9 |               73.5 |          34564 |             34.78 |           -1.22 |            -36    |        -0.581 |
| M30        |  17 |               55.7 |               73.5 |          35786 |              3.02 |           52.31 |             49.3  |        -0.939 |
| H1         |   9 |               59.1 |               74.7 |          39797 |            -40.21 |           29.45 |             69.65 |        -1     |
| H4         |   2 |               48.7 |               58.9 |          36539 |             -6.49 |           -1.19 |              5.31 |       nan     |

Notes :

```text
- M1 a 481 lignes : microfilm complet.
- M5 a 97 lignes.
- M15 a 33 lignes.
- M30 a 17 lignes.
- H1 a 9 lignes.
- H4 a seulement 2 lignes dans la fenêtre : 08:00 et 12:00.
- W/D ne sont pas présents dans cette fenêtre ; les dernières valeurs D/W sont trop anciennes pour une lecture dynamique.
```

---

## 3. Lecture HTF — W / D / H4

### 3.1 W / D

W et D existent dans la DB mais ne sont pas frais sur cette fenêtre :

```text
W  : dernier snapshot 2026-04-26
D  : dernier snapshot 2026-05-04
```

Donc pour cette analyse :

```text
W/D = contexte de fond trop stale pour une lecture dynamique.
H4 = seul HTF exploitable dans la fenêtre.
```

### 3.2 H4

H4 dans la fenêtre :

```text
08:00 H4
open 1.35652 → close 1.36137
force_gbp 49.08
force_usd 55.57
force_diff GBP-USD = -6.49

12:00 H4
open 1.36141 → close 1.36139
force_gbp 54.69
force_usd 55.87
force_diff GBP-USD = -1.19
```

Lecture :

```text
H4 ne montre pas un GBP dominant franc.
H4 montre plutôt une pression USD qui se réduit.
La gravité supérieure passe de USD-dominant à quasi-équilibre.
```

Interprétation PowerFlow :

```text
H4 = champ de bataille qui se neutralise.
Le prix monte, mais la force H4 n’est pas encore un signal de domination GBP nette.
Cela rend les lectures LTF/MTF très importantes.
```

---

## 4. Lecture MTF — H1 / M30 / M15

### 4.1 H1

H1 est le meilleur traducteur global de la matinée :

```text
07:00 pair_diff GBP-USD = -40.21
15:00 pair_diff GBP-USD = +29.45
delta = +69.65
rho GBP/USD = -1.000
```

Lecture :

```text
H1 montre une bascule progressive et propre de l’opposition GBP/USD.
USD domine au début.
GBP reprend progressivement le champ.
```

C’est la couche la plus claire pour dire :

```text
La séquence complète est une transition de champ vers GBP.
```

### 4.2 M30

M30 confirme une structure relationnelle très forte :

```text
pair_diff 07:00 = +3.02
pair_diff 15:00 = +52.31
rho GBP/USD = -0.939
```

Lecture :

```text
M30 montre une opposition GBP/USD très structurée.
C’est une couche de champ, pas du bruit.
```

### 4.3 M15

M15 est la charnière intéressante :

```text
pair_diff 07:00 = +34.78
pair_diff 15:00 = -1.22
delta = -36.00
rho GBP/USD = -0.581
```

Lecture :

```text
M15 n’accompagne pas proprement la fin de séquence.
Il montre une fatigue / normalisation après l’impulsion.
```

Point critique :

```text
M15 est fort au milieu de séquence, puis décroît nettement après 13:00.
À 15:00, M15 est revenu proche de neutre / légèrement USD.
```

Interprétation :

```text
MTF = construction haussière globale.
Mais M15 prévient que la structure se fatigue avant la zone NFP.
```

---

## 5. Lecture LTF — M15 / M5 / M1

### 5.1 M5

M5 sur la fenêtre :

```text
price_delta ≈ +56.4 pips
pair_diff 07:00 = -15.25
pair_diff 15:00 = -17.73
rho GBP/USD = -0.878
```

Lecture :

```text
M5 reste très opposé GBP/USD mais ne finit pas en domination GBP.
Il montre une tension relationnelle plus qu’une libération finale.
```

C’est très important :

```text
Le prix a monté.
Mais M5 finit encore avec USD > GBP en force brute.
Donc la fin de fenêtre n’est pas une continuation propre.
```

### 5.2 M1

M1 sur la fenêtre :

```text
price_delta ≈ +55.8 pips
range total ≈ 73.5 pips
tick volume total = 33368
pair_diff 07:00 = -11.40
pair_diff 15:00 = +26.19
rho GBP/USD = -0.682
```

Lecture :

```text
M1 est beaucoup plus vif et plus réactif.
Il montre les retournements internes avant les couches supérieures.
```

M1 révèle notamment :

```text
- 10:00–10:30 : pression USD / absorption avant release
- 11:00–11:31 : release GBP visible dans la force
- 11:45–12:45 : force M1 se retourne alors que le prix reste haut
- 14:00–14:20 : flip violent GBP/USD pré-NFP
```

---

## 6. Phases comportementales

| Fenêtre     | Prix                  | Tick vol M1         | Force diff M1                     | Lecture                                      | Interprétation                                                                                                                            |
|:------------|:----------------------|:--------------------|:----------------------------------|:---------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------|
| 07:00–08:00 | +10.6                 | 1752+1506=3258      | -11→+26 then +28→+4               | London open / première mise sous tension     | M1/M5 signalent beaucoup de COMPRESSION_BREAK; force GBP reprend sur USD mais MTF pas encore propre.                                      |
| 08:00–09:00 | +8.8                  | 1550+1395=2945      | +1→+14 puis +21→-19               | Contre-souffle / respiration instable        | LTF détecte compression réelle candidate vers 08:45; en M1 c’est vif, mais la structure reste fragile.                                    |
| 09:00–10:30 | +11.1 puis -7.2       | 2502+2342+2728=7572 | -14→+9 puis +8→-51 puis -53→-47   | Compression / absorption / fake-risk         | M1 tick-volume accélère; B4 compressing + B3 noise monte; beaucoup de rejets LTF. Zone d’étude majeure.                                   |
| 10:30–11:45 | +1.9 puis +32.0       | 2022+2694+2616=7332 | -43→-16 puis -25→+73 puis +74→-32 | Release principale puis retournement interne | Explosion de force GBP autour 11:00–11:31; prix suit. Ensuite le M1 montre déjà un renversement interne avant que le prix ait tout rendu. |
| 11:45–12:45 | +6.1 puis -1.2        | 2341+2137=4478      | -28→-57 puis -59→-34              | Distribution / price lag                     | Le prix fait son haut à 12:21 alors que force_diff M1 est déjà négatif : price lag / rattrapage potentiel.                                |
| 12:45–13:45 | -1.7                  | 1644+1900=3544      | -26→-16 puis -18→-55              | Champ qui se refroidit puis pression USD     | M15/M5 restent en opposition; signaux nombreux mais lecture moins directionnelle.                                                         |
| 13:45–15:00 | +9.6 net depuis 14:00 | 2151+1958=4109      | -52→+57 puis +58→+34              | Pré-NFP coil / repositionnement              | Force M1 se retourne fort à 14:00, M15/M5 divergent et se fatiguent vers 15:00. À 15:00, pas de décision : attente événementielle.        |

---

## 7. M1 tick volume — lecture microfilm

Les plus gros pics M1 :

| dt    |   tick_volume |    open |    high |     low |   close |   pair_diff |   force_gbp |   force_usd |
|:------|--------------:|--------:|--------:|--------:|--------:|------------:|------------:|------------:|
| 13:55 |           168 | 1.36084 | 1.36088 | 1.36049 | 1.36079 |    -32.2227 |     53.4197 |     85.6424 |
| 12:03 |           168 | 1.36196 | 1.36201 | 1.36174 | 1.36175 |     -2.2781 |     42.7597 |     45.0378 |
| 10:15 |           167 | 1.35816 | 1.3583  | 1.35802 | 1.35828 |    -43.2713 |     20.6184 |     63.8897 |
| 10:02 |           164 | 1.35879 | 1.35879 | 1.35849 | 1.35855 |    -49.1887 |     33.367  |     82.5557 |
| 12:01 |           159 | 1.36144 | 1.36186 | 1.36144 | 1.36182 |    -18.3978 |     39.7027 |     58.1005 |
| 11:25 |           147 | 1.35942 | 1.35981 | 1.35939 | 1.3598  |     66.3983 |     78.4702 |     12.0719 |
| 11:23 |           136 | 1.35943 | 1.35951 | 1.35939 | 1.3595  |     61.1034 |     75.1831 |     14.0797 |
| 11:30 |           133 | 1.36001 | 1.36032 | 1.35999 | 1.36025 |     73.9851 |     84.5297 |     10.5446 |
| 11:54 |           133 | 1.36087 | 1.36099 | 1.36079 | 1.36095 |    -22.3582 |     42.7787 |     65.1369 |
| 11:21 |           131 | 1.35899 | 1.35949 | 1.35899 | 1.35949 |     52.7607 |     72.38   |     19.6193 |
| 15:00 |           130 | 1.36128 | 1.36131 | 1.36106 | 1.36106 |     26.1869 |     62.9058 |     36.7189 |
| 11:22 |           128 | 1.35948 | 1.35963 | 1.35946 | 1.3595  |     58.0659 |     74.5285 |     16.4626 |

Lecture des pics :

```text
10:02–10:15
Tick volume élevé avec pair_diff fortement négatif.
Lecture : pression USD / contre-souffle / absorption avant la vraie release.

11:21–11:31
Tick volume élevé avec pair_diff très positif.
Lecture : phase de release GBP la plus propre.

12:01–12:03
Tick volume très élevé, mais pair_diff proche neutre puis négatif.
Lecture : friction / distribution / price lag.

13:55
Tick volume max avec pair_diff négatif.
Lecture : poussée USD / préparation du repositionnement pré-news.

14:52–15:00
Tick volume réapparaît avec pair_diff positif.
Lecture : M1 essaie de reconstruire un biais GBP alors que M5/M15 ne sont pas parfaitement alignés.
```

Point important :

```text
Le tick volume M1 est utile.
Mais il ne doit pas être lu seul.
Il indique où le flux travaille, pas automatiquement où il décide.
```

---

## 8. Lecture via Lab V7.2

J’ai exécuté les profils Lab sur la DB fournie avec les modules V7.2 disponibles dans cette session.

### 8.1 HTF profile

```text
TF profile : HTF = W/D/H4
Frames     : 2
Scenes     : 0
```

Lecture :

```text
HTF trop peu dense sur 07:00→15:00.
H4 donne seulement deux ancrages.
W/D sont stale.
```

Conclusion HTF :

```text
HTF donne le contexte : champ supérieur qui se neutralise.
Il ne donne pas la micro-lecture de la séquence.
```

### 8.2 MTF profile — H1/M30/M15 sans M1

```text
TF profile : MTF
Frames     : 32
Key events : 1
Lecture clé : 14:45
B1 proxy    : TENDANCE
B4 proxy    : CYCLE_EXPANDING
B5          : DIVERGENT
EIE proxy   : ELASTIC_IN_EXTREME
Outcome     : RELEASE_CONFIRMED
```

Lecture :

```text
MTF est très condensé.
Il voit surtout la structure globale et l’état pré-NFP.
```

Conclusion MTF :

```text
MTF donne la carte :
la séquence est une bascule progressive vers GBP,
mais à 14:45 elle reste sous tension événementielle.
```

### 8.3 LTF profile — M15/M5 avec M1 en zoom

```text
TF profile : LTF
M1 mode    : zoom
Frames     : 96
Scenes     : 39
Key events : 22
M1 zooms   : 8
M1 episodes après fusion : 3
```

Les épisodes M1 fusionnés :

```text
M1_EPISODE_01
08:15 → 08:55
ZONE_BREATH_COMPRESSION
COMPRESSION_REAL_CANDIDATE
DELAYED_RELEASE

M1_EPISODE_02
09:15 → 09:55
ZONE_BREATH_COMPRESSION
COMPRESSION_REAL_CANDIDATE
SECOND_LEG_CONFIRMED

M1_EPISODE_03
14:05 → 14:20
ZONE_BREATH_COMPRESSION
COMPRESSION_REAL_CANDIDATE
RELEASE_CONFIRMED
```

Lecture :

```text
Le Lab isole bien trois moments où M1 mérite microscope.
Ce sont les moments où la compression / respiration du flux devient exploitable pour étude.
```

---

## 9. Analyse des épisodes clés

## Épisode 1 — 08:15→08:55 — compression réelle candidate, release retardée

Contexte :

```text
Prix monte peu.
M1/M5 oscillent.
B4 compressing côté LTF.
B5 divergence active.
```

Lecture :

```text
Le marché travaille mais ne libère pas immédiatement.
C’est un bon cas de respiration de zone / préparation lente.
```

Risque technique :

```text
Si on lit M1 seul, on peut voir trop tôt.
MTF n’a pas encore confirmé une release propre.
```

Interprétation :

```text
Compression réelle candidate mais encore immature.
```

---

## Épisode 2 — 09:15→09:55 — compression puis second leg

Contexte :

```text
09:00→09:30 : prix pousse.
09:30→10:00 : retour / absorption.
M1 signale beaucoup de compression et de rejet.
```

Lecture :

```text
C’est une des zones les plus pédagogiques.
Le flux monte, respire, puis le champ prépare la suite.
```

Interprétation :

```text
Compression + counter breath + second leg en construction.
```

---

## Épisode 3 — 14:05→14:20 — pré-NFP repositioning

Contexte :

```text
13:45→14:00 : baisse / pression USD.
14:00→14:20 : retournement M1 violent vers GBP.
M15/M5 pas parfaitement alignés.
```

Lecture :

```text
M1 détecte une reconstruction rapide du biais GBP.
Mais M5/M15 montrent encore de la fatigue / désynchronisation.
```

Interprétation :

```text
Repositionnement pré-news.
C’est un moment à observer, pas à conclure.
```

---

## 10. Price lag / catch-up

Le moment le plus net :

```text
12:21 : prix fait le high M1 de la fenêtre à 1.36229
mais le pair_diff M1 est déjà négatif :
force_gbp 25.75
force_usd 53.65
pair_diff = -27.90
```

Lecture PowerFlow :

```text
Le prix fait encore un haut pendant que la force interne ne confirme plus.
C’est une signature price lag / distribution.
```

Conséquence observée :

```text
Après 12:21, le prix ne poursuit pas franchement.
La structure devient plus latérale / fatiguée avant la phase 13:45.
```

---

## 11. Gravity / B5

B5 relation sur la fenêtre :

```text
M1  rho GBP/USD = -0.682
M5  rho GBP/USD = -0.878
M15 rho GBP/USD = -0.581
M30 rho GBP/USD = -0.939
H1  rho GBP/USD = -1.000
```

Lecture :

```text
La relation GBP/USD est fortement divergente.
GBP et USD se comportent comme deux forces opposées.
```

Mais attention :

```text
B5 ne dit pas qui est leader tout seul.
B5 dit que le champ relationnel est structuré en opposition.
```

La vraie lecture leader/follower vient du timing :

```text
- H1/M30 montrent une bascule progressive vers GBP.
- M15 fatigue après 13:00.
- M1 anticipe plusieurs retournements.
- M5 reste plus conflictuel en fin de fenêtre.
```

Conclusion :

```text
Gravity = champ d’opposition fort.
Pas une simple direction.
```

---

## 12. Structural Flow Footprint

Plusieurs zones ont un comportement compatible avec :

```text
STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE
```

mais avec les risques techniques obligatoires :

```text
INFERENCE_ONLY
NO_VOLUME_DATA
NO_ORDERBOOK_DATA
```

Dans cette DB, M1 a du tick volume, mais il n’y a pas d’orderbook ni de volume institutionnel réel.

Donc formulation correcte :

```text
Empreinte comportementale candidate de flux structuré.
Pas institution confirmée.
```

Zones candidates :

```text
09:15–09:55
10:30–11:31
14:05–14:20
```

---

## 13. Lecture finale de la séquence

### Ce que PowerFlow comprend bien

```text
- Le prix monte sur la fenêtre.
- Mais la montée est construite par respirations, pas par tendance lisse.
- GBP/USD sont en opposition forte.
- H1/M30 donnent la bascule de champ vers GBP.
- M15 avertit d’une fatigue après 13:00.
- M1 montre les naissances, absorptions et repositionnements.
- Le tick volume M1 identifie bien les zones de travail du flux.
```

### Ce que PowerFlow doit qualifier prudemment

```text
- Les footprints sont candidates.
- Le HMM / Wavelet / EIE complet ne sont pas rejoués frame par frame dans cette sandbox.
- W/D ne sont pas frais.
- Après 14:00, le contexte pré-NFP rend les interprétations plus fragiles.
```

### Verdict comportemental

```text
07:00–10:30
Accumulation / compression / absorption.

10:30–11:45
Release GBP principale.

11:45–12:45
Distribution / price lag.

12:45–13:45
Refroidissement / digestion.

13:45–15:00
Repositionnement pré-NFP, M1 vif, MTF pas totalement propre.
```

---

## 14. Conclusion trader-facing, sans décision

```text
Cette séquence est un excellent cas de travail Lab V7.2.

Elle montre :
- pourquoi M1 est précieux mais trop bavard,
- pourquoi MTF doit donner la carte,
- pourquoi B5 doit rester une lecture de relation,
- pourquoi le price lag est visible,
- pourquoi le pré-news doit être lu comme champ de tension.

Le moteur ne décide pas.
Il expose la bataille.
```

---

## 15. Prochaines pistes d’expérimentation

À tester dans le Lab :

```text
1. Relancer uniquement 09:00→10:15 en LTF + M1 zoom.
2. Relancer 10:30→12:00 en MTF puis LTF zoom.
3. Relancer 11:45→12:45 pour étudier price lag / distribution.
4. Relancer 13:45→15:00 pour comprendre le pré-NFP coil.
5. Comparer avec la séquence post-15:30, mais dans un rapport séparé.
```

Commandes utiles :

```powershell
python Core\run_lab_profile_v72_once.py --db Core\powerflow.db --symbol GBPUSD --date 2026-05-08 --start 09:00 --end 10:15 --tf-profile LTF --m1 zoom --pretty

python Core\run_lab_profile_v72_once.py --db Core\powerflow.db --symbol GBPUSD --date 2026-05-08 --start 10:30 --end 12:00 --tf-profile LTF --m1 zoom --pretty

python Core\run_lab_m1_episode_merger_v72_once.py --latest --pretty
```
