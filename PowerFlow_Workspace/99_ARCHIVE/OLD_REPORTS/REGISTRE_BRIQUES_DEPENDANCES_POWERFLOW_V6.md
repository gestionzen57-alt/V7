# REGISTRE DES BRIQUES ET DÉPENDANCES — POWERFLOW V6

Date : 2026-05-07  
Statut : CARTOGRAPHIE ACTIVE

---

# 1. Chaîne moteur principale

```text
force_snapshots
→ pf_temporal_node_state.py
→ output/temporal_node_state.json
```

Produit :

```text
capture_quality
relay_quality
session_transition
kinematics_state
release_state
energy_release_alignment
energy_context
```

Ne doit pas dépendre de :

```text
cockpit_*
dashboard_*
telegram_*
```

---

# 2. Currency Energy

Fichiers :

```text
pf_currency_energy_probe.py
run_currency_energy_probe_once.py
```

Rôle :

```text
mesurer la vitalité devise contextualisée
```

Dépendances utiles :

```text
pf_personalities.py
pf_zone_dynamics.py
pf_force_kinematics.py
pf_db_freshness_probe.py
```

Interdits :

```text
Energy ≠ direction
Energy ≠ signal
Energy ≠ Node Heat
```

Connexion actuelle :

```text
utilisée par energy_release_alignment dans Node V0.8.2
```

---

# 3. Kinematics

Localisation :

```text
pf_temporal_node_state.py
pf_force_angle_speed_probe.py
pf_force_kinematics.py
```

Rôle :

```text
dire comment ça bouge :
angle, vitesse, accélération, first_detachment, clusters
```

Champs :

```text
kinematics_state
angle_state
speed_state
acceleration_state
first_detachment
same_angle_cluster
tight_gravity_cluster
```

---

# 4. Relational Gravity

Fichiers :

```text
pf_relational_gravity_probe.py
run_relational_gravity_probe_once.py
pf_relational_gravity_bridge.py
```

Rôle :

```text
mesurer comment les devises se tiennent entre elles :
groupe, distance, leader, followers, antagoniste, cohérence multi-TF.
```

État :

```text
V0.1 standalone validé
V0.1.1 delta filter validé
P1.1 cockpit bridge validé
P1.2 bridge guard à faire
```

Dépendance vers cockpit :

```text
cockpit_agentic_state_v01.py lit pf_relational_gravity_bridge.py
```

Ne doit pas faire :

```text
pas de DB read dans cockpit
pas de Telegram
pas de dashboard direct
pas de Node integration immédiate
```

---

# 5. Behavioral Flow

Fichiers :

```text
pf_behavioral_alert_mapper.py
run_behavioral_alert_mapper_once.py
cockpit_agentic_state_v01.py
dashboard_sync_agent_v01.py
dashboard_server.py
dashboard_live.html
```

Chaîne validée :

```text
temporal_node_state.json
→ behavioral_alert_queue.json
→ cockpit_agentic_state_v01.json
→ dashboard_data.json
→ dashboard_live.html
```

Relational Gravity P2 :

```text
En attente P1.2 Bridge Guard
```

---

# 6. Dashboard

Rôle :

```text
afficher
ne pas décider
ne pas calculer la logique moteur
```

Règle writer :

```text
un seul dashboard_server actif
dashboard_sync_agent doit rester le dernier enrichisseur logique
```

---

# 7. Telegram

Statut :

```text
à ne pas brancher maintenant
```

Condition future :

```text
probe stable
cockpit stable
behavioral queue stable
dashboard stable
```
