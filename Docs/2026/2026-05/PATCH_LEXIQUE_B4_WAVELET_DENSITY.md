# PATCH LEXIQUE - B4 WAVELET DENSITY

**Projet :** PowerFlow V7.1  
**Patch propose :** Ajout section lexique pour B4 Wavelet Morlet  
**Date :** 2026-05-10  
**Cible :** `LEXIQUE_GRAMMAIRE_V7.1.md`  
**Statut :** Pret a integrer apres validation P0 live

---

## Instruction d'integration

Ajouter cette section a la suite du lexique V7.1, apres les sections deja presentes sur la qualite donnees, session overlay, entropie, replay et film.

Titre recommande :

```markdown
## 22. B4 WAVELET DENSITY - MORLET CWT
```

---

## Patch a coller dans le lexique

```markdown
---

## 22. B4 WAVELET DENSITY - MORLET CWT

### B4_WAVELET_DENSITY

Nouvelle lecture de la densite temporelle B4 basee sur une Continuous Wavelet Transform Morlet.
Remplace ou complete l'autocorrelation rolling lorsque les series Forex sont non-stationnaires.
Ne predit pas une direction. Mesure comment l'energie cyclique se concentre dans le temps et dans les scales.

Fichier moteur : `pf_wavelet_density.py`.
Runner : `run_wavelet_density_once.py`.
Sortie : `output/wavelet_density.json`.

### MORLET_CWT

Continuous Wavelet Transform avec ondelette Morlet.
Elle decompose le signal de force en plusieurs scales pour detecter ou l'energie oscillatoire se concentre.
Dans PowerFlow, elle sert a percevoir la compression ou l'expansion du champ cyclique.

Implementation PyWavelets : `morl`.
Nom comportemental PowerFlow : `morlet`.

### WAVELET_SCALE

Echelle d'analyse de la CWT.
PowerFlow B4 Wavelet utilise par defaut les scales `1..64`.
Un scale bas capte les oscillations courtes.
Un scale haut capte les respirations plus longues.

Ne pas confondre avec une timeframe.
Le scale est interne a l'analyse du signal sur une timeframe donnee.

### WAVELET_POWER

Puissance locale de l'ondelette :

```python
power = abs(coeffs) ** 2
```

Elle represente l'intensite de la reponse du signal de force a chaque scale et a chaque barre.
PowerFlow l'utilise comme mesure brute de densite cyclique.

### POWER_BY_SCALE

Somme de la puissance wavelet par scale :

```python
power_by_scale = power.sum(axis=1)
```

Permet d'identifier les scales ou l'energie cyclique dominante se concentre.
C'est la base du calcul de `compression_ratio` en mode wavelet.

### WAVELET_POWER_MAX

Puissance maximale observee dans la matrice wavelet.
Champ de diagnostic expose dans le JSON B4 Wavelet :

```json
"wavelet_power_max": 450.3
```

Ce n'est pas un signal de trading.
C'est une intensite brute de reponse cyclique.

### WAVELET_COMPRESSION_RATIO

Ratio de concentration de puissance cyclique :

```python
compression_ratio = max(power_by_scale) / sum(power_by_scale)
```

Interpretion comportementale :

- proche de 1.0 : energie concentree sur peu de scales, cycle compresse ;
- plus faible : energie etalee, champ cyclique en respiration ou expansion.

Seuils PowerFlow B4 Wavelet :

```text
> 0.75       CYCLE_COMPRESSING
0.50 - 0.75  CYCLE_STABLE
< 0.50       CYCLE_EXPANDING
```

### DOMINANT_SCALE

Scale ou `power_by_scale` est maximal.
Il indique la respiration cyclique dominante detectee par la CWT.

Important : `np.argmax(power_by_scale)` donne un index, pas le scale reel.
Le scale reel est :

```python
dominant_scale = scales[np.argmax(power_by_scale)]
```

### DOMINANT_PERIOD_BARS_WAVELET

Conversion comportementale du scale dominant en periode exprimee en barres :

```python
dominant_period_bars = dominant_scale * 4
```

Approximation Morlet utilisee par PowerFlow.
Elle garde la sortie compatible avec B4 legacy : periode dominante en nombre de barres, pas en Hz.

### AUTOCORR_PEAK_LEGACY

Pic d'autocorrelation conserve dans la sortie B4 Wavelet pour comparaison avec l'ancien moteur B4.
Il ne decide pas l'etat final wavelet.
Il sert a observer les ecarts entre repetition lineaire et concentration multi-scale.

Champ JSON :

```json
"autocorr_peak": 0.82
```

### CYCLE_COMPRESSING_WAVELET

Etat B4 lorsque la puissance wavelet se concentre fortement sur une zone de scales.
Indique que le champ cyclique se focalise.
C'est un pre-signal de densite temporelle, pas un ordre et pas une prediction.

Condition actuelle :

```text
compression_ratio > 0.75
validity = VALID
```

### CYCLE_EXPANDING_WAVELET

Etat B4 lorsque la puissance wavelet est dispersee entre plusieurs scales.
Indique une respiration plus large, une expansion ou un champ moins focalise.
Ce n'est pas un signal faible par nature : c'est une autre texture temporelle.

Condition actuelle :

```text
compression_ratio < 0.50
validity = VALID
```

### CYCLE_STABLE_WAVELET

Etat intermediaire entre compression et expansion.
La puissance cyclique existe, mais sans focalisation extreme.
Peut correspondre a une respiration stable, une consolidation comportementale ou une phase d'attente.

Condition actuelle :

```text
0.50 <= compression_ratio <= 0.75
validity = VALID
```

### CYCLE_NOISY_WAVELET

Etat expose lorsque le moteur ne peut pas attribuer une densite cyclique exploitable.
Ca peut venir d'un signal statique, d'une puissance nulle, d'une erreur CWT ou de donnees insuffisantes.

Important : `CYCLE_NOISY` est une qualification technique de perception.
Ce n'est pas une censure et ce n'est pas une decision de trading.

### INSUFFICIENT_DATA_WAVELET

Validite retournee lorsque la serie contient moins que le minimum de barres requis.
Valeur actuelle : 50 barres.

JSON typique :

```json
{
  "cycle_state": "CYCLE_NOISY",
  "validity": "INSUFFICIENT_DATA",
  "dominant_period_bars": 1
}
```

### STATIC_SIGNAL_WAVELET

Signal de force dont l'ecart type est quasi nul.
Cas frequent en week-end, capture arretee ou donnees figees.

Comportement moteur :

```text
cycle_state = CYCLE_NOISY
validity = INVALID
dominant_period_bars = 1
```

### MORLET_RUNTIME_ALIAS

Mapping technique necessaire entre le langage PowerFlow et PyWavelets :

```python
"morlet" -> "morl"
```

Permet de conserver le vocabulaire metier Morlet tout en executant correctement la librairie PyWavelets.

### B4_WAVELET_JSON_CONTRACT

Contrat JSON du moteur B4 Wavelet :

```json
{
  "symbol": "GBPUSD",
  "timeframe": 5,
  "timestamp": "2026-05-12T23:14:00Z",
  "cycle_state": "CYCLE_COMPRESSING",
  "compression_ratio": 0.78,
  "dominant_period_bars": 24,
  "autocorr_peak": 0.82,
  "wavelet_power_max": 450.3,
  "method": "morlet_cwt",
  "validity": "VALID"
}
```

Ce contrat est concu pour rester compatible avec la lecture B4 existante, tout en ajoutant `wavelet_power_max` et `method = morlet_cwt`.

### B4_WAVELET_RUNNER

Runner one-shot produisant un snapshot B4 Wavelet depuis `force_snapshots` en read-only.

Commande type :

```powershell
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty --output output/wavelet_density.json
```

Le runner n'ecrit jamais dans `powerflow.db`.
Il lit la memoire, appelle le moteur, puis ecrit une queue JSON temporaire.

### B4_WAVELET_VALIDATION

Validation minimale avant integration :

```powershell
python -m py_compile pf_wavelet_density.py run_wavelet_density_once.py
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty --output output/wavelet_density.json
python -m json.tool output/wavelet_density.json > $null
```

Validation comportementale attendue en marche ouvert :

```text
- dominant_period_bars different de 1 ;
- validity = VALID sur TF1/TF5/TF15 si donnees suffisantes ;
- compression_ratio stable sur snapshots rapproches ;
- autocorr_peak conserve pour comparaison legacy ;
- aucune ecriture DB ;
- aucune dependance cockpit dans pf_wavelet_density.py.
```
```

---

## Notes de doctrine

Ce patch ne transforme pas B4 en signal de trading.
Il precise seulement une nouvelle grammaire de perception : concentration cyclique, puissance par scale, periode dominante et validite technique.

Aucune notion BUY/SELL.
Aucun conseil.
Aucune censure d'alerte precoce.

La machine percoit la densite temporelle.
Le trader decide.
