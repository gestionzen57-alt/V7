MISSION : Dashboard Live — Behavioral Flow Card V0.1

Objectif :
Afficher dans dashboard_live.html la carte BEHAVIORAL FLOW déjà présente dans dashboard_data.json.

Fichiers fournis :
- dashboard_live.html : fichier à patcher
- dashboard_data.json : source réelle enrichie
- dashboard_sync_agent_v01.py : référence, ne pas modifier

Règle :
Le HTML lit dashboard_data.json.
Le HTML ne recalcule rien.

À afficher :
- behavioral_flow.title
- behavioral_flow.status
- behavioral_flow.top_alert
- behavioral_flow.line
- behavioral_flow.alerts[]

Ou fallback :
chercher dans dashboard_cards la carte title = "BEHAVIORAL FLOW".

Interdits :
- ne pas modifier pf_*
- ne pas modifier cockpit_*
- ne pas modifier dashboard_sync_agent_v01.py
- ne pas toucher powerflow.db
- ne pas brancher Telegram
- ne pas créer BUY/SELL
- ne pas faire de logique métier dans le HTML

Critère de réussite :
Quand dashboard_data.json contient behavioral_flow,
le dashboard affiche une carte :
BEHAVIORAL FLOW
HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
FIRST_DETACHMENT_WITH_CLEAN_RELAY
et la liste des alertes :
- DETACH+RELAY
- COUNTER REL
- HEAT≠ENERGY
- GRAVITY CLUSTER
- SAME ANGLE
