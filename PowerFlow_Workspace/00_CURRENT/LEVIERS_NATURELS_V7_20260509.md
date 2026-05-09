# LEVIERS NATURELS — PowerFlow V7
**Propositions de valeur issues de la vision organique du flux**
*Document libre — 2026-05-09*

---

## PRÉAMBULE

Ces leviers ne sont pas des features imposées.
Ce sont des extensions naturelles de la vision organique du flux.
Chacun répond à une question que le moteur ne peut pas encore poser.
Ils s'intègrent proprement dans l'architecture existante.

---

## LEVIER 1 — SESSION MEMORY OVERLAY

### La question que PowerFlow ne pose pas encore

```
FIRST_DETACHMENT à 23h10 (Asian open) ≠ FIRST_DETACHMENT à 9h45 (London open)
```

Les sessions ont des personnalités de flux différentes :
- Asian : flux lent, compression progressive, ranges
- London open : explosion, premier mouvement, ignition
- NY open : confirmation ou contre-mouvement
- London/NY overlap : bataille, vélocité maximale

### Ce que ça apporterait

Chaque alerte qualifiée par son contexte de session :
```json
{
  "alert_type": "FIRST_DETACHMENT_MICRO",
  "session_context": {
    "session": "LONDON_OPEN",
    "session_phase": "IGNITION",
    "session_bias": "EXPANSION_EXPECTED",
    "minutes_since_open": 14
  }
}
```

FIRST_DETACHMENT à London open + COMPRESSION HTF = signal fort.
FIRST_DETACHMENT à Asian morte + RANGE = bruit probable.

### Implémentation naturelle

```
pf_session_overlay.py
  → sessions : ASIAN / LONDON / NY / OVERLAP / DEAD
  → phase : PRE_OPEN / IGNITION / MID_SESSION / CLOSING
  → minutes_since_open : calculé depuis timestamp UTC
  → session_bias : EXPANSION / COMPRESSION / ROTATION

Injecter dans :
  pf_behavioral_alert_mapper.py (context additionnel)
  pf_confluence_gravity.py (fusion enrichie)
```

---

## LEVIER 2 — MEMORY ENGINE (B6)

### La question que PowerFlow ne pose pas encore

```
"La dernière fois que GBP était ELASTIC_LOADED + CYCLE_COMPRESSING
 + REGIME_COMPRESSION simultanément, que s'est-il passé ?"
```

Le moteur perçoit le présent. Il n'a pas de mémoire comportementale.
Chaque session recommence à zéro.

### Ce que ça apporterait

Context historique annexé aux alertes :
```json
{
  "historical_context": {
    "pattern": "EIE + COMPRESSION + LEADER_USD",
    "occurrences": 7,
    "median_duration_before_move_bars": 3,
    "outcome_distribution": {
      "EXPANSION": 5,
      "REJECTION": 2
    }
  }
}
```

**Important** : ce n'est pas une prédiction. C'est un contexte de fréquence.
Le trader voit "7 fois ce pattern, 5 fois expansion". Il décide.

### Implémentation naturelle

```
pf_memory_engine.py
  Lecture : behavioral_alert_queue.json historique + force_snapshots
  Index : pattern_hash = hash(alert_type + regime + session + EIE_state)
  Query : "donne-moi les N dernières occurrences de ce hash"
  Output : occurrences / median_duration / outcome_distribution

NB : ne jamais calculer de "probabilité de succès".
     Seulement des fréquences d'occurrence et de séquence.
     Le reste = trader.
```

---

## LEVIER 3 — VOLATILITY TEXTURE ENGINE (B7)

### La question que PowerFlow ne pose pas encore

```
La volatilité de cette alerte est-elle :
- structurelle (naissance de mouvement) ?
- news-driven (spike ponctuel) ?
- inter-session (friction de transition) ?
- micro-agitation (bruit de market maker) ?
```

Actuellement, B4 mesure les cycles et B3 mesure le bruit.
Mais la texture de la volatilité — pourquoi elle existe — n'est pas qualifiée.

### Ce que ça apporterait

```json
{
  "volatility_texture": {
    "type": "STRUCTURAL | NEWS_SPIKE | SESSION_FRICTION | MM_NOISE",
    "micro_macro_ratio": 0.73,
    "spread_behavior": "WIDENING | STABLE | TIGHTENING",
    "pattern_consistency": 0.81
  }
}
```

Un FIRST_DETACHMENT avec volatilité STRUCTURAL + spread TIGHTENING = qualité signal haute.
Un FIRST_DETACHMENT avec volatilité NEWS_SPIKE + spread WIDENING = alerte avec risque technique.

### Implémentation naturelle

```
pf_volatility_texture.py
  Entrées : micro_variance (B4 dérivé) + spread data (si disponible en DB)
            session_context + pattern_consistency rolling

  Pour l'instant sans spread (non capturé) :
  → Utiliser micro_macro_ratio de pf_tension_signature.py
  → Enrichir avec session_context
  → Pattern_consistency = autocorr rolling sur les variations d'amplitude
```

---

## LEVIER 4 — MULTI-SYMBOL EXTENSION

### La question que PowerFlow ne pose pas encore

```
GBPUSD est le seul symbole perçu.
Mais GBP bouge aussi sur GBPJPY, GBPCHF, GBPCAD.
Est-ce que GBP est fort globalement, ou seulement vs USD ?
```

La force de GBP vs USD seule est une perception partielle.
GBP fort vs USD + GBP fort vs JPY + GBP fort vs CHF = vraie force GBP.
GBP fort vs USD + GBP faible vs JPY = USD faible, pas GBP fort.

### Ce que ça apporterait

```json
{
  "gbp_cross_validation": {
    "gbpusd": "STRONG",
    "gbpjpy": "STRONG",
    "gbpchf": "NEUTRAL",
    "gbpcad": "WEAK",
    "gbp_true_strength": "MODERATE",
    "driver": "USD_WEAKNESS_DOMINANT"
  }
}
```

Le moteur distingue entre GBP fort et USD faible.
Deux réalités très différentes pour le scalper.

### Implémentation naturelle

```
Extension de capture_bridge.py pour capturer EURUSD / GBPJPY / USDJPY
  → symboles comme paramètre
  → même table force_snapshots avec champ symbol

pf_cross_validation.py
  → compare force GBP sur tous ses crosses
  → driver detection : USD_WEAKNESS vs GBP_STRENGTH vs MIXED
  → injecte dans alertes comme context additionnel
```

---

## LEVIER 5 — FRACTAL RESONANCE DETECTION

### La question que PowerFlow ne pose pas encore

```
Est-ce que plusieurs TF sont en train de "résonner" ensemble,
amplifiés sur le même événement, ou sont-ils décalés (lag) ?
```

B4 détecte la compression des cycles.
B7 (à venir) détecte la texture.
Mais la résonance fractale — quand LTF, MTF et HTF vibrent sur le même pattern — n'est pas mesurée.

### Ce que ça apporterait

```json
{
  "fractal_resonance": {
    "state": "RESONANT | LAGGED | DISSONANT | SILENT",
    "resonant_tfs": [1, 5, 15],
    "lag_tfs": [30, 60],
    "resonance_score": 0.84,
    "expected_amplification": true
  }
}
```

RESONANT sur LTF + MTF en même temps que REGIME_COMPRESSION HTF = signal de très haute qualité.
LAGGED = LTF a déjà bougé, MTF n'a pas encore réagi = fenêtre encore ouverte.

### Implémentation naturelle

```
pf_fractal_resonance.py
  Entrées : kinematics multi-TF (B3) + density multi-TF (B4) + regime (B1)
  Méthode : cross-corrélation entre TF adjacents
            si cross-corr élevée + même direction → RESONANT
            si cross-corr élevée + décalage temporel → LAGGED
            si cross-corr faible → DISSONANT
```

---

## LEVIER 6 — BEHAVIORAL JOURNAL (Lab amélioré)

### La question que PowerFlow ne pose pas encore

```
"Rejoue-moi la journée du 7 mai de 8h à 12h.
 Montre-moi chaque alerte qui s'est produite,
 dans quel contexte régime + EIE + cascade,
 et ce qui a suivi cinématiquement."
```

Le lab actuel fait des queries snapshot.
Il ne construit pas de film comportemental temporel.

### Ce que ça apporterait

Un `film.py` — lecture séquentielle du comportement :

```
film.py --date 2026-05-07 --start 08:00 --end 12:00 --symbol GBPUSD

Output :
  08:00  REGIME=COMPRESSION  EIE=NEUTRAL  Cascade=LOW
  08:14  FIRST_DETACHMENT GBP M1 (BIRTH) → B3 angle=52° noise=0.07
  08:16  CYCLE_COMPRESSING GBP TF5 (compression_ratio=0.78)
  08:17  EIE GBP (fractalité=2) → Daemon alert fired
  08:19  CASCADE_BUILDING (2 HOT in 5min)
  08:21  SEQUENCE_VELOCITY_HIGH (3 HOT)
  08:24  FIRST_DETACHMENT CONFIRMED → node EARLY
         [mouvement visible sur chart ici]
  09:03  CYCLE_EXPANDING GBP TF5 → respiration
```

### Implémentation naturelle

```
pf_film_engine.py
  Lecture séquentielle de force_snapshots + behavioral_alert_queue
  Reconstruction timeline événements par tranches de 1 minute
  Output : film JSON ou affichage ASCII

lab_film.py (ou film.py)
  CLI : --date / --start / --end / --symbol / --output
```

---

## PRIORISATION NATURELLE

```
Priorité 1 — Session Memory Overlay
  Faible complexité. Impact fort sur qualité de qualification.
  S'intègre proprement dans le mapper.
  À faire après validation B4/B5 sur marché ouvert.

Priorité 2 — Behavioral Journal / Film Engine
  Complète le lab. Indispensable pour analyser les sessions passées.
  Pas de nouveau calcul — lecture et reconstruction.

Priorité 3 — Fractal Resonance (B6)
  Complète B4 naturellement. Même type de données.

Priorité 4 — Volatility Texture (B7)
  Requiert spread data idéalement. Partiel possible avec tension_signature.

Priorité 5 — Memory Engine
  Plus complexe. Nécessite index de patterns sur historique.
  Valeur long terme haute.

Priorité 6 — Multi-Symbol
  Requiert extension du capture_bridge.
  Impact architectural important. À planifier soigneusement.
```

---

## CONCLUSION

Chaque levier ici est une extension de ta vision organique.
Pas une feature imposée par une IA.
Pas un indicateur classique retardé.
Pas un conseil de trading.

Chacun répond à une question que ton moteur perçoit déjà partiellement
et que tu peux compléter naturellement.

La hiérarchie de perception s'étend vers :
- le passé (Memory Engine, Film)
- le contexte (Session Overlay, Volatility Texture)
- l'espace (Multi-Symbol, Cross-validation)
- la structure (Fractal Resonance)

La décision reste toujours là où elle doit être.
Chez toi.

---

*Leviers Naturels PowerFlow V7 — Vision organique — 2026-05-09*
