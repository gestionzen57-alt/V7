# RAPPORT COMPLET - MISSION 2 - B4 WAVELET DENSITY

**Projet :** PowerFlow V7.1  
**Mission :** B4 Wavelet Density - Morlet CWT upgrade  
**Date de livraison :** 2026-05-10  
**Mode :** Infrastructure / moteur de perception  
**Commit cible :** `B4: Morlet Wavelet CWT upgrade`

---

## 1. Resume executif

La mission a produit une nouvelle brique B4 alternative :

```text
Core/pf_wavelet_density.py
Core/run_wavelet_density_once.py
output/wavelet_density.json
```

Objectif atteint : remplacer la logique fragile d'autocorrelation rolling par une perception de densite cyclique via **Morlet Continuous Wavelet Transform**.

Le module garde le contrat comportemental B4 existant :

```json
{
  "cycle_state": "CYCLE_COMPRESSING | CYCLE_EXPANDING | CYCLE_STABLE | CYCLE_NOISY",
  "compression_ratio": 0.0,
  "dominant_period_bars": 1,
  "autocorr_peak": 0.0,
  "wavelet_power_max": 0.0,
  "method": "morlet_cwt",
  "validity": "VALID | INVALID | INSUFFICIENT_DATA"
}
```

Le moteur ne decide rien. Il percoit la densite temporelle, nomme l'etat du cycle et expose les risques techniques via `validity` et `error` si necessaire.

---

## 2. Contexte PowerFlow

PowerFlow V7.1 est un moteur de perception du flux Forex. La brique B4 appartient a la couche moteur `pf_*`.

Role B4 historique :

```text
Detecter si les oscillations de force se compriment dans le temps.
Produire un pre-signal de rupture avant que la lecture prix soit evidente.
```

Limite de l'ancienne approche :

```text
Autocorrelation rolling fragile sur series Forex non-stationnaires.
Autocorr utile pour comparaison, mais trop sensible aux regimes mixtes, shifts de moyenne et transitions de session.
```

Amelioration livree :

```text
CWT Morlet = lecture multi-scale de la puissance cyclique.
Le moteur ne cherche pas seulement une repetition lineaire.
Il mesure ou l'energie cyclique se concentre dans le champ des scales.
```

---

## 3. Livrables produits

### 3.1 `Core/pf_wavelet_density.py`

Classe principale :

```python
WaveletDensityAnalyzer
```

Responsabilites :

```text
- Nettoyer le signal force_rolling.
- Refuser les donnees insuffisantes.
- Detecter signal statique / week-end / capture figee.
- Calculer CWT Morlet.
- Calculer power = abs(coeffs) ** 2.
- Calculer power_by_scale.
- Calculer compression_ratio.
- Calculer dominant_period_bars.
- Garder autocorr_peak pour comparaison legacy.
- Produire un dict JSON-ready compatible B4.
```

Proprietes importantes :

```python
DEFAULT_MIN_BARS = 50
DEFAULT_SCALES = np.arange(1, 65, dtype=int)
COMPRESSION_THRESHOLD = 0.75
STABLE_THRESHOLD = 0.50
```

Etats cycles :

```text
compression_ratio > 0.75  -> CYCLE_COMPRESSING
compression_ratio >= 0.50 -> CYCLE_STABLE
compression_ratio < 0.50  -> CYCLE_EXPANDING
signal invalide/statique  -> CYCLE_NOISY
```

### 3.2 `Core/run_wavelet_density_once.py`

Runner one-shot CLI.

Responsabilites :

```text
- Ouvrir powerflow.db en read-only.
- Lire force_snapshots.
- Recuperer les 100 dernieres barres par timeframe.
- Supporter TF1, TF5, TF15 par defaut.
- Produire output/wavelet_density.json.
- Imprimer le JSON dans stdout.
```

Arguments CLI :

```powershell
python Core\run_wavelet_density_once.py --db Core\powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty --output Core\output\wavelet_density.json
```

Options disponibles :

```text
--db          chemin SQLite, read-only
--symbol      symbole affiche, defaut GBPUSD
--currency    devise force pour schema V7, defaut infere depuis symbol
--force-col   colonne force explicite, ex: force_gbp
--tfs         timeframes separes par virgule, ex: 1,5,15
--bars        nombre de barres lues, defaut 100
--output      chemin JSON de sortie
--pretty      JSON lisible
```

### 3.3 `output/wavelet_density.json`

Snapshot JSON de validation locale produit sur base synthetique SQLite.

Extrait :

```json
{
  "1": {
    "symbol": "GBPUSD",
    "timeframe": 1,
    "cycle_state": "CYCLE_EXPANDING",
    "compression_ratio": 0.056658192068786827,
    "dominant_period_bars": 116,
    "autocorr_peak": 0.8401968338489662,
    "wavelet_power_max": 1017.4413401799368,
    "method": "morlet_cwt",
    "validity": "VALID"
  }
}
```

---

## 4. Calcul moteur livre

### 4.1 Signal d'entree

Entree attendue :

```python
force_rolling: Iterable[float]
```

Format comportemental :

```text
100 barres chronologiques recommandees.
Minimum runtime : 50 barres.
TF compatibles : 1, 5, 15, 30, 60, 240, 1440.
```

Le runner recupere les lignes SQL en DESC puis les inverse pour reconstruire l'ordre chronologique.

### 4.2 CWT Morlet

Formule operationnelle :

```python
coeffs = pywt.cwt(signal, scales, "morl")[0]
power = np.abs(coeffs) ** 2
power_by_scale = power.sum(axis=1)
```

Important : le prompt mission parle de `morlet`, mais PyWavelets nomme l'ondelette Morlet `morl`. Le module garde l'intention PowerFlow `morlet` et mappe correctement vers `morl` pour eviter une erreur runtime.

### 4.3 Compression ratio

Definition livree :

```python
compression_ratio = max(power_by_scale) / sum(power_by_scale)
```

Interpretation PowerFlow :

```text
Ratio haut  = puissance concentree sur peu de scales.
Ratio bas   = puissance etalee, champ cyclique moins focalise.
```

Classification :

```text
> 0.75       CYCLE_COMPRESSING
0.50 - 0.75  CYCLE_STABLE
< 0.50       CYCLE_EXPANDING
```

### 4.4 Dominant period

Correction importante :

```python
dominant_index = np.argmax(power_by_scale)
dominant_scale = scales[dominant_index]
dominant_period_bars = dominant_scale * 4
```

Le prompt brut utilisait directement `np.argmax(power_by_scale)`. Cela donne un index zero-based, pas le scale reel. La version livree prend bien le scale correspondant.

### 4.5 Autocorr legacy

Le champ `autocorr_peak` est conserve pour comparaison.

Implementation robuste :

```text
- centrage du signal avant autocorrelation ;
- garde denominateur nul ;
- lag 0 ignore ;
- max sur lags 1..19.
```

Objectif : valider Wavelet vs ancienne B4 sans confondre avec une decision de signal.

---

## 5. Corrections techniques par rapport au prompt brut

Ces corrections sont volontaires et necessaires pour avoir un fichier executable dans PowerFlow.

### 5.1 Nom PyWavelets

Prompt :

```python
wavelet = "morlet"
```

Runtime PyWavelets :

```python
wavelet = "morl"
```

Livraison :

```python
aliases = {"morlet": "morl", "morl": "morl"}
```

### 5.2 Retour de `pywt.cwt`

Selon version PyWavelets, `pywt.cwt` retourne :

```python
(coefficients, frequencies)
```

Livraison :

```python
cwt_result = pywt.cwt(signal, self.scales, self.pywt_wavelet)
coeffs = cwt_result[0] if isinstance(cwt_result, tuple) else cwt_result
```

### 5.3 Dominant scale

Prompt :

```python
dominant_scale = np.argmax(power_by_scale)
```

Risque : index 0..63 au lieu de scale 1..64.

Livraison :

```python
dominant_index = int(np.argmax(power_by_scale))
dominant_scale = int(self.scales[dominant_index])
```

### 5.4 Validity contract

Le prompt mentionnait `INSUFFICIENT_DATA` dans la sortie attendue et `INVALID` dans les snippets.

Livraison :

```text
validity = INSUFFICIENT_DATA si moins de 50 barres.
validity = INVALID si signal statique, zero power ou erreur CWT.
validity = VALID si calcul exploitable.
```

### 5.5 Runner compatible schema DB

Le prompt supposait une colonne generique :

```sql
SELECT force FROM force_snapshots
```

PowerFlow V7 peut utiliser des colonnes de type :

```text
force_gbp, force_usd, force_eur, etc.
```

Livraison :

```text
- si colonne force existe : utilise force ;
- sinon inferre force_gbp depuis GBPUSD ;
- sinon accepte --force-col ;
- si symbol existe : filtre symbol ;
- si symbol n'existe pas : compatible DB single-symbol legacy.
```

---

## 6. Validation effectuee ici

Checks realises sur l'environnement de livraison :

```powershell
python -m py_compile Core\pf_wavelet_density.py Core\run_wavelet_density_once.py
python Core\run_wavelet_density_once.py --db <sample_db> --tfs 1,5,15 --pretty --output output\wavelet_density.json
python -m json.tool output\wavelet_density.json
```

Resultat :

```text
py_compile : OK
runner synthetique : OK
JSON valide : OK
```

Limite honnete :

```text
Le test sur powerflow.db reel et le commit Git ne peuvent pas etre executes depuis cet environnement.
Le depot distant est accessible en lecture, mais pas en ecriture.
Le commit doit etre fait depuis le workspace Windows local.
```

---

## 7. Validation a lancer dans le depot reel

Depuis le repo V7 local :

```powershell
cd Core
pip install PyWavelets numpy scipy
python -m py_compile pf_wavelet_density.py run_wavelet_density_once.py
python run_wavelet_density_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15 --pretty --output output/wavelet_density.json
python -m json.tool output/wavelet_density.json > $null
```

Comparaison legacy B4 :

```powershell
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --pretty > autocorr_results.json
python run_wavelet_density_once.py --db powerflow.db --tfs 1,5,15 --pretty > wavelet_results.json
python -c "
import json
wavelet = json.load(open('wavelet_results.json'))
for tf in ['1','5','15']:
    w = wavelet.get(tf, {})
    print(f'TF{tf}: state={w.get("cycle_state")}, ratio={w.get("compression_ratio")}, autocorr_peak={w.get("autocorr_peak")}, period={w.get("dominant_period_bars")}')
"
```

Stabilite :

```powershell
python run_wavelet_density_once.py --db powerflow.db --tfs 1,5,15 --pretty > snap1.json
python run_wavelet_density_once.py --db powerflow.db --tfs 1,5,15 --pretty > snap2.json
python run_wavelet_density_once.py --db powerflow.db --tfs 1,5,15 --pretty > snap3.json
python -c "
import json
for i in [1,2,3]:
    data = json.load(open(f'snap{i}.json'))
    tf5 = data.get('5', {})
    print(f'Snapshot {i}: TF5={tf5.get("cycle_state")}, ratio={tf5.get("compression_ratio")}, period={tf5.get("dominant_period_bars")}')
"
```

JSON valide :

```powershell
python -m json.tool output/wavelet_density.json > $null
```

---

## 8. Commande commit

Script fourni :

```text
commit_b4_wavelet.ps1
```

Commande manuelle alternative :

```powershell
git status
git add Core/pf_wavelet_density.py Core/run_wavelet_density_once.py
git add -f Core/output/wavelet_density.json
git commit -m "B4: Morlet Wavelet CWT upgrade"
git push
```

Note PowerFlow : si `output/` est ignore par Git, c'est normal. Le livrable permanent critique est le code moteur + runner.

---

## 9. Risques techniques residuels

### 9.1 Calibration compression ratio

Risque : seuil `0.75` tres strict avec concentration par somme multi-scale.

Impact possible : beaucoup de `CYCLE_EXPANDING` sur donnees vivantes alors que l'ancien autocorr voyait de la compression.

Mitigation : garder le seuil mission pour compatibilite, puis observer sur P0 live. Si besoin, creer une calibration V7.1.1 apres film marche ouvert.

### 9.2 Difference de distribution vs autocorr

La wavelet ne mesure pas la meme chose que l'autocorr.

Autocorr : repetition lineaire par lag.  
Wavelet : concentration d'energie par scale.

Donc les ratios ne doivent pas etre attendus numeriquement identiques. Ils doivent etre comportementalement comparables.

### 9.3 Dependency PyWavelets

Risque : `PyWavelets` absent sur machine Windows.

Mitigation :

```powershell
pip install PyWavelets numpy scipy
python -c "import pywt; print(pywt.__version__)"
```

Le module contient un fallback numpy pour smoke test, mais la production doit utiliser PyWavelets.

### 9.4 Data figee / weekend

Si signal plat :

```text
validity = INVALID
cycle_state = CYCLE_NOISY
dominant_period_bars = 1
```

C'est un risque de perception, pas un filtre de trading.

---

## 10. Integration architecture

La brique respecte la separation PowerFlow :

```text
pf_wavelet_density.py       -> couche moteur, aucun acces DB, aucun cockpit
run_wavelet_density_once.py -> couche runner, lit DB read-only, ecrit JSON
output/wavelet_density.json -> interface temporaire
```

Aucune dependance interdite :

```text
- pas de cockpit_* importe dans pf_*
- pas de telegram_* importe dans pf_*
- pas d'ecriture powerflow.db
- pas de BUY/SELL
- pas de decision de trade
```

---

## 11. Etat final de mission

```text
Mission B4 Wavelet Density : LIVREE
Moteur : pret a deposer dans Core/
Runner : pret a deposer dans Core/
JSON : produit localement
Validation locale : OK
Validation DB reelle : a lancer dans workspace Windows
Commit Git : a faire localement avec message cible
```

---

## 12. Checkpoint PowerFlow

```text
B4 legacy autocorr reste disponible.
B4 Wavelet devient candidat upgrade robuste.
La comparaison autocorr_peak reste exposee.
Le moteur gagne une lecture multi-scale plus adaptee aux series non-stationnaires Forex.
La mission ne modifie pas le comportement cockpit existant tant que le runner n'est pas branche a l'orchestrateur.
```

Phrase de fin :

```text
La machine ne predit pas.
Elle percoit la concentration cyclique.
Elle nomme compression, expansion, stabilite ou bruit.
Le trader filtre.
```
