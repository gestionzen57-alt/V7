# LE_MANIFESTE_DES_REJETS_POWERFLOW

**Version :** Mise à jour 03/05/2026  
**Projet :** PowerFlow V6  
**Objet :** Ce que PowerFlow refuse de devenir, afin de protéger sa vision.

---

## 1. Principe

PowerFlow n’est pas une usine à signaux.  
PowerFlow est un lecteur de flux, de champ, de préparation et de fenêtres temporelles.

Le système doit aider le trader à voir, pas décider à sa place.

```text
La machine perçoit.
Le Cockpit affiche.
L’humain frappe.
```

---

## 2. Rejet du BUY/SELL automatique

PowerFlow rejette les sorties de type :

```text
BUY maintenant
SELL maintenant
entrée obligatoire
direction certaine
```

PowerFlow peut dire :

```text
fenêtre en préparation
gate ouverte
release active
champ contesté
attention haute
```

Mais il ne doit pas remplacer le jugement humain.

---

## 3. Rejet des seuils bruts isolés

PowerFlow rejette :

```text
force > seuil = signal
croisement = signal
densité haute = entrée
```

Un événement n’a de sens que dans son contexte :

```text
timeframe
compression précédente
coalition
antagoniste
personnalité devise
mémoire de zone
permission HTF
```

---

## 4. Rejet de la lecture plate

Le marché n’est pas une ligne.  
Le marché est un organisme.

PowerFlow rejette les lectures du type :

```text
ça monte donc c’est haussier
ça baisse donc c’est baissier
```

PowerFlow lit plutôt :

```text
ça prépare
ça compresse
ça ouvre une porte
ça libère
ça paie
ça rebalancera
```

---

## 5. Rejet du M1 souverain

PowerFlow rejette l’idée que le M1 commande seul.

Le M1 sert à lire :

```text
micro recharge
micro couture
micro réponse
naissance du mouvement
```

Mais il ne remplace pas :

```text
H1 / H4 pour le décor
M30 pour la gate
M15 pour la scène
M5 pour la jambe tactique
```

---

## 6. Rejet de la dominance comme seule vérité

PowerFlow rejette :

```text
pas dominant HTF = pas de scénario
```

Une devise peut ne pas être dominante, mais avoir une fenêtre d’expansion.

Il faut séparer :

```text
DOMINANCE
PERMISSION D’EXPANSION
```

Le Cockpit doit apprendre à afficher cette différence.

---

## 7. Rejet de la densité comme vérité complète

Temporal Density V0.1 est utile, mais elle ne suffit pas.

PowerFlow rejette :

```text
densité NEUTRAL = rien à voir
densité COMPRESSED = signal immédiat
```

Parce qu’une release puissante peut être visible après la compression.

Le système doit intégrer :

```text
mémoire de compression
angle de release
famille qui sort ensemble
devise opposée qui plie
```

---

## 8. Rejet de la surcharge dashboard

PowerFlow rejette les dashboards qui noient le trader.

Le Cockpit doit prioriser :

```text
1. état DB
2. champ dominant
3. fenêtre temporelle
4. gate / release / rebalancement
5. zones à surveiller
```

Le détail profond doit exister, mais dans une couche secondaire.

---

## 9. Rejet de la procédure qui bloque la création

La documentation doit protéger le noyau, pas tuer l’observation.

PowerFlow accepte :

```text
observation brute
vocabulaire DRAFT
lexique vivant
mise à jour de fin de session
```

PowerFlow rejette :

```text
procédure lourde avant toute idée
codage avant compréhension
validation administrative qui bloque le trader
```

---

## 10. Rejet de la continuité inventée

Si la DB a un trou ou manque l’amont, PowerFlow doit le dire.

Il rejette :

```text
inventer une continuité
forcer un film absent
supposer une préparation non mesurée
```

Le Cockpit doit afficher :

```text
données insuffisantes
amont absent
lecture partielle
DB stale
```

---

## 11. Rejet de Telegram trop tôt

PowerFlow rejette les alertes Telegram précipitées.

Avant Telegram, il faut savoir :

```text
qu’est-ce qui mérite vraiment interruption ?
qu’est-ce qui reste visuel ?
qu’est-ce qui est bruit ?
qu’est-ce qui est fenêtre ?
```

Les alertes doivent venir après stabilisation du langage.

---

## 12. Principe final

PowerFlow refuse d’être un signal.

PowerFlow veut devenir :

```text
une fenêtre temporelle lisible
sur l’organisme vivant du marché.
```

Phrase manifeste :

```text
PowerFlow ne doit pas dire “fais”.
PowerFlow doit dire “regarde ici, l’énergie se prépare ou vient de libérer”.
```
