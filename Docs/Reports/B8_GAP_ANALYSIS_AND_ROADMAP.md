# B8 GAP ANALYSIS AND ROADMAP

**Projet :** PowerFlow / B8 / Multi-devises FX  
**Objet :** manques, risques techniques, roadmap minimale  
**Statut :** audit documentaire V0  

---

## 0. Verdict

B8 semble deja posseder plusieurs morceaux de logique multi-devises, mais il manque probablement :

```text
un contrat JSON unique,
une politique claire de coverage,
un alignement temporel explicite,
une separation nette B5/RG/B8,
un langage HONEST_UNKNOWN quand les donnees sont faibles,
une liaison propre avec B9/B6 sans fusion prematuree.
```

Le risque principal est que B8 parle trop fort avec une couverture trop faible.

---

## 1. Gaps data

### 1.1 Symbol coverage

Manque possible : liste officielle des symboles attendus.

Proposition minimale :

```text
GBPUSD
GBPJPY
GBPCHF
GBPCAD
EURUSD
USDJPY
USDCHF
USDCAD
AUDUSD
NZDUSD
```

Selon la disponibilite broker, chaque symbole doit etre classe :

```text
AVAILABLE
MISSING
STALE
THIN
```

### 1.2 Timeframe coverage

B8 doit distinguer :

```text
M1 coverage
M5 coverage
M15 coverage
HTF context optional
```

Si M1 est present mais M5/M15 absent :

```text
coverage = PARTIAL
limits += ["M5_M15_CROSS_CONTEXT_MISSING"]
```

### 1.3 Time alignment

B8 doit mesurer l'ecart temporel entre symboles.

Champ propose :

```json
{
  "time_alignment": {
    "max_gap_seconds": 0,
    "aligned": true,
    "risk": "NONE | B8_TIME_ALIGNMENT_RISK"
  }
}
```

---

## 2. Gaps architecture

### 2.1 Contrat JSON absent ou disperse

Sortie cible unique : `cross_symbol_context`.

Si plusieurs modules produisent des sorties differentes, choisir un contrat commun et laisser les autres comme producteurs d'evidence.

### 2.2 Confusion B5 / RG / B8

Clarification :

```text
B5 = mesure relationnelle.
RG = organisation leader/follower/coalition.
B8 = validation cross-symbol orientee driver + coverage.
```

### 2.3 Confusion B8 / B9

B9 ne doit pas attendre B8 pour raconter la scene locale.

B8 arrive apres comme contexte :

```text
supported
opposed
mixed
unknown
degraded
```

### 2.4 B8 vers surfaces

Aucun patch dashboard / Telegram maintenant.

Toute sortie B8 doit rester consommable par fichier ou evidence bus, sans import surface depuis `pf_*`.

---

## 3. Gaps semantiques

### 3.1 Driver trop dur

B8 doit eviter :

```text
GBP est fort.
USD est faible.
```

si coverage insuffisante.

Preferer :

```text
GBP_STRENGTH_CANDIDATE
USD_WEAKNESS_CANDIDATE
MIXED_DRIVER
UNKNOWN_DRIVER
```

### 3.2 Absence de HONEST_UNKNOWN

Si le moteur ne sait pas, il doit le dire.

Etats obligatoires :

```text
HONEST_UNKNOWN
CROSS_VALIDATION_DEGRADED
```

### 3.3 Absence de piege historisable

B8 doit documenter les faux contextes :

```text
GBPUSD semblait porter une scene locale, mais les GBP crosses etaient absents.
USD weakness semblait dominante, mais USDJPY et USDCHF contredisaient.
Coalition apparente degradee par time alignment.
```

---

## 4. Roadmap minimale

### Etape 1 — Audit local reel

Executer :

```powershell
git ls-files | findstr /I "b8 cross coalition gravity spearman pair_driver"
```

Puis inventorier outputs :

```powershell
Get-ChildItem -Path .\Core\output -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'b8|cross|coalition|gravity|driver' }
```

### Etape 2 — Coverage DB read-only

Executer :

```sql
SELECT symbol, timeframe, COUNT(*) rows, MIN(timestamp) first_seen, MAX(timestamp) last_seen
FROM force_snapshots_v2
GROUP BY symbol, timeframe;
```

Adapter le champ temps au schema reel.

### Etape 3 — Comparer les modules au contrat

Chaque module doit etre classe :

```text
CORE_PRODUCER
EVIDENCE_PRODUCER
SURFACE_ONLY
LEGACY_DUPLICATE
UNKNOWN
```

### Etape 4 — Patch minimal contrat

Seulement apres audit : creer ou normaliser une fonction read-only :

```python
def build_cross_symbol_context(...):
    return {
        "cross_symbol_context": {...}
    }
```

### Etape 5 — B6 integration plus tard

B6 doit memoriser :

```text
film B9 + contexte B8 + coverage + piege.
```

Pas de prediction.

---

## 5. Risques techniques

| Risque | Description | Mitigation |
|---|---|---|
| `B8_TIME_ALIGNMENT_RISK` | symboles compares a des instants differents | max_gap_seconds + aligned false |
| `CROSS_VALIDATION_DEGRADED` | trop peu de crosses | coverage THIN/BLIND |
| `DRIVER_OVERCLAIM` | B8 affirme GBP/USD sans preuve suffisante | utiliser UNKNOWN_DRIVER |
| `MODULE_DUPLICATION` | plusieurs modules calculent la meme chose | contrat unique |
| `B5_B8_CONFUSION` | correlation prise pour driver | separer mesure et interpretation |
| `B8_B9_PREMATURE_MERGE` | B8 reclassifie B9 trop tot | B8 contexte uniquement |
| `SURFACE_DEPENDENCY` | pf_* importe dashboard/telegram | tests statiques anti-import |
| `STALE_SYMBOLS` | paires non fraiches | stale_symbols visible |

---

## 6. Roadmap proposee

### P0 — Documentation actuelle

Ce pack : audit + communication map + gap analysis + contrat.

### P1 — Audit DB et outputs reels

Lire `force_snapshots_v2`, outputs B8, modules presents.

### P2 — Contrat JSON B8 minimal

Normaliser `cross_symbol_context`.

### P3 — Evidence Bus

Injecter B8 comme preuve, pas comme decision.

### P4 — B6 Film Memory

Stocker les films B9 avec contexte B8.

### P5 — Surface trader plus tard

Uniquement apres validation du contrat.

---

## 7. Phrase de verrouillage

```text
B8 ne decide pas.
B8 contextualise.
Si B8 ne peut pas verifier, il doit le dire clairement.
```

