# PATCH LEXIQUE — Lab Engine V7.2

**Date :** 2026-05-10  
**Statut :** Patch lexique V0.1 — Lab Engine V7.2  
**Rôle :** Ajouter les termes apparus avec le nouveau Lab V7.2

---

## 1. LAB_ENGINE_V72

Moteur de replay expérimental PowerFlow V7.2.

Définition :

```text
Module qui rejoue une fenêtre historique,
reconstruit les frames,
enrichit les métriques,
détecte les scènes,
mesure les causes / conséquences,
et produit des rapports lisibles.
```

Ne décide pas.

Ne produit pas de BUY/SELL.

---

## 2. REPLAY_RAW

Reconstruction brute d’une fenêtre DB.

Contient :

```text
minute
rows_count
timeframes
lignes DB par TF
```

Rôle :

```text
Matière première historique.
```

---

## 3. REPLAY_ENRICHED

Replay enrichi par métriques PowerFlow.

Contient selon disponibilité :

```text
B1_regime
B3_kinematics
B4_density
B5_relation
EIE_zone
B7_resonance
scene_context
structural_footprint
technical_risks
```

Rôle :

```text
Transformer les frames brutes en frames comportementales.
```

---

## 4. CAUSE_CONSEQUENCE

Bloc d’analyse avant / pendant / après.

Structure :

```text
before      = fenêtre avant événement
at_event    = moment t0
after       = fenêtre après événement
outcome     = conséquence observée
```

Rôle :

```text
Mesurer ce qui précède et suit une scène.
```

---

## 5. KEY_EVENT

Événement retenu pour lecture condensée.

Important :

```text
Un key event n’est pas une alerte filtrée.
C’est un repère de lecture.
```

Les événements non retenus restent disponibles dans :

```text
events_index_full.json
```

---

## 6. EVENTS_INDEX_FULL

Index complet des événements.

Rôle :

```text
Conserver la traçabilité totale.
Prouver qu’aucune scène n’a été supprimée.
```

Doctrine :

```text
Condensation ≠ censure
```

---

## 7. KEY_SCENE_CLUSTER

Regroupement de scènes proches ou répétées.

Rôle :

```text
Éviter la lecture minute par minute quand plusieurs frames racontent le même épisode.
```

---

## 8. TF_PROFILE

Profil de timeframes utilisé par le Lab.

Profils standards :

```text
HTF = W / D / H4
MTF = H1 / M30 / M15
LTF = M15 / M5 / M1
FULL = tout
CUSTOM = manuel
```

Rôle :

```text
Adapter la lecture au niveau d’observation.
```

---

## 9. HTF_PROFILE

Profil stratégique.

```text
W
D
H4
```

Rôle :

```text
Gravité supérieure.
Champ de bataille stratégique.
Contexte profond.
```

---

## 10. MTF_PROFILE

Profil principal de lecture.

```text
H1
M30
M15
```

Rôle :

```text
Lecture centrale du film.
Battle window.
Structure exploitable sans bruit M1 permanent.
```

---

## 11. LTF_PROFILE

Profil tactique.

```text
M15
M5
M1
```

Rôle :

```text
Lecture tactique.
Naissance.
Relais.
Microfilm.
```

---

## 12. M1_MICROSCOPE

Définition :

```text
M1 n’est pas du bruit par défaut.
M1 est le microscope du flux.
```

Règle :

```text
M1 doit être activé autour des moments sensibles,
pas forcément imposé au film principal.
```

---

## 13. M1_MODE_OFF

Mode où M1 est retiré du film principal.

Usage :

```text
Lecture MTF propre.
Analyse macro / battle window sans torrent micro.
```

---

## 14. M1_MODE_FULL

Mode où M1 est inclus partout.

Usage :

```text
Microfilm complet.
Inspection détaillée.
Peut être très bavard.
```

---

## 15. M1_MODE_ZOOM

Mode où M1 est retiré du film principal puis relancé autour des moments clés.

Usage recommandé :

```text
MTF pour trouver les moments.
M1 zoom pour comprendre la micro-mécanique.
```

---

## 16. M1_ZOOM_WINDOW

Fenêtre M1 courte autour d’un key moment.

Exemple :

```text
t0 - 5 minutes
t0 + 10 minutes
```

Rôle :

```text
Voir naissance / absorption / relais / contre-souffle sans noyer le film global.
```

---

## 17. M1_EPISODE

Fusion de plusieurs zooms M1 proches ou chevauchants.

Rôle :

```text
Transformer plusieurs zooms voisins en une histoire micro lisible.
```

Exemple :

```text
Zoom 10:35 → 10:50
Zoom 10:40 → 10:55
Zoom 10:45 → 11:00

devient :

M1_EPISODE_01
10:35 → 11:00
```

---

## 18. M1_EPISODE_MERGER

Module V0.4 du Lab.

Rôle :

```text
Fusionner les zooms M1 voisins.
Créer m1_episodes.json.
Créer film_m1_episodes.md.
Créer lab_report_m1_episodes.html.
```

Doctrine :

```text
Fusion de lecture seulement.
Aucune suppression du microfilm.
```

---

## 19. STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE

Empreinte comportementale compatible avec un flux structuré.

Important :

```text
Candidate ≠ certitude institutionnelle.
```

Toujours accompagnée de risques techniques comme :

```text
INFERENCE_ONLY
NO_VOLUME_DATA
NO_ORDERBOOK_DATA
```

---

## 20. COMPRESSION_REAL_CANDIDATE

Compression potentiellement structurelle.

Signature typique :

```text
B4 compressing
B1 cohérent
B5 non neutre
EIE actif ou pré-extrême
B3 noise faible ou acceptable
```

---

## 21. COMPRESSION_FAKE_RISK

Compression potentiellement fausse / bruitée.

Signature typique :

```text
B4 compressing
B1 range ou incertain
B5 neutral
EIE absent
B3 noise élevé
```

---

## 22. FILM_BEHAVIORAL

Film comportemental complet.

Rôle :

```text
Raconter toutes les scènes détectées.
```

Peut être dense.

---

## 23. FILM_KEY_EVENTS

Film condensé.

Rôle :

```text
Raconter seulement les événements clés de lecture.
```

Ne remplace pas le film complet.

---

## 24. FILM_M1_EPISODES

Film micro condensé.

Rôle :

```text
Raconter les épisodes M1 fusionnés.
```

C’est le meilleur fichier pour comprendre ce que M1 raconte autour d’une scène.

---

## 25. RÈGLE LAB V7.2

```text
Le Lab ne doit pas décider.
Le Lab doit rejouer, enrichir, nommer, mesurer et raconter.
```

---

## 26. RÈGLE M1

```text
M1 est central pour la naissance.
Mais M1 doit être isolé en microscope quand la lecture principale demande de la clarté.
```

---

## 27. RÈGLE DE LECTURE

```text
HTF = gravité supérieure
MTF = carte du champ
LTF = tactique
M1 = microscope
M1 Episode = histoire micro lisible
```

---

## 28. Phrase lexique

```text
Le dashboard montre ce que PowerFlow voit maintenant.
Le Lab montre comment PowerFlow comprend une séquence.

La carte se lit en MTF.
La naissance s’inspecte en M1.
La mémoire apprend par scènes.
La conséquence se mesure après l’événement.
```
