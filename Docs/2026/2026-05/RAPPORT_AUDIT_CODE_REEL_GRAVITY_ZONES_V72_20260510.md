# RAPPORT D’AUDIT CODE RÉEL — Gravity / Zones / Footprints — PowerFlow V7.2

**Date :** 2026-05-10  
**Statut :** Audit code réel après scan sémantique  
**Objet :** Vérification des red flags Gravity / Zones / Institutional Footprint avant codage du Lab Engine V7.2  
**Repo :** `C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT`

---

## 1. Résumé exécutif

Le scanner sémantique avait remonté :

```text
classical_zone_red_flags:
  - Core\pf_temporal_node_state.py

architecture_red_flags:
  - Core\pf_temporal_node_state.py
  - Core\pf_flow_nodes.py

institutional_red_flags:
  - Core\pf_flow_nodes.py
  - Core\pf_behavioral_alert_mapper.py
```

Après inspection des lignes exactes, la lecture est plus précise :

```text
pf_temporal_node_state.py       → faux positif majoritaire, fichier sain, read-only confirmé
pf_behavioral_alert_mapper.py   → faux positif protecteur, fichier sain, doctrine anti BUY/SELL explicite
pf_flow_nodes.py                → vrai point d’attention architecture : ancien module legacy qui écrit en DB
```

Verdict :

```text
Aucune preuve de mauvaise sémantique institutionnelle active.
Aucune preuve que B5 Spearman déduise leader/follower à tort dans les lignes inspectées.
Le vrai risque est architectural / legacy autour de pf_flow_nodes.py.
```

Décision :

```text
Ne pas modifier pf_temporal_node_state.py.
Ne pas modifier pf_behavioral_alert_mapper.py.
Classer pf_flow_nodes.py comme LEGACY WRITE MODULE, à ne pas utiliser comme source principale du Lab V7.2 sans wrapper read-only.
```

---

## 2. Analyse fichier par fichier

---

# 2.1 Core/pf_temporal_node_state.py

## Red flag initial

Le scanner avait détecté :

```text
classical_zone_red_flags
architecture_red_flags
```

## Lignes inspectées

### Ligne 570

```python
# M5 support directionnel de la paire.
```

Puis :

```python
m5_supports_detachment = False
```

Et utilisation :

```python
if m5_supports_detachment:
    rc_ok.append("m5_direction_support")
elif detachment_found:
    rc_flags.append("m5_direction_not_confirming")
```

## Lecture

Ici, le mot `support` ne signifie pas support/résistance chartiste.

Il signifie :

```text
M5 soutient-il / relaie-t-il le détachement détecté ?
```

Donc c’est un faux positif lexical.

Interprétation PowerFlow correcte :

```text
M5 relay support
M5 direction confirms detachment
M5 direction does not confirm detachment
```

Cela est aligné avec la doctrine :

```text
M1 = microfilm / naissance
M5 = relais tactique
```

## Recommandation lexicale éventuelle

Pour éviter les faux positifs futurs, on pourrait renommer plus tard :

```text
m5_supports_detachment
```

en :

```text
m5_relays_detachment
```

Mais ce n’est **pas urgent**, car le fichier est stable et ne doit pas être modifié sans nécessité.

---

## Read-only / architecture

Lignes inspectées :

```python
def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    if db_path.is_absolute():
        ...
    else:
        uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)
```

Et commentaire :

```python
The module intentionally does not import cockpit_* or telegram_*.
It reads SQLite, computes a small temporal state, and returns JSON-ready data.
```

## Lecture

Le scanner a remonté `sqlite3.connect`, mais l’inspection confirme :

```text
mode=ro
read-only
pas cockpit
pas telegram
```

Donc le red flag architecture est un faux positif.

## Verdict pf_temporal_node_state.py

```text
Statut : SAIN
Risque : faible
Action : ne pas modifier
Note : éventuel renommage futur support → relay si besoin documentaire
```

---

# 2.2 Core/pf_behavioral_alert_mapper.py

## Red flag initial

Le scanner avait détecté :

```text
institutional_red_flags
```

## Lignes inspectées

On trouve :

```python
- Energy ne produit jamais BUY/SELL ni HOT seule
```

et :

```python
# Jamais de BUY/SELL. Jamais de DB. Jamais de Telegram direct.
```

et :

```python
"buy_sell_output": False
```

## Lecture

Le scanner a détecté `BUY/SELL`, mais les occurrences sont des garde-fous doctrinaux.

Ce n’est pas une dérive.

Au contraire, le fichier affirme explicitement :

```text
pas de BUY/SELL
pas de DB
pas de Telegram
Energy ne produit jamais HOT seule
```

C’est conforme PowerFlow.

## Sur le vocabulaire energy support

Exemples inspectés :

```python
ENERGY_SUPPORTS_REJECTION
ENERGY_SUPPORTS_COUNTER_RELEASE
ENERGY_SUPPORTS_ABSORPTION_NOT_RELEASE
ENERGY_SUPPORTS_MICRO_TENSION
COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
```

Lecture :

```text
Le mot support est utilisé dans le sens “soutient / confirme / appuie”.
Il ne désigne pas un support graphique.
```

Donc pas de dérive chartiste.

## Verdict pf_behavioral_alert_mapper.py

```text
Statut : SAIN
Risque : faible
Action : ne pas modifier
Note : fichier doctrinalement protecteur
```

---

# 2.3 Core/pf_flow_nodes.py

## Red flags initiaux

Le scanner avait détecté :

```text
architecture_red_flags
institutional_red_flags
```

## Lignes inspectées

Header :

```python
- Pas de BUY/SELL.
- Pas de Telegram direct.
- Sortie cockpit/backtest : score, intérêt, devises, message court.
```

Puis :

```python
conn = sqlite3.connect(db_path)
```

Et :

```python
def init_table(conn: sqlite3.Connection) -> None:
```

Puis :

```python
INSERT INTO flow_nodes_v1 (...)
```

## Lecture

Ici, il y a un vrai point d’attention.

Contrairement à `pf_temporal_node_state.py`, ce module :

```text
ouvre une connexion SQLite standard
crée/init une table
insère dans flow_nodes_v1
```

Donc ce n’est pas un module read-only.

Il ne faut pas forcément le supprimer : il peut appartenir à une époque V6/V7 antérieure où `flow_nodes_v1` servait de mémoire DB.

Mais pour la doctrine actuelle V7.2 :

```text
Core lab / audit / replay doivent lire la DB en read-only.
Le futur Lab Engine V7.2 ne doit pas dépendre d’un module qui écrit en DB.
```

## Institutional red flag

Le scanner a aussi remonté `BUY/SELL`, mais dans les lignes exactes on voit :

```text
Pas de BUY/SELL
```

Donc ce n’est pas une dérive institutionnelle.

Il n’y a pas, dans les lignes inspectées, de preuve de :

```text
institution detected
smart money
bank buying
```

## Risque réel

Le risque réel n’est pas le langage institutionnel.

Le risque réel est :

```text
pf_flow_nodes.py = legacy write module
```

Donc il doit être classé :

```text
LEGACY / WRITE-AWARE / NON READ-ONLY
```

## Verdict pf_flow_nodes.py

```text
Statut : LEGACY À ISOLER
Risque : moyen si utilisé directement par Lab V7.2
Action : ne pas utiliser comme dépendance directe du Lab V7.2
Solution : wrapper read-only ou extraction logique pure si nécessaire
```

---

## 3. Conclusion sur les red flags

| Fichier | Red flag scanner | Lecture réelle | Décision |
|---|---|---|---|
| `pf_temporal_node_state.py` | classical zone + architecture | faux positif : support = relay, DB read-only confirmé | sain, ne pas modifier |
| `pf_behavioral_alert_mapper.py` | institutional | faux positif : anti BUY/SELL explicite | sain, ne pas modifier |
| `pf_flow_nodes.py` | architecture + institutional | vrai risque DB write, mais BUY/SELL est garde-fou | classer legacy / isoler |

---

## 4. Décision sémantique

## 4.1 Gravity

Aucune nouvelle preuve dans ces lignes que B5 Spearman déduise leader/follower à tort.

Mais l’audit doctrinal reste valide :

```text
B5 Spearman = capteur relationnel.
Gravity organique = relation + lead/lag + field structure + confluence.
```

À maintenir dans le futur Lab.

---

## 4.2 Zones

Le mot `support` dans `pf_temporal_node_state.py` ne désigne pas support/résistance.

Il désigne :

```text
relay / confirmation directionnelle M5
```

Donc la sémantique zone n’est pas polluée par l’analyse technique classique dans les lignes inspectées.

Cependant, le futur Lab doit continuer à utiliser :

```text
zone dynamique
zone active
EIE
node
battlefield zone
```

et non :

```text
support/résistance
order block
supply/demand
```

---

## 4.3 Structural Flow Footprint

Aucune preuve d’un langage institutionnel abusif dans les lignes exactes.

On maintient quand même la règle :

```text
Ne jamais coder INSTITUTION_DETECTED.
Coder STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE + INFERENCE_ONLY.
```

---

## 5. Implication pour le futur Lab Engine V7.2

Le Lab V7.2 peut avancer, mais avec contraintes :

```text
1. Ne pas dépendre directement de pf_flow_nodes.py pour écrire/lire flow_nodes_v1.
2. Lire powerflow.db en mode read-only.
3. Utiliser pf_temporal_node_state.py comme source stable si besoin.
4. Utiliser pf_behavioral_alert_mapper.py comme mapper doctrinalement sain.
5. Garder B5 comme relation, pas gravity totale.
6. Intégrer zones comme champ de tension, pas support/résistance.
7. Intégrer structural footprints comme candidates, jamais certitudes institutionnelles.
```

---

## 6. Classification recommandée des modules

```text
SAFE_READ_ONLY_CORE:
- pf_temporal_node_state.py
- pf_behavioral_alert_mapper.py
- pf_spearman_gravity.py à auditer séparément
- pf_zone_dynamics.py à auditer séparément
- pf_confluence_elastic.py à auditer séparément
- pf_confluence_gravity.py à auditer séparément

LEGACY_WRITE_MODULE:
- pf_flow_nodes.py
```

---

## 7. Recommandation technique immédiate

Avant codage Lab, créer une note dans l’architecture :

```text
pf_flow_nodes.py est legacy et peut écrire dans powerflow.db.
Le Lab Engine V7.2 ne doit pas l’appeler directement.
S’il faut exploiter les nodes, créer une couche read-only :
pf_flow_nodes_reader.py
ou
pf_lab_node_snapshot.py
```

---

## 8. Décision finale de cet audit

```text
Audit code réel = pas de dérive grave détectée.
Le principal risque est pf_flow_nodes.py, module legacy write.
La sémantique support dans pf_temporal_node_state.py est un faux positif.
Le langage BUY/SELL dans pf_behavioral_alert_mapper.py est un garde-fou, pas une sortie.
```

Décision :

```text
GO pour préparer le cahier des charges Lab Engine V7.2,
à condition d’isoler pf_flow_nodes.py et de maintenir les règles sémantiques Gravity/Zones/Footprints.
```

---

## 9. Phrase de clôture

```text
Le champ Gravity/Zones n’est pas cassé.
Il est simplement encore à clarifier.

Le futur Lab V7.2 doit lire le champ,
pas réveiller des modules legacy qui écrivent en DB.

Zone = tension.
Gravity = organisation.
Footprint = empreinte candidate.
B5 = relation, pas décision.
```

---

*Rapport généré après inspection des lignes exactes remontées par Select-String.*
