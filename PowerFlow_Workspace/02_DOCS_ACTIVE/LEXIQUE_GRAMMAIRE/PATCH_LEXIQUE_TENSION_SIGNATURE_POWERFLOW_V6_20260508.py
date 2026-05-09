# PATCH LEXIQUE — TENSION SIGNATURE — POWERFLOW V6
Date : 2026-05-08
Domaine : micro-structure / compression / zone dynamique
Statut : ACTIVE_RUNTIME

---

## Nouveaux termes

### TENSION_SIGNATURE
Mesure de la micro-structure interne d'une devise sur N barres.
Ratio : micro_variance / macro_variance.
Distingue la compression institutionnelle du mouvement directionnel ou du silence.
Calculée par pf_tension_signature.compute_tension_signature().

### ELASTIC_LOADED
Label tension_signature.
Devise plate en macro mais agitée en micro.
Score > 2.5 sur échelle force_snapshots_v2.
Signature : institutions absorbent chaque tentative de sortie.
L'élastique se charge. La libération est imminente ou en cours de construction.
≠ DIRECTIONAL_MOVE ≠ DEAD_CURRENCY.

### DEAD_CURRENCY
Label tension_signature.
Devise inactive. Micro et macro équilibrés ou amplitude négligeable.
Deux cas :
  - amplitude absolue < seuil → bruit blanc, devise vraiment morte
  - score 0.35-2.5 → devise en pause avec amplitude présente

### DIRECTIONAL_MOVE
Label tension_signature.
Macro-variance domine. La devise se déplace régulièrement dans une direction.
Score < 0.35.
≠ compression ≠ accumulation.

### MICRO_VARIANCE
Variance des deltas barre-à-barre.
Capture l'agitation micro — les micro-oscillations à haute fréquence.

### MACRO_VARIANCE
Variance des moyennes mobiles sur sous-fenêtres.
Capture le drift macro — le mouvement directionnel global.

### MULTI_TF_ELASTIC
État cross-TF.
ELASTIC_LOADED détecté simultanément sur TF1 ET TF5.
Compression multi-échelle confirmée. Signal structurellement plus fort
qu'une compression isolée sur un seul TF.
Pattern fractal : la même structure de compression visible à deux échelles.

### ELASTIC_IN_EXTREME
État confluence.
MULTI_TF_ELASTIC + zone TF15/TF30 en ACCUMULATING ou EXTREME.
Compression micro-structure sur fond de gravité de zone active.
Signal le plus fort du module tension_signature.
Alerte : élastique chargé en zone de gravité — libération probable.

### ELASTIC_WEAK_ZONE
État confluence.
ELASTIC_LOADED sur un seul TF + zone active.
Signal partiel — compression visible mais non confirmée multi-échelle.

### ELASTIC_NO_ZONE
État confluence.
MULTI_TF_ELASTIC sans zone active TF15/TF30.
Compression micro présente mais sans gravité de zone pour la porter.

### ZONE_NO_ELASTIC
État confluence.
Zone TF15/TF30 active (ACCUMULATING/EXTREME) sans compression micro détectée.
La zone est chargée mais l'élastique n'est pas encore visible en micro.
Précurseur possible — à surveiller.

---

## Règles

ELASTIC_LOADED ≠ signal de trade.
ELASTIC_LOADED = perception de compression en cours.
Le trader filtre et décide.

MULTI_TF_ELASTIC = pattern fractal confirmé.
La compression existe à deux échelles temporelles simultanément.

ELASTIC_IN_EXTREME = confluence maximale tension_signature.
Pas un ordre. Une alerte de perception forte.