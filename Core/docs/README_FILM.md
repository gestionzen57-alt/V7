# 🎬 FILM POWERFLOW — Séquence DB Auto

**Status** : ✅ OPÉRATIONNEL  
**Mission** : Rejouer les dernières heures avec toutes les briques PowerFlow

---

## 🎯 Principe

Tu veux voir ce qui s'est passé pendant que tu tradais.

Ou pendant que tu dormais.

Ou pendant la session London.

**film.py** rejoue la séquence DB et te montre **le film** :

```text
14:23:15 [M1] FIRST_DETACHMENT_GBP_UP, SPREAD_TIGHT
             | GBP +0.723 USD -0.312 | angle 0.471 | spread 1.8
             | maturity=BIRTH

14:24:02 [M1] STRONG_ANGLE_SHIFT, SAME_ANGLE_CLUSTER
             | GBP +0.815 USD -0.401 | angle 0.523 | spread 2.1
             | maturity=EARLY

14:25:30 [M1] COMPRESSION
             | GBP +0.782 USD -0.389 | angle 0.089 | spread 2.3
             | maturity=WATCH

14:27:11 [M1] FIRST_DETACHMENT_GBP_DOWN
             | GBP +0.612 USD -0.201 | angle 0.387 | spread 2.5
             | maturity=BIRTH
```

**C'est le film de ce qui s'est passé.**

---

## 🚀 Usage

### Rejouer les 4 dernières heures

```powershell
python film.py --last 4h
```

### Rejouer aujourd'hui

```powershell
python film.py --today
```

### Rejouer période spécifique

```powershell
python film.py --start "2026-05-06 08:00" --end "2026-05-06 12:00"
```

### Avec rapport Markdown

```powershell
python film.py --last 4h --report
```

---

## 📊 Événements détectés

### FIRST_DETACHMENT

```text
FIRST_DETACHMENT_GBP_UP   → Premier détachement GBP vers le haut
FIRST_DETACHMENT_GBP_DOWN → Premier détachement GBP vers le bas
```

Condition : `angle_shift > 0.3 AND speed > 0.1`

### ANGLE_SHIFT

```text
STRONG_ANGLE_SHIFT → Changement d'angle fort (> 0.4)
```

### COMPRESSION

```text
COMPRESSION → Force maintenue, angle faible
```

Condition : `angle_shift < 0.1 AND force > 0.5`

### CLUSTERS

```text
SAME_ANGLE_CLUSTER → 3 bars avec angles similaires (0.2-0.4)
```

### SPREAD

```text
SPREAD_TIGHT → Spread serré (< 2.0)
SPREAD_WIDE  → Spread large (> 4.0)
```

### FORCE EXTREME

```text
FORCE_GBP_EXTREME → Force GBP extrême (> 0.8)
FORCE_USD_EXTREME → Force USD extrême (> 0.8)
```

---

## 🔧 Options

### Timeframe

```powershell
--tf 1    # M1 (défaut)
--tf 5    # M5
--tf 15   # M15
```

### Symbole

```powershell
--symbol GBPUSD    # défaut
--symbol EURUSD
```

### Rapport

```powershell
--report    # Génère output/film_report_<timestamp>.md
```

---

## 📝 Rapport Markdown

Le rapport contient :

```markdown
# FILM POWERFLOW — 2026-05-06 08:00 → 12:00

Généré : 2026-05-06T16:30:00+00:00

---

## Film Narratif

```text
08:15:23 [M1] FIRST_DETACHMENT_GBP_UP, SPREAD_TIGHT | ...
08:17:45 [M1] STRONG_ANGLE_SHIFT | ...
...
```

---

**Légende**

- `FIRST_DETACHMENT_GBP_UP` → Premier détachement GBP vers le haut
- ...
```

---

## 💡 Use Cases

### Valider les briques après session

Tu as tradé ce matin. Tu veux voir si PowerFlow a bien vu ce que toi tu as vu.

```powershell
python film.py --start "2026-05-06 08:00" --end "2026-05-06 12:00" --report
```

Tu lis le film. Tu compares avec ce que tu as perçu live.

**Briques validées ou ajustées.**

### Analyser une période manquée

Tu as dormi pendant London. Tu veux savoir ce qui s'est passé.

```powershell
python film.py --start "2026-05-06 08:00" --end "2026-05-06 10:00"
```

Tu vois les détachements, compressions, clusters.

**Tu apprends sans avoir été là.**

### Rejouer la journée

Chaque soir :

```powershell
python film.py --today --report
```

Tu vois le film complet de la journée.

**Apprentissage continu.**

### Combiner avec notes

```powershell
# Matin : tu captures intuitions
python note.py "compression GBP, je sens libération haut"

# Soir : tu rejoues notes + film
python replay_notes.py --today
python film.py --today --report
```

**Tes intuitions vs le film réel.**

---

## 🧠 Évolution future

### V1 (actuel)

```text
✅ Détection événements basiques
✅ Kinematics (angle, speed)
✅ Maturity simple (BIRTH, EARLY, CANDIDATE, WATCH)
✅ Film narratif console + Markdown
```

### V2 (prochaine)

```text
⏳ Relay quality (M5 clean/thin/missing)
⏳ Currency Energy intégrée
⏳ Release state (ATTEMPT, CANDIDATE, CONFIRMED)
⏳ Behavioral alerts dans le film
```

### V3 (future)

```text
⏳ Relational Gravity dans le film
⏳ Temporal Density
⏳ Film multi-TF (M1+M5+M15 synchronisé)
⏳ Comparaison film vs alertes Telegram envoyées
```

---

## 🔥 Workflow réel

### Pendant le trading

```text
[Tu trades]
[Capture intuitions]

python note.py "compression, spread tight, je sens haut"
```

### Le soir

```powershell
# Rejoue tes notes
python replay_notes.py --today

# Rejoue le film DB
python film.py --today --report

# Compare
```

**Tu vois :**
1. Ce que tu as senti
2. Ce qui s'est vraiment passé
3. Ce que PowerFlow a détecté

**Tu apprends.**

**PowerFlow s'améliore.**

---

## 🎯 Phrase finale

```text
Le film DB est la mémoire objective.

Tes notes sont ta mémoire subjective.

La comparaison est l'apprentissage.

L'apprentissage devient signature.

La signature devient PowerFlow.

PowerFlow devient toi, codé.
```

---

**✅ Film opérationnel. GO rejouer tes séquences.**
