# 🔬 LAB RAPIDE — Test de Conditions DB

**Status** : ✅ OPÉRATIONNEL  
**Mission** : Tester tes intuitions sur la DB en 10 secondes

---

## 🎯 Principe

Tu as une intuition :

```text
"Quand angle_shift > 0.3 ET relay clean ET energy GBP > 0.6,
 ça monte souvent après"
```

Avant, tu devais :
1. Ouvrir Python
2. Écrire une requête SQL
3. Parser les résultats
4. Analyser manuellement
5. **20 minutes perdues**

Maintenant :

```powershell
python lab.py "angle_shift > 0.3 AND force_gbp > 0.5" --last 3h
```

**10 secondes. Résultat direct.**

---

## 🚀 Usage

### Syntaxe de base

```powershell
python lab.py "CONDITION" --last PÉRIODE
```

### Exemples

```powershell
# Angle shift fort
python lab.py "angle_shift > 0.3" --last 4h

# Force GBP dominante
python lab.py "force_gbp > force_usd AND force_gbp > 0.5" --last 3h

# Spread serré + force
python lab.py "spread < 2.5 AND force_gbp > 0.6" --last 6h

# Conditions multiples
python lab.py "angle_shift > 0.3 AND force_gbp > 0.5 AND spread < 3" --last 4h

# Energy (placeholder pour l'instant)
python lab.py "energy_gbp > 0.6 AND energy_usd < 0.4" --last 2h
```

---

## 📊 Champs disponibles

### Forces

```text
force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
```

### Dérivés (calculés automatiquement)

```text
angle_shift         → delta force max entre 2 bars
angle_shift_gbp     → delta force GBP
angle_shift_usd     → delta force USD
speed_gbp           → rate de changement GBP (3 bars)
speed_usd           → rate de changement USD (3 bars)
```

### Prix / Spread

```text
bid
spread
```

### Relay / Energy (v1 simplifiée)

```text
relay_clean         → (placeholder, à enrichir)
relay_thin
relay_missing
energy_gbp          → (placeholder, à enrichir avec pf_currency_energy)
energy_usd
```

---

## 🔧 Options

### Période

```powershell
--last 3h          # Dernières 3 heures
--last 30m         # Dernières 30 minutes
--last today       # Depuis 00:00 aujourd'hui
```

### Timeframe

```powershell
--tf 1             # M1 (défaut)
--tf 5             # M5
--tf 15            # M15
--tf 30            # M30
```

### Symbole

```powershell
--symbol GBPUSD    # défaut
--symbol EURUSD
```

### Bars après

```powershell
--bars-after 10    # Analyse 10 bars après (défaut)
--bars-after 20    # Analyse 20 bars après
```

---

## 📈 Sortie

Pour chaque occurrence trouvée :

```text
================================================================================

📍 OCCURRENCE #1
   Timestamp : 2026-05-06 14:23:15
   Bid       : 1.26345
   Spread    : 2.3
   GBP       : 0.723
   USD       : 0.312
   Angle     : 0.471

   📈 Après 10 bars :
      High : +12.3 pips
      Low  : -2.1 pips
      Net  : +8.7 pips
      GBP Δ: +0.145
      USD Δ: -0.082
      ✅ UP +8.7 pips

   ----------------------------------------------------------------------------
```

---

## 🧠 Opérateurs

### Comparaison

```text
>    Plus grand
<    Plus petit
>=   Plus grand ou égal
<=   Plus petit ou égal
==   Égal
!=   Différent
```

### Logique

```text
AND   ET logique
OR    OU logique
NOT   NON logique
```

### Exemples

```powershell
# ET
python lab.py "force_gbp > 0.5 AND spread < 3" --last 4h

# OU
python lab.py "force_gbp > 0.7 OR force_usd < -0.5" --last 4h

# Combinaison
python lab.py "angle_shift > 0.3 AND (force_gbp > 0.5 OR force_usd < -0.3)" --last 4h
```

---

## 💡 Use Cases

### Valider une signature

```powershell
# Tu penses : "quand angle > 0.3 + GBP > 0.5, ça monte"
python lab.py "angle_shift > 0.3 AND force_gbp > 0.5" --last 6h --tf 1

# Tu vois combien de fois ça s'est produit
# Tu vois combien de fois ça a monté après
# Tu VALIDES ou INVALIDES ton intuition
```

### Trouver le seuil optimal

```powershell
# Test plusieurs seuils
python lab.py "angle_shift > 0.2" --last 4h
python lab.py "angle_shift > 0.3" --last 4h
python lab.py "angle_shift > 0.4" --last 4h

# Compare les résultats
# Trouve le seuil qui donne le meilleur signal
```

### Tester un combo

```powershell
# Combo force + spread + angle
python lab.py "force_gbp > 0.6 AND spread < 2.5 AND angle_shift > 0.35" --last 4h

# Vois si ce combo est rare (donc précieux)
# Ou commun (donc bruit)
```

---

## 🔥 Workflow réel

### 1. Intuition en live

Tu trades. Tu vois un comportement.

```text
"Tiens, quand l'angle shift est fort et que le spread est serré,
 ça monte souvent après"
```

### 2. Capture

```powershell
python note.py "angle fort, spread serré, ça monte"
```

### 3. Test DB

```powershell
python lab.py "angle_shift > 0.3 AND spread < 2.5" --last 6h
```

### 4. Résultat

```text
✅ 12 occurrences trouvées
   9 → UP
   2 → DOWN
   1 → FLAT

→ Signal valide à 75%
```

### 5. Signature

Si validé → tu crées la signature PowerFlow.

```python
signature = Signature(
    name="ANGLE_SHIFT_TIGHT_SPREAD_UP",
    conditions=[
        ("angle_shift", ">", 0.3),
        ("spread", "<", 2.5),
    ],
    expected_direction="UP",
    confidence=0.75,
)
```

### 6. Intégration moteur

La signature devient une brique PowerFlow.

Le moteur détecte maintenant ce comportement.

---

## 🎯 Phrase finale

```text
Tes intuitions → Lab rapide (10s)
Lab rapide → Validation DB
Validation DB → Signatures
Signatures → PowerFlow

Le cycle s'accélère.
Tes perceptions deviennent code.
PowerFlow devient toi.
```

---

**✅ Lab opérationnel. GO tester tes intuitions.**
