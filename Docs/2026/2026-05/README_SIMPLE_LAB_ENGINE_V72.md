# README SIMPLE — PowerFlow V7.2 Lab

## 1. À quoi sert le Lab ?

Le Lab sert à rejouer une séquence passée pour comprendre comment PowerFlow la lit.

Il permet de voir :

```text
- les scènes détectées
- les compressions réelles ou fake
- les déséquilibres leader/follower
- les pullbacks absorbés
- les counter breaths
- les second legs
- les footprints candidates
- ce qui s’est passé après l’événement
```

Le Lab ne donne pas d’ordre.

Il ne fait pas BUY/SELL.

Il aide à comprendre.

---

## 2. Commande recommandée pour commencer

Lecture principale propre, sans M1 :

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT

python Core\run_lab_profile_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tf-profile MTF `
  --m1 off `
  --pretty
```

Ensuite ouvre :

```text
output\lab_runs\<dernier_run>\lab_report_key_events.html
```

Puis :

```text
output\lab_runs\<dernier_run>\film_key_events.md
```

---

## 3. Pour zoomer avec M1

Quand tu veux voir la micro-mécanique :

```powershell
python Core\run_lab_profile_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tf-profile LTF `
  --m1 zoom `
  --max-m1-zooms 5 `
  --pretty
```

Puis fusionner les zooms proches :

```powershell
python Core\run_lab_m1_episode_merger_v72_once.py --latest --pretty
```

Ensuite ouvre :

```text
output\lab_runs\<dernier_run>\lab_report_m1_episodes.html
```

Puis :

```text
output\lab_runs\<dernier_run>\film_m1_episodes.md
```

---

## 4. Profils de timeframes

```text
HTF = W / D / H4
MTF = H1 / M30 / M15
LTF = M15 / M5 / M1
FULL = tout
CUSTOM = manuel
```

Usage simple :

```text
MTF + m1 off
  = lecture principale

LTF + m1 zoom
  = inspection des moments clés

LTF + m1 full
  = microfilm complet, très détaillé
```

---

## 5. Fichiers importants

Dans chaque run :

```text
lab_report_key_events.html
  Vue principale condensée.

film_key_events.md
  Narration condensée.

key_events.csv
  Table Excel.

cause_consequence.json
  Analyse avant / pendant / après.

lab_report_m1_episodes.html
  Épisodes M1 lisibles.

film_m1_episodes.md
  Narration M1 condensée.

m1_episodes.json
  Données structurées des épisodes M1.

replay_enriched.json
  Toutes les frames enrichies.

events_index_full.json
  Tous les événements, même ceux non retenus dans la lecture condensée.
```

---

## 6. Workflow conseillé

```text
1. Lancer MTF sans M1.
2. Lire lab_report_key_events.html.
3. Repérer un moment intéressant.
4. Lancer LTF avec m1 zoom.
5. Fusionner les épisodes M1.
6. Lire lab_report_m1_episodes.html.
7. Noter ce que PowerFlow comprend bien / mal.
8. Ajuster plus tard la grammaire ou les scènes.
```

---

## 7. Exemple de lecture

Si le Lab sort :

```text
ZONE_BREATH_COMPRESSION
COMPRESSION_REAL_CANDIDATE
STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE
RELEASE_CONFIRMED
```

Lecture :

```text
PowerFlow voit une compression de zone qui ressemble à une compression réelle,
avec empreinte structurelle candidate,
et une release observée après.
```

Ce n’est pas une certitude institutionnelle.

C’est une observation comportementale.

---

## 8. Si le Lab parle trop

Utilise :

```text
--tf-profile MTF --m1 off
```

Si tu veux voir la naissance :

```text
--tf-profile LTF --m1 zoom
```

Si tu veux tout voir :

```text
--tf-profile LTF --m1 full
```

---

## 9. Commandes utiles

Dernier run avec profils TF :

```powershell
python Core\run_lab_profile_v72_once.py --db Core\powerflow.db --symbol GBPUSD --date 2026-05-08 --start 09:00 --end 11:00 --tf-profile MTF --m1 off --pretty
```

Dernier run M1 zoom :

```powershell
python Core\run_lab_profile_v72_once.py --db Core\powerflow.db --symbol GBPUSD --date 2026-05-08 --start 09:00 --end 11:00 --tf-profile LTF --m1 zoom --pretty
```

Fusion M1 épisodes :

```powershell
python Core\run_lab_m1_episode_merger_v72_once.py --latest --pretty
```

Fermer session :

```powershell
.\pf_close_session.ps1 "V7.2: lab tests session"
```

---

## 10. Phrase à retenir

```text
MTF donne la carte.
M1 donne le microscope.
Le Lab donne le replay.
Le trader donne le jugement.
```
