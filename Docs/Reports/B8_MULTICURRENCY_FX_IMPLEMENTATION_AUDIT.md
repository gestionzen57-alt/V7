# B8 MULTICURRENCY FX IMPLEMENTATION AUDIT

**Projet :** PowerFlow / B8 / Multi-devises FX / Cross-Symbol  
**Branche cible :** `docs/b8-multicurrency-fx-implementation-audit`  
**Statut :** audit documentaire V0  
**Nature :** contrat d'audit, pas de patch moteur  
**Doctrine :** B8 ne décide pas. B8 dit si la scene locale est soutenue, contredite ou non verifiable par les devises autour.

---

## 0. Resume executif

B8 doit devenir la couche de contexte multi-devises de PowerFlow. Son role n'est pas de remplacer B9, B6 ou B7. Son role est de repondre a une question simple :

```text
Le mouvement local observe sur une paire est-il soutenu, contredit ou non verifiable par les autres devises ?
```

Pour GBPUSD, B8 doit eviter la confusion classique :

```text
GBPUSD bouge ≠ GBP fort automatiquement.
GBPUSD bouge peut venir de GBP, de USD, des deux, ou d'une scene locale non confirmee par les crosses.
```

L'audit identifie une architecture B8 deja amorcee, mais probablement dispersee entre plusieurs modules :

```text
pf_cross_symbol_validation.py
pf_b8_cross_surface_once.py
pf_b8_data_visibility.py
pf_battlefield_flux_cross_symbol.py
pf_pair_driver_context.py
pf_coalition_relations.py
pf_coalitions.py
pf_spearman_gravity.py
pf_relational_gravity_*
run_cross_symbol_validation_once.py
run_battlefield_cross_symbol_once.py
```

Le probleme probable n'est pas l'absence totale de code. Le probleme probable est l'absence d'un **contrat commun B8** entre :

- donnees capturees ;
- validation cross-symbol ;
- gravite relationnelle ;
- evidence bus ;
- B9 scene locale ;
- B6 film memory ;
- futurs packets trader.

---

## 1. Questions d'audit

### 1.1 Couverture reelle

B8 ne peut pas parler de coalition si les symboles ne sont pas presents, pas frais ou pas alignes temporellement.

Questions minimales :

```text
Quels symboles sont presents ?
Quels timeframes sont presents ?
Combien de lignes par symbole/timeframe ?
Quel first_seen / last_seen ?
Quels symboles sont stale ?
Quels symboles sont absents ?
```

Requete read-only proposee :

```sql
SELECT
  symbol,
  timeframe,
  COUNT(*) AS rows,
  MIN(timestamp) AS first_seen,
  MAX(timestamp) AS last_seen
FROM force_snapshots_v2
GROUP BY symbol, timeframe
ORDER BY symbol, timeframe;
```

Si le champ temps se nomme autrement selon la version DB :

```sql
PRAGMA table_info(force_snapshots_v2);
```

puis remplacer `timestamp` par `created_at`, `ts_utc` ou `bar_time` selon le schema.

### 1.2 Driver reel

Pour chaque paire prioritaire, B8 doit tenter de separer :

```text
PAIR_LOCAL_MOVE
BASE_CURRENCY_STRENGTH
QUOTE_CURRENCY_WEAKNESS
MIXED_DRIVER
UNKNOWN_DRIVER
```

Exemple GBPUSD :

```text
GBPUSD monte localement.
B8 doit demander :
- GBP monte-t-il aussi sur GBPJPY / GBPCHF / GBPCAD ?
- USD faiblit-il aussi sur EURUSD / USDJPY / USDCHF / USDCAD ?
- Les crosses sont-ils alignes dans la meme fenetre temps ?
- La couverture est-elle suffisante ou degradee ?
```

### 1.3 Communication avec B5 / RG

B5 et Relational Gravity ne doivent pas etre confondus avec B8.

```text
B5 / Spearman / RG = mesure relationnelle et organisation leader/follower.
B8 = validation cross-symbol orientee driver et couverture data.
```

B8 peut consommer B5/RG, mais ne doit pas devenir une copie de B5.

### 1.4 Communication avec B9

B9 raconte la scene locale : effort, resultat, progres, retest, memoire.

B8 ajoute seulement :

```text
Cette scene locale est soutenue par les crosses.
Cette scene locale est contredite par les crosses.
Cette scene locale est non verifiable car coverage faible.
Cette scene locale est mixte.
```

B8 ne doit pas reclassifier directement un moment B9 en decision.

### 1.5 Communication avec B6

B6 doit memoriser les films et les pieges.

B8 doit fournir a B6 un contexte historisable :

```json
{
  "b8_context_state": "CONFIRMED | OPPOSED | MIXED | HONEST_UNKNOWN | CROSS_VALIDATION_DEGRADED",
  "driver": "GBP_STRENGTH | USD_WEAKNESS | MIXED_DRIVER | UNKNOWN_DRIVER",
  "coverage": "FULL | PARTIAL | THIN | BLIND",
  "trap_notes": []
}
```

B6 pourra ensuite demander :

```text
A-t-on deja vu ce film local B9 avec un contexte B8 oppose ?
Le piege venait-il d'une mauvaise lecture GBP vs USD ?
La couverture B8 etait-elle degradee ?
```

---

## 2. Modules a inventorier localement

### 2.1 Commandes d'inventaire

Depuis la racine repo :

```powershell
Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Name -match 'b8|cross|coalition|gravity|spearman|pair_driver' } | Select-Object FullName
```

Depuis Git :

```powershell
git ls-files | findstr /I "b8 cross coalition gravity spearman pair_driver"
```

### 2.2 Modules probables

| Module | Role suppose | Point d'audit |
|---|---|---|
| `pf_cross_symbol_validation.py` | validation cross-symbol | verifie driver / coverage / output |
| `pf_b8_cross_surface_once.py` | surface B8 ponctuelle | verifier si surface ou logique moteur |
| `pf_b8_data_visibility.py` | qualite data B8 | verifier etats FULL/PARTIAL/THIN/BLIND |
| `pf_battlefield_flux_cross_symbol.py` | extension battlefield cross-symbol | risque de melange B8/B9 |
| `pf_pair_driver_context.py` | contexte driver paire | central pour GBP vs USD |
| `pf_coalition_relations.py` | coalitions | verifier vocabulaire et fraicheur |
| `pf_coalitions.py` | coalitions | risque duplication avec precedent |
| `pf_spearman_gravity.py` | correlation rang | B5/RG, pas B8 pur |
| `pf_relational_gravity_*` | leader/follower/RG | utile mais a separer du contrat B8 |
| `run_cross_symbol_validation_once.py` | runner | verifier output JSON |
| `run_battlefield_cross_symbol_once.py` | runner | verifier dependances / outputs |

---

## 3. Outputs a rechercher

B8 doit avoir une sortie stable, lisible et contractuelle.

A auditer :

```text
output/b8_*.json
output/cross_symbol_*.json
output/pair_driver_*.json
output/coalition_*.json
output/relational_gravity_*.json
output/dashboard_surface/*b8*.json
```

Le point important n'est pas que le JSON existe. Le point important est :

```text
Est-ce qu'un consommateur peut savoir clairement :
- driver ;
- coverage ;
- aligned symbols ;
- missing symbols ;
- stale symbols ;
- limits ;
- confidence cap ;
- role B8 par rapport a B9 ?
```

---

## 4. Problemes probables

### 4.1 Double logique

Risque : plusieurs modules calculent une version differente de la meme idee.

Exemples :

```text
cross validation dans pf_cross_symbol_validation.py
coalitions dans pf_coalitions.py
relations dans pf_coalition_relations.py
driver dans pf_pair_driver_context.py
surface dans pf_b8_cross_surface_once.py
```

Risque technique : deux outputs contradictoires pour le meme timestamp.

### 4.2 Time alignment

B8 compare des paires. Si les snapshots ne sont pas alignes, le contexte devient fragile.

Risque officiel :

```text
B8_TIME_ALIGNMENT_RISK
```

A mesurer :

```text
max timestamp gap entre symboles dans une fenetre commune
ratio symboles alignes / symboles attendus
age des snapshots par symbole
```

### 4.3 Coverage faible

Si les crosses GBP ou USD sont absents, B8 doit dire :

```text
HONEST_UNKNOWN
CROSS_VALIDATION_DEGRADED
```

Il ne doit pas combler les trous par un verdict dur.

### 4.4 Confusion B8 / B9

B9 est local. B8 est cross-symbol. Le mauvais couplage serait :

```text
B8 impose une lecture directionnelle a B9.
B9 depend de B8 pour exister.
B8 transforme une scene locale en conclusion.
```

Le bon couplage :

```text
B9 produit la scene locale.
B8 ajoute un contexte de soutien / opposition / inconnu.
Le trader voit les deux couches separees.
```

### 4.5 Confusion B8 / B6

B6 ne doit pas recevoir seulement des evenements B8. Il doit recevoir des films contextualises.

Exemple utile :

```text
Film : high zone rejected then memory shifted down.
B8 : USD weakness was absent / GBP crosses degraded.
Piege : scene locale forte mais coalition non verifiable.
```

---

## 5. Verdict V0

B8 doit etre traite comme une couche de contexte, pas comme un moteur de validation dure.

Etats minimaux :

```text
CONFIRMED
OPPOSED
MIXED
HONEST_UNKNOWN
CROSS_VALIDATION_DEGRADED
```

Drivers minimaux :

```text
GBP_STRENGTH
USD_WEAKNESS
EUR_STRENGTH
JPY_WEAKNESS
MIXED_DRIVER
UNKNOWN_DRIVER
```

Coverage minimal :

```text
FULL
PARTIAL
THIN
BLIND
```

Risque principal : B8 parle trop fort avec trop peu de symboles.

Decision d'audit : creer un contrat JSON B8 avant tout patch moteur.

---

## 6. Prochaine etape recommandee

1. Executer l'inventaire local des modules.
2. Executer les requetes read-only de coverage.
3. Comparer outputs existants au contrat `B8_CROSS_SYMBOL_CONTEXT_CONTRACT.md`.
4. Marquer les modules doublons / obsoletes / surfaces uniquement.
5. Proposer un patch minimal seulement si un contrat manquant bloque la suite.

