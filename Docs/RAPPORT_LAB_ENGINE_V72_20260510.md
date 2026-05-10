# RAPPORT — PowerFlow V7.2 Lab Engine

**Date :** 2026-05-10  
**Statut :** Lab V7.2 opérationnel / prêt pour expérimentation de séquences  
**Dernier état Git connu :** repo propre, branch `main` à jour avec `origin/main`  
**Dernier checkpoint :** Lab V7.2 V0.4 validé et pushé

---

## 1. Résumé exécutif

Le Lab Engine V7.2 est maintenant en place et utilisable pour rejouer des séquences historiques.

Il permet de passer de :

```text
powerflow.db
  ↓
replay brut
  ↓
replay enrichi
  ↓
scènes détectées
  ↓
causes / conséquences
  ↓
métriques
  ↓
film lisible
  ↓
zoom M1 optionnel
  ↓
épisodes M1 fusionnés
```

Le Lab ne remplace pas le dashboard.

```text
Dashboard = lecture live / état courant
Lab       = replay / expérimentation / compréhension des séquences
```

Le Lab est maintenant adapté à ta méthode :

```text
voir le flux
rejouer une séquence
comprendre comment PowerFlow l’a lue
mesurer ce qui a suivi
améliorer la grammaire
```

---

## 2. Doctrine du Lab

Le Lab respecte la doctrine PowerFlow :

```text
- aucun BUY/SELL
- aucune décision de trade
- aucun filtrage destructif
- aucune écriture dans powerflow.db
- aucun appel direct au module legacy pf_flow_nodes.py
- les footprints sont candidates, jamais des certitudes institutionnelles
- M1 est conservé comme microscope, pas imposé comme film principal
```

Le Lab mesure, nomme, rejoue et compare.

Le trader juge.

---

## 3. Ce qui a été construit

## 3.1 Lab V0.1 — Replay + Cause / Consequence Engine

Fichiers :

```text
Core/pf_lab_engine_v72.py
Core/run_lab_engine_v72_once.py
scripts/validate_lab_engine_v72.ps1
README_LAB_ENGINE_V72.md
```

Rôle :

```text
Créer un run complet de lab depuis powerflow.db en read-only.
```

Sorties :

```text
output/lab_runs/<run_id>/replay_raw.json
output/lab_runs/<run_id>/replay_enriched.json
output/lab_runs/<run_id>/scene_timeline.json
output/lab_runs/<run_id>/cause_consequence.json
output/lab_runs/<run_id>/lab_metrics.json
output/lab_runs/<run_id>/film_behavioral.md
output/lab_runs/<run_id>/lab_report.md
output/lab_runs/<run_id>/lab_report.html
```

Ce que ça fait :

```text
- reconstruit une fenêtre historique
- enrichit les frames avec des proxys B1/B3/B4/B5/EIE/B7
- détecte des scènes
- mesure avant / pendant / après
- produit un film comportemental
```

Statut :

```text
VALIDÉ
```

Limite connue :

```text
La V0.1 voit beaucoup.
Elle peut produire trop de scènes minute par minute.
```

---

## 3.2 Lab V0.2 — Key Event Selector

Fichiers :

```text
Core/pf_lab_event_selector_v72.py
Core/run_lab_event_selector_v72_once.py
scripts/validate_lab_event_selector_v72.ps1
README_LAB_EVENT_SELECTOR_V72.md
```

Rôle :

```text
Créer une couche lisible au-dessus du microfilm complet.
```

Sorties ajoutées :

```text
events_index_full.json
key_events.json
key_events.csv
key_scene_clusters.json
film_key_events.md
lab_report_key_events.html
event_selector_metrics.json
```

Principe :

```text
events_index_full.json = tous les événements
key_events.json        = les événements sélectionnés pour lecture
key_events.csv         = lecture Excel
film_key_events.md     = film condensé
```

Point important :

```text
La sélection n’est pas une censure.
Le microfilm complet reste disponible.
```

Statut :

```text
VALIDÉ
```

Limite connue :

```text
La V0.2 était encore trop permissive.
Elle conservait trop de scènes proches, surtout à cause du M1.
```

---

## 3.3 Lab V0.3 — Timeframe Profiles + M1 Modes

Fichiers :

```text
Core/pf_lab_tf_profiles_v72.py
Core/run_lab_profile_v72_once.py
scripts/validate_lab_tf_profiles_v72.ps1
README_LAB_TF_PROFILES_V72.md
```

Rôle :

```text
Ajouter des profils de timeframes et isoler M1.
```

Profils :

```text
HTF = W / D / H4       = 10080,1440,240
MTF = H1 / M30 / M15   = 60,30,15
LTF = M15 / M5 / M1    = 15,5,1
FULL = tout
CUSTOM = manuel
```

Modes M1 :

```text
--m1 off
  M1 retiré du film principal.

--m1 full
  M1 inclus partout.

--m1 zoom
  M1 retiré du film principal,
  puis relancé uniquement autour des key moments.
```

Phrase centrale :

```text
M1 n’est pas du bruit.
M1 est le microscope.
Mais le microscope ne doit pas remplacer la carte du champ.
```

Statut :

```text
VALIDÉ
```

---

## 3.4 Lab V0.4 — M1 Episode Merger

Fichiers :

```text
Core/pf_lab_m1_episode_merger_v72.py
Core/run_lab_m1_episode_merger_v72_once.py
scripts/validate_lab_m1_episode_merger_v72.ps1
README_LAB_M1_EPISODE_MERGER_V72.md
```

Rôle :

```text
Fusionner les zooms M1 voisins en épisodes lisibles.
```

Sorties ajoutées :

```text
m1_episodes.json
film_m1_episodes.md
lab_report_m1_episodes.html
m1_episode_merger_metrics.json
```

Résultat validé sur le test :

```text
zoom_count_input: 5
episode_count_output: 1
compression_ratio: 0.2
main_scene: ZONE_BREATH_COMPRESSION
main_compression: COMPRESSION_REAL_CANDIDATE
main_footprint: STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE
main_outcome: RELEASE_CONFIRMED
```

Interprétation :

```text
Les 5 zooms M1 voisins ont été regroupés en 1 épisode M1 lisible.
```

Statut :

```text
VALIDÉ + COMMIT + PUSH
```

---

## 4. Architecture de lecture recommandée

## 4.1 Lecture principale

Pour comprendre une séquence sans être noyé par M1 :

```powershell
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

Lecture :

```text
MTF = H1/M30/M15
M1 retiré
film principal plus propre
```

---

## 4.2 Lecture tactique avec zoom M1

Pour inspecter les naissances après avoir trouvé les moments importants :

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

Puis fusionner les zooms M1 :

```powershell
python Core\run_lab_m1_episode_merger_v72_once.py --latest --pretty
```

Lecture :

```text
LTF = M15/M5/M1
M1 isolé autour des moments clés
zooms fusionnés en épisodes
```

---

## 4.3 Microfilm complet

À utiliser seulement si tu veux tout voir :

```powershell
python Core\run_lab_profile_v72_once.py `
  --db Core\powerflow.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 11:00 `
  --tf-profile LTF `
  --m1 full `
  --pretty
```

Lecture :

```text
M1 partout.
Très riche.
Peut devenir trop bavard.
À utiliser comme microscope complet, pas comme lecture principale.
```

---

## 5. Fichiers à lire en priorité dans un run

Dans :

```text
output/lab_runs/<run_id>/
```

Lire dans cet ordre :

```text
1. lab_report_key_events.html
2. film_key_events.md
3. key_events.csv
4. lab_report_m1_episodes.html
5. film_m1_episodes.md
6. m1_episodes.json
7. cause_consequence.json
8. replay_enriched.json
```

Lecture rapide :

```text
lab_report_key_events.html
  = vue synthétique des moments importants

film_key_events.md
  = narration condensée

key_events.csv
  = comparaison rapide / Excel

lab_report_m1_episodes.html
  = épisodes M1 lisibles

film_m1_episodes.md
  = histoire micro des épisodes

cause_consequence.json
  = mesure avant / pendant / après
```

---

## 6. Ce que le Lab permet maintenant

Le Lab permet de tester des hypothèses comme :

```text
Quand B4 compresse, est-ce réel ou fake ?
Quand B5 devient divergent, que fait le champ ?
Quand EIE apparaît, est-ce suivi d’une release ?
Quand M1 montre un first detachment, est-ce que M5/M15 relaie ?
Quand une absorption apparaît, y a-t-il follow-through ?
Quand le prix lag, y a-t-il catch-up ?
Quand une footprint candidate apparaît, qu’est-ce qui suit ?
```

Il permet aussi de comparer :

```text
séquence calme asiatique
séquence London
séquence NY overlap
compression fake
compression réelle
pullback absorbé
counter breath
second leg
price lag / catch-up
```

---

## 7. Limites connues

Le Lab V7.2 est exploitable, mais encore V0.x.

Limites actuelles :

```text
- Les enrichissements B1/B3/B4/B5/EIE/B7 sont encore souvent des proxys.
- Le HMM B1+ n’est pas rejoué frame par frame.
- B4 Wavelet complet n’est pas encore recalculé sur chaque fenêtre.
- EIE complet est approximé dans certains runs.
- Les footprints restent INFERENCE_ONLY.
- Pas de volume / orderbook.
- Les résultats doivent être lus comme observations, pas certitudes.
```

C’est volontairement exposé dans :

```text
technical_risks
```

---

## 8. Statut Git / Administration

Derniers éléments pushés :

```text
Lab V0.1
Lab V0.2
Lab V0.3
Lab V0.4
semantic_audit_gravity_zones_v72.py
```

Dernier état confirmé :

```text
branch main
up to date with origin/main
working tree clean
```

---

## 9. Décision finale

Le Lab V7.2 est maintenant suffisamment structuré pour commencer l’expérimentation manuelle de séquences.

Statut :

```text
GO TEST SÉQUENCES
```

Prochaine étape non urgente :

```text
Observer plusieurs séquences.
Noter les incohérences.
Identifier les scènes mal nommées.
Comparer compression réelle / fake.
Comparer MTF sans M1 vs LTF avec M1 zoom.
```

---

## 10. Phrase de clôture

```text
PowerFlow voit le flux en live avec le dashboard.
PowerFlow rejoue le passé avec le Lab.

Le Lab V7.2 donne maintenant :
la carte du champ,
les moments clés,
le microscope M1,
les épisodes lisibles,
et les conséquences observées.

Ce n’est pas une machine à décider.
C’est une machine à comprendre.
```
