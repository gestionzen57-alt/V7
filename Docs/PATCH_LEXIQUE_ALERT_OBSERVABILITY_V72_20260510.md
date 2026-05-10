# PATCH LEXIQUE — PowerFlow V7.2 — Alert Observability Metrics

**Date :** 2026-05-10  
**Brique :** Alert Observability Metrics  
**Statut :** À intégrer au lexique V7.2  
**Doctrine :** Observabilité non bloquante

---

## 1. ALERT_OBSERVABILITY_METRICS

Brique de mesure non bloquante du champ d’alertes PowerFlow.

Elle mesure la distribution, la couverture, la complétude et les doublons des alertes produites.

Elle ne filtre pas les alertes.  
Elle ne valide pas les trades.  
Elle ne supprime pas les signaux précoces.  
Elle ne décide pas.

Produit :

```text
output/alert_metrics.json
output/alert_metrics.md
```

---

## 2. ALERT_METRICS_JSON

Fichier JSON produit par `pf_alert_observability_metrics.py`.

Contient les métriques brutes d’observabilité :

```text
total_alerts
distribution
coverage
duplicates
technical_notes
technical_risks
```

Utilisé par le dashboard pour afficher la santé du champ d’alertes.

---

## 3. ALERT_METRICS_MD

Rapport Markdown humain produit par le runner d’observabilité.

Il résume :

```text
- total alertes
- distribution par niveau
- distribution par maturité
- distribution par type
- couverture des contextes
- risques techniques
- doublons
```

Ce rapport est lisible sans code.

---

## 4. METRICS_ONLY

Flag indiquant que la brique ne produit que des métriques.

Valeur attendue :

```json
"metrics_only": true
```

Signifie :

```text
Le module observe.
Il ne filtre pas.
Il ne décide pas.
```

---

## 5. NO_FILTERING

Flag doctrinal indiquant que la brique ne supprime aucune alerte.

Valeur attendue :

```json
"no_filtering": true
```

Ce flag interdit toute logique du type :

```text
alerte refusée
alerte cachée
alerte bloquée
alerte invalidée
```

---

## 6. NO_TRADE_DECISION

Flag doctrinal indiquant que la brique ne donne aucun jugement de trade.

Valeur attendue :

```json
"no_trade_decision": true
```

Interdit :

```text
BUY
SELL
do not trade
trade valid
trade invalid
should ignore
```

---

## 7. ALERT_DISTRIBUTION

Distribution des alertes selon plusieurs dimensions :

```text
by_alert_type
by_level
by_maturity
by_symbol
by_regime
by_session
technical_risks
```

Permet de voir comment le moteur alerte.

Ne juge pas si cette distribution est bonne ou mauvaise.

---

## 8. BY_ALERT_TYPE

Compteur des alertes par type comportemental.

Exemples :

```text
FIRST_DETACHMENT_MICRO
EIE_LEADER_CONFIRMED
CASCADE_BUILDING_ALERT
SEQUENCE_VELOCITY_HIGH
```

Permet de voir quelles perceptions dominent la session.

---

## 9. BY_LEVEL

Compteur des alertes par niveau :

```text
HOT
WATCH
INFO
UNKNOWN
```

Ne doit pas être utilisé pour censurer.  
Sert seulement à observer la charge d’attention transmise.

---

## 10. BY_MATURITY

Compteur des alertes par maturité :

```text
BIRTH
EARLY
CANDIDATE
CONFIRMED
UNKNOWN
```

Important pour PowerFlow car une alerte précoce doit être exposée, pas censurée.

---

## 11. BY_SYMBOL

Compteur des alertes par symbole ou instrument :

```text
GBPUSD
EURUSD
USDJPY
XAUUSD
UNKNOWN
```

Utile pour la lecture multi-symboles.

---

## 12. BY_REGIME

Compteur des alertes par régime de marché :

```text
COMPRESSION
TENDANCE
RANGE
TRANSITION
UNKNOWN
```

Permet de voir dans quel climat les alertes apparaissent.

---

## 13. BY_SESSION

Compteur des alertes par session :

```text
ASIAN
LONDON
NY
OVERLAP
UNKNOWN
```

Permet de voir la distribution temporelle/sessionnelle du champ d’alertes.

---

## 14. CONTEXT_COVERAGE

Mesure la présence des contextes dans les alertes.

Champs :

```text
alert_type_present_ratio
level_present_ratio
maturity_present_ratio
symbol_present_ratio
regime_context_present_ratio
session_context_present_ratio
technical_risks_present_ratio
```

Ce sont des ratios de complétude, pas des scores de validité trade.

---

## 15. REGIME_CONTEXT_PRESENT_RATIO

Ratio d’alertes contenant un régime exploitable.

Exemple :

```json
"regime_context_present_ratio": 0.87
```

Si bas, note technique possible :

```text
REGIME_CONTEXT_PARTIAL
```

---

## 16. SESSION_CONTEXT_PRESENT_RATIO

Ratio d’alertes contenant un contexte de session.

Exemple :

```json
"session_context_present_ratio": 0.64
```

Si bas, note technique possible :

```text
SESSION_CONTEXT_PARTIAL
```

---

## 17. TECHNICAL_RISKS_PRESENT_RATIO

Ratio d’alertes contenant au moins un risque technique nommé.

Exemples de risques :

```text
M1_NOISE_POSSIBLE
EARLY_MATURITY
RELAY_ABSENT
LOW_ALERT_SAMPLE
```

Ce champ vérifie que la machine expose ses limites techniques.

---

## 18. ALERT_KEY

Clé stable construite pour mesurer les doublons.

Structure :

```text
alert_type | symbol | level | maturity | regime | session
```

Exemple :

```text
FIRST_DETACHMENT_MICRO|GBPUSD|HOT|BIRTH|COMPRESSION|LONDON
```

Sert à mesurer la répétition d’un même type de perception.

---

## 19. DUPLICATE_RATIO

Ratio de répétition des alertes sur la fenêtre observée.

Calcul conceptuel :

```text
1 - unique_alert_keys / total_alerts
```

Un ratio élevé indique un champ répétitif.

Ce n’est pas un filtre.  
C’est une information de lisibilité.

---

## 20. TOP_DUPLICATE_KEYS

Liste des clés d’alerte les plus répétées.

Exemple :

```json
[
  {
    "alert_key": "FIRST_DETACHMENT_MICRO|GBPUSD|HOT|BIRTH|COMPRESSION|LONDON",
    "count": 4
  }
]
```

Permet d’identifier les perceptions répétées.

---

## 21. NO_ALERTS_IN_WINDOW

Note technique indiquant qu’aucune alerte n’est présente dans la fenêtre observée.

Ce n’est pas une erreur.

Causes possibles :

```text
marché fermé
daemon non actif
queue vide
aucun événement récent
fenêtre trop courte
```

---

## 22. QUEUE_NOT_FOUND

Note technique indiquant que le fichier de queue d’alertes n’a pas été trouvé.

Action :

```text
vérifier output/behavioral_alert_queue.json
vérifier Core/output/behavioral_alert_queue.json
vérifier daemon alert mapper / confluence
```

---

## 23. NO_ALERT_LIST_FOUND_IN_JSON

Note technique indiquant que le fichier JSON existe mais ne contient pas de liste d’alertes directement exploitable.

Action :

```text
observer le format réel du JSON
ajouter un parseur spécifique si nécessaire
```

---

## 24. REGIME_CONTEXT_PARTIAL

Note technique indiquant que toutes les alertes ne contiennent pas encore `regime_context`.

Ce n’est pas une invalidation.

Cela indique une couverture partielle du contexte B1/B1+.

---

## 25. SESSION_CONTEXT_PARTIAL

Note technique indiquant que toutes les alertes ne contiennent pas encore `session_context`.

Ce n’est pas une invalidation.

Cela indique une couverture partielle de l’overlay sessionnel.

---

## 26. MATURITY_PARTIAL

Note technique indiquant que certaines alertes n’exposent pas leur maturité.

La maturité attendue est :

```text
BIRTH
EARLY
CANDIDATE
CONFIRMED
```

---

## 27. TECHNICAL_RISKS_PARTIAL

Note technique indiquant que peu d’alertes exposent des risques techniques.

Ce n’est pas une raison pour bloquer les alertes.

Cela indique que la lisibilité technique peut être enrichie.

---

## 28. HIGH_DUPLICATE_RATIO

Note technique indiquant une forte répétition des mêmes clés d’alerte.

Ce n’est pas un filtre.

Le trader peut vouloir voir les répétitions, car une répétition peut signaler :

```text
persistance
saturation
compression
champ bloqué
alerte trop bavarde
```

La brique expose. Le trader juge.

---

## 29. LOW_ALERT_SAMPLE

Note technique indiquant un échantillon faible d’alertes.

Typique :

```text
self-test
week-end
marché fermé
daemon non actif
faible activité
```

---

## 30. OBSERVABILITY_NOT_VALIDATION

Principe doctrinal :

```text
La brique ne valide pas une alerte.
Elle observe la manière dont PowerFlow alerte.
```

Elle ne doit jamais produire :

```text
trade_valid
alert_allowed
should_ignore
bad_alert
```

---

## 31. ALERT_FIELD_COMPLETENESS

Notion de complétude des champs d’alerte.

Champs observés :

```text
alert_type
level
maturity
symbol
regime_context
session_context
technical_risks
```

Permet de savoir si les alertes sont suffisamment renseignées pour le cockpit et le trader.

---

## 32. NON_BLOCKING_METRICS

Principe selon lequel les métriques ne bloquent jamais la perception.

Même si :

```text
session_context manquant
technical_risks partiels
duplicate_ratio élevé
queue vide
```

la brique ne doit pas empêcher les alertes de sortir.

---

## 33. DASHBOARD_ALERT_OBSERVABILITY_CARD

Card dashboard recommandée pour afficher `alert_metrics.json`.

Champs conseillés :

```text
total_alerts
by_level
by_maturity
regime_context_present_ratio
session_context_present_ratio
technical_risks_present_ratio
duplicate_ratio
technical_notes
```

Objectif :

```text
Voir comment la machine alerte.
Ne pas décider à la place du trader.
```

---

## 34. RÈGLE ANTI-LIMITANTE

Règle centrale :

```text
Mesurer oui.
Qualifier oui.
Compter oui.
Exposer oui.
Visualiser oui.

Filtrer non.
Censurer non.
Juger non.
Décider non.
```

---

## 35. PHRASE LEXIQUE

```text
Alert Observability Metrics est le miroir du champ d’alertes.
Il montre comment PowerFlow parle.
Il ne dit pas si le trader doit agir.
```

---

*Patch lexique généré pour intégration PowerFlow V7.2.*
