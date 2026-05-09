# 01 — DOCTRINE POWERFLOW V6 ACTIVE

Date : 2026-05-05  
Statut : DOCTRINE ACTIVE — version nettoyée sans restrictions biaisées

## Nature

PowerFlow V6 est un système vivant d’augmentation de perception du trader.

Il n’est pas une nounou, pas une tour de contrôle, pas une administration, pas un robot BUY/SELL, pas un indicateur technique classique.

Il est une extension algorithmique de perception.

```text
PowerFlow voit le flux.
PowerFlow mesure la tension.
PowerFlow nomme l’événement.
PowerFlow alerte vite.
Le trader filtre.
Le trader décide.
```

## Phrase noyau

```text
Voir le flux.
Détecter l’événement.
Alerter vite.
Filtrer humainement.
Décider clairement.
```

## M1

```text
M1 = microfilm vivant.
M1 = naissance.
M1 = inflexion.
M1 = premier basculement.
M1 = niveau tactique essentiel pour scalping.
```

M1 ne doit pas être rejeté par prudence générique.

```text
M1      = naissance / microstructure / inflexion rapide
M5      = confirmation tactique / deuxième jambe
M15     = scénario court / respiration structurée
M30-H1  = gravité / champ porteur
H4      = pression large / contexte supérieur
```

Règle :

```text
Pour scalper, attendre trop de confirmation peut tuer l’information.
```

## Alertes

Une alerte PowerFlow n’est pas un ordre.

Elle peut signaler :

```text
BIRTH
NODE_BIRTH
WATCH
HOT
CONFIRMING
ABSORBING
SECOND_LEG
LATE
CHAOTIC
```

Règles :

```text
Alerte ≠ ordre.
Direction de flux ≠ décision de trade.
Qualifier n’est pas retenir.
Alerter n’est pas ordonner.
```

## Anti-nounou

À retirer :

```text
prudence financière générique
rappels automatiques sur les risques du trading
blocage des alertes précoces
masquage des directions mesurées
sur-filtrage par peur de ressembler à un signal
```

À conserver seulement comme risques techniques :

```text
faux positif
latence
surcharge Telegram
bruit M1
sur-filtrage
invalidation floue
complexité inutile
dette technique
requête SQL trop lente
dépendance circulaire
hardcoding
signature mathématique faible
```

## Temporal Nodes

Les Temporal Nodes ne sont pas une brique à enterrer.

```text
Temporal Nodes = moments où le flux commence à parler.
```

Classification active :

```text
[TEMPORAL_NODES_ACTIVE_LAB]
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
pf_temporal_density.py
pf_temporal_patterns.py
pf_temporal_patterns_cockpit.py
```

Objectif :

```text
auditer
recadrer
tester read-only
rendre lisible
produire un state
connecter progressivement à Telegram selon mode choisi par le trader
```

Règle :

```text
Temporal Node Alert ≠ TemporalWindowActive.
On peut alerter un node avant de déclarer une grande fenêtre temporelle active.
```

## Écosystème IA réel

```text
GPT principal = architecte vivant / intégrateur / challenger / simplificateur
Autre GPT Pro = workspace externe / rapport stratégique
Claude = code / consolidation / rédaction longue / patch ciblé
Perplexity = veille / recherche / éclairage externe
Gemini téléphone = audio / digestion / écoute mobile
Trader = centre vivant / validation / décision
```

Règle :

```text
Aucune IA n’est tour de contrôle.
Les IA sont des partenaires spécialisés.
Le trader orchestre.
```

## Documents

```text
Un document informe.
Il n’enferme pas.
```

Quand une règle semble restrictive :

```text
ACTIVE
À ASSOUPLIR
LEGACY
À SUPPRIMER
```

## Architecture

```text
capture_*   = acquisition / pont MT4 / écrit DB
pf_*        = moteur / calcul / analyse / mémoire
agentic_*   = lecture agentique / nomination / orchestration
cockpit_*   = affichage / lecture / clarification
telegram_*  = transmission d’alertes
DB          = trace / mémoire / comparaison
Trader      = décision finale
```

Règles :

```text
pf_* ne dépend pas de cockpit_*.
cockpit_* ne modifie jamais powerflow.db.
capture_bridge.py reste protégé.
La DB garde la trace, elle ne décide pas.
Le trader valide.
```

## Conclusion

```text
PowerFlow doit être assez structuré pour ne pas dériver,
mais assez libre pour respirer avec le trader.
```
