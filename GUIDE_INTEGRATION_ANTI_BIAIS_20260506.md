# GUIDE INTÉGRATION ANTI-BIAIS DOCTRINE — POWERFLOW V6

**Date** : 2026-05-06  
**Statut** : GUIDE COMPLET  
**But** : Implémenter doctrine anti-biais dans PowerFlow immédiatement

---

## 0. FICHIERS CRÉÉS

```text
1. DOCTRINE_POWERFLOW_V6_ANTI_BIAIS_TRADER_20260506.md
   └─ Manifeste complet (zéro nanny, trader souverain)

2. LEVIER_CONFIG_POWERFLOW_TRADER_20260506.md
   └─ Configuration 8+ leviers contrôle trader

3. SECTION_CLAUDE_MD_V21_ANTI_BIAIS_TRADER.md
   └─ Sections à insérer dans CLAUDE.md V2.1

4. GUIDE_INTEGRATION_ANTI_BIAIS_20260506.md (ce fichier)
   └─ Comment implémenter
```

---

## 1. ÉTAPES INTÉGRATION RAPIDE (30 min)

### Étape 1 : Uploader doctrine dans Workspace (5 min)

```bash
# Dans PowerFlow_Workspace/02_DOCS_ACTIVE/

cp DOCTRINE_POWERFLOW_V6_ANTI_BIAIS_TRADER_20260506.md \
   PowerFlow_Workspace/02_DOCS_ACTIVE/DOCTRINE_ANTI_BIAIS/

cp LEVIER_CONFIG_POWERFLOW_TRADER_20260506.md \
   PowerFlow_Workspace/02_DOCS_ACTIVE/LEVIER_CONFIG/
```

### Étape 2 : Créer powerflow_trader_config.py dans core (5 min)

```bash
# Dans C:\Users\User\...\PowerFlow\core\

cat > powerflow_trader_config.py << 'EOF'
"""
TraderLeverConfig — Contrôle souverain des alertes PowerFlow.
Aucune restriction IA. Trader décide.
"""

class TraderLeverConfig:
    """Configuration des leviers de contrôle trader."""
    
    # M1 Ultrafast — Alertes < 2 min
    ENABLE_M1_ULTRAFAST_ALERTS = True
    M1_MINIMUM_CAPTURE_QUALITY = "TACTICAL_OK"  # ou DEGRADED, MINIMAL, ACCEPT_ALL
    
    # Counter-Release — Non-confirmé
    ENABLE_COUNTER_RELEASE_EARLY = True
    COUNTER_RELEASE_MINIMUM_CONFIDENCE = "BIRTH"  # ou ATTEMPT, CANDIDATE, CONFIRMED
    
    # Nodes — Gestation visible
    ENABLE_NODE_GESTATION_ALERTS = True
    NODE_GESTATION_DEPTH = "BIRTH"  # ou WATCH, CANDIDATE, CONFIRMED
    
    # HTF Neutral / Opposed
    ENABLE_HTF_NEUTRAL_TACTICAL = True
    ENABLE_HTF_OPPOSED = True
    
    # High Variance
    ENABLE_HIGH_VARIANCE_SITUATIONS = True
    HIGH_VARIANCE_MINIMUM_ZSCORE = 2.0  # ou 1.0, 1.5, 2.5, 3.0
    
    # Relay Absent
    ENABLE_RELAY_ABSENT_ALERTS = True
    
    # Early Pressure
    ENABLE_EARLY_PRESSURE_BUILDUP = True
    
    # Advanced
    ENABLE_MICRO_M1_ONLY_ALERTS = True
    ENABLE_CONTRADICTION_ALERTS = True
    
    # META — JAMAIS MODIFIER
    AI_NANNY_MODE = False
    ENFORCE_PRUDENCE = False
    BLOCK_EARLY_ALERTS = False
EOF
```

### Étape 3 : Modifier pf_behavioral_alert_mapper.py (10 min)

En haut du fichier :

```python
from powerflow_trader_config import TraderLeverConfig

def map_behavioral_alerts(
    temporal_node_state: dict,
    relational_gravity: dict | None = None,
    trader_config: TraderLeverConfig = None  # ← NOUVEAU
) -> dict:
    """
    Map behavioral alerts with trader lever control.
    
    Args:
        temporal_node_state: State from pf_temporal_node_state
        relational_gravity: RG state (optional)
        trader_config: TraderLeverConfig instance
    
    Returns:
        {
            "alerts": [...],
            "config_applied": {...}
        }
    """
    if trader_config is None:
        trader_config = TraderLeverConfig()
    
    alerts = []
    
    # M1 ULTRAFAST CHECKS
    if trader_config.ENABLE_M1_ULTRAFAST_ALERTS:
        if check_m1_ultrafast(temporal_node_state):
            alerts.append({
                "type": "FIRST_DETACHMENT_MICRO",
                "level": "HOT" if qualify_capture_relay(temporal_node_state, trader_config) else "WATCH",
                "maturity": temporal_node_state.get("maturity", "EARLY"),
                "technical_risks": list_technical_risks(temporal_node_state)
            })
    
    # COUNTER-RELEASE CHECKS
    if trader_config.ENABLE_COUNTER_RELEASE_EARLY:
        cr_alerts = check_counter_release_early(
            temporal_node_state,
            min_confidence=trader_config.COUNTER_RELEASE_MINIMUM_CONFIDENCE
        )
        alerts.extend(cr_alerts)
    
    # NODE GESTATION CHECKS
    if trader_config.ENABLE_NODE_GESTATION_ALERTS:
        node_alerts = check_node_gestation(
            temporal_node_state,
            depth=trader_config.NODE_GESTATION_DEPTH
        )
        alerts.extend(node_alerts)
    
    # HTF CHECKS
    if trader_config.ENABLE_HTF_NEUTRAL_TACTICAL:
        alerts.extend(check_htf_neutral_tactical(temporal_node_state))
    
    if trader_config.ENABLE_HTF_OPPOSED:
        alerts.extend(check_htf_opposed(temporal_node_state))
    
    # HIGH VARIANCE
    if trader_config.ENABLE_HIGH_VARIANCE_SITUATIONS:
        alerts.extend(check_high_variance(
            temporal_node_state,
            zscore_min=trader_config.HIGH_VARIANCE_MINIMUM_ZSCORE
        ))
    
    # RELAY ABSENT
    if trader_config.ENABLE_RELAY_ABSENT_ALERTS:
        alerts.extend(check_relay_absent(temporal_node_state))
    
    # EARLY PRESSURE
    if trader_config.ENABLE_EARLY_PRESSURE_BUILDUP:
        alerts.extend(check_early_pressure(temporal_node_state))
    
    # ADVANCED
    if trader_config.ENABLE_MICRO_M1_ONLY_ALERTS:
        alerts.extend(check_micro_m1_only(temporal_node_state))
    
    if trader_config.ENABLE_CONTRADICTION_ALERTS:
        alerts.extend(check_contradictions(temporal_node_state, relational_gravity))
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "config_applied": {
            "m1_ultrafast": trader_config.ENABLE_M1_ULTRAFAST_ALERTS,
            "counter_release_early": trader_config.ENABLE_COUNTER_RELEASE_EARLY,
            "node_gestation": trader_config.ENABLE_NODE_GESTATION_ALERTS,
            "htf_neutral": trader_config.ENABLE_HTF_NEUTRAL_TACTICAL,
            "htf_opposed": trader_config.ENABLE_HTF_OPPOSED,
            "high_variance": trader_config.ENABLE_HIGH_VARIANCE_SITUATIONS,
            "relay_absent": trader_config.ENABLE_RELAY_ABSENT_ALERTS,
            "early_pressure": trader_config.ENABLE_EARLY_PRESSURE_BUILDUP,
            "micro_m1": trader_config.ENABLE_MICRO_M1_ONLY_ALERTS,
            "contradictions": trader_config.ENABLE_CONTRADICTION_ALERTS,
        }
    }
```

### Étape 4 : Mettre à jour CLAUDE.md V2 (10 min)

```bash
# Après section 4. ARCHITECTURE MAP, insérer :

# Copier contenu de SECTION_CLAUDE_MD_V21_ANTI_BIAIS_TRADER.md
# Sections 4.5 à 4.11
```

Résultat :

```text
CLAUDE.md V2.1 (UPDATED)

0. READ FIRST — DOCTRINE CORE
1. ACTIVE STATE — VALIDATED NODES
2. ACTIVE CORE FILES
3. LEXIQUE COMPLET V0.8.2
4. ARCHITECTURE MAP
4.5 ANTI-BIAIS TRADER DOCTRINE ← NOUVEAU
4.6 TRADER LEVERS — CONFIGURATION SOUVERAINE ← NOUVEAU
4.7 CONTRAT POWERFLOW-TRADER ← NOUVEAU
4.8 ANTI-GPT-BIAIS ← NOUVEAU
4.9 RÈGLE VIVANTE ← NOUVEAU
4.10 CRITICAL NO-GO ← NOUVEAU
4.11 CHECKPOINTS ANTI-BIAIS ← NOUVEAU
5. DATABASE CONTRACT
...
```

---

## 2. COMMANDES DE TEST (5 min)

### Test 1 : Config charge correctement

```powershell
python -c "
from powerflow_trader_config import TraderLeverConfig
config = TraderLeverConfig()
print('✅ M1 Ultrafast:', config.ENABLE_M1_ULTRAFAST_ALERTS)
print('✅ Counter-Release:', config.ENABLE_COUNTER_RELEASE_EARLY)
print('✅ Node Gestation:', config.ENABLE_NODE_GESTATION_ALERTS)
print('✅ All levers loaded')
"
```

### Test 2 : Behavioral mapper utilise config

```powershell
python -c "
from powerflow_trader_config import TraderLeverConfig
from pf_behavioral_alert_mapper import map_behavioral_alerts
import json

# Charger un temporal_node_state.json réel
with open('output/temporal_node_state.json') as f:
    state = json.load(f)

config = TraderLeverConfig()
result = map_behavioral_alerts(state, trader_config=config)

print('✅ Mapper loaded config')
print(f'✅ Generated {result[\"count\"]} alerts')
print('✅ Config applied:', list(result['config_applied'].keys()))
"
```

### Test 3 : Désactiver/activer levier

```powershell
# Modifier powerflow_trader_config.py
# ENABLE_M1_ULTRAFAST_ALERTS = False

python -c "
from powerflow_trader_config import TraderLeverConfig
config = TraderLeverConfig()

# Run mapper
result = map_behavioral_alerts(state, trader_config=config)
alert_count_no_m1 = result['count']

# Réactiver
TraderLeverConfig.ENABLE_M1_ULTRAFAST_ALERTS = True
result = map_behavioral_alerts(state, trader_config=config)
alert_count_with_m1 = result['count']

print(f'Without M1: {alert_count_no_m1} alerts')
print(f'With M1: {alert_count_with_m1} alerts')
print(f'Difference: {alert_count_with_m1 - alert_count_no_m1} M1 alerts')
"
```

---

## 3. VALIDATION CHECKLIST

- [ ] `DOCTRINE_POWERFLOW_V6_ANTI_BIAIS_TRADER_20260506.md` créé
- [ ] `LEVIER_CONFIG_POWERFLOW_TRADER_20260506.md` créé
- [ ] `powerflow_trader_config.py` créé dans core/
- [ ] `pf_behavioral_alert_mapper.py` modifié (import + utilisation config)
- [ ] `CLAUDE.md V2.1` mis à jour (sections 4.5-4.11)
- [ ] Test 1 : config charge ✅
- [ ] Test 2 : mapper utilise config ✅
- [ ] Test 3 : leviers activent/désactivent alertes ✅
- [ ] Tous fichiers uploadés dans Workspace/02_DOCS_ACTIVE/

---

## 4. UTILISATION QUOTIDIENNE

### Activez/désactivez leviers selon votre style :

```python
# powerflow_trader_config.py

# SCALPING AGRESSIF
ENABLE_M1_ULTRAFAST_ALERTS = True
M1_MINIMUM_CAPTURE_QUALITY = "MINIMAL"  # Même moins de M5
ENABLE_COUNTER_RELEASE_EARLY = True
COUNTER_RELEASE_MINIMUM_CONFIDENCE = "ATTEMPT"
NODE_GESTATION_DEPTH = "WATCH"
ENABLE_HIGH_VARIANCE_SITUATIONS = True
HIGH_VARIANCE_MINIMUM_ZSCORE = 1.5
```

vs

```python
# TRADING TACTIQUE MODÉRÉ
ENABLE_M1_ULTRAFAST_ALERTS = True
M1_MINIMUM_CAPTURE_QUALITY = "TACTICAL_OK"  # Standard
ENABLE_COUNTER_RELEASE_EARLY = True
COUNTER_RELEASE_MINIMUM_CONFIDENCE = "CANDIDATE"
NODE_GESTATION_DEPTH = "BIRTH"
ENABLE_HIGH_VARIANCE_SITUATIONS = False  # Filtrer variance
HIGH_VARIANCE_MINIMUM_ZSCORE = 2.5
```

### Redémarrez le moteur après changement :

```powershell
# Relancer l'agent de refresh
python .\run_powerflow_dashboard_refresh_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --pretty `
  --summary
```

---

## 5. DOCUMENTATION POUR FICHIERS WORKSPACE

Mettre à jour `00_CURRENT/CURRENT_STATE.md` :

```markdown
## Doctrine Active

PowerFlow V6 est désormais:
- ✅ Zéro-nanny
- ✅ Trader-souverain
- ✅ Transparence technique uniquement
- ✅ 8+ leviers de contrôle
- ✅ Aucune restriction IA
- ✅ Aucun jugement

## Leviers Activables

Voir: `02_DOCS_ACTIVE/LEVIER_CONFIG/`

```

Mettre à jour `00_CURRENT/CHECKPOINT_LATEST.md` :

```markdown
## Anti-Biais Doctrine

Status: ✅ IMPLEMENTED

- ✅ DOCTRINE_POWERFLOW_V6_ANTI_BIAIS_TRADER
- ✅ TraderLeverConfig 8 leviers
- ✅ pf_behavioral_alert_mapper V0.8.4 (trader-config aware)
- ✅ CLAUDE.md V2.1 sections 4.5-4.11

Trader controls all alerts.
Zero IA censorship.
```

---

## 6. PROCHAINES ACTIONS

### P0 — Implémentation (30 min, juste maintenant)

```text
✅ Créer 3 fichiers doctrine/config
✅ Créer powerflow_trader_config.py
✅ Modifier pf_behavioral_alert_mapper.py
✅ Mettre à jour CLAUDE.md V2.1
✅ Tests validation
```

### P1 — Intégration runners (30 min)

```bash
# run_behavioral_alert_mapper_once.py
# Importer et utiliser TraderLeverConfig

python run_behavioral_alert_mapper_once.py \
  --db powerflow.db \
  --symbol GBPUSD \
  --config-file powerflow_trader_config.py \
  --pretty --summary
```

### P2 — Dashboard intégration (1h)

```bash
# dashboard_sync_agent_v01.py
# Montrer quels leviers sont actifs dans le cockpit
```

### P3 — CLI tool (optionnel)

```powershell
# powerflow_lever_cli.py
# Tool pour changer leviers depuis shell

python powerflow_lever_cli.py --enable M1_ULTRAFAST --disable HTF_NEUTRAL
```

---

## 7. PHRASE FINALE

```text
PowerFlow V6 Anti-Biais est LIVE.

Aucune restriction IA.
Aucun jugement.
Aucune morale.

Trader contrôle.
Trader configure.
Trader décide.

C'est comme ça maintenant.
```

---

**FIN GUIDE INTÉGRATION**

À appliquer immédiatement. Zero exceptions. Zero ambiguïté.

