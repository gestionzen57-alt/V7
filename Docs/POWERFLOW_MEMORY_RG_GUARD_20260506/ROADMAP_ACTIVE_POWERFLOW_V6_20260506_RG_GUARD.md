# ROADMAP ACTIVE — POWERFLOW V6
## Mise à jour 2026-05-06 — Relational Gravity Guard

## Validé

```text
Node V0.8.2 — Energy Release Alignment
Behavioral Flow Dashboard
Relational Gravity Bridge Guard P1.2
Topline State P1.2.2
Behavioral Mapper Guard-Aware P2
Full Refresh Runner RG-aware P2.1
Refresh Cockpit From Queue P2.1.1
```

## Priorité immédiate

### P1 — Patch lexique Relational Gravity Guard

À faire sur autre fil :

```text
PATCH_LEXIQUE_RELATIONAL_GRAVITY_GUARD_P12_P2_20260506.md
```

Termes à intégrer :

```text
RELATIONAL_GRAVITY_BRIDGE_GUARD
RELATIONAL_GRAVITY_TOPLINE_STATE
RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT
RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT
RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE
RELATIONAL_GRAVITY_TOPLINE_PARTIAL
RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO
LEADER_CONFLICT_INFO
topline_reliable
direction_consistency
leader_consistency
antagonist_consistency
```

## Prochaine micro-brique possible

### P2.2 — Behavioral Flow RG Film Step

Objectif :

```text
Ajouter un film_step [RELATIONAL_GRAVITY]
dans behavioral_alert_queue / cockpit / dashboard.
```

Exemple :

```text
[RELATIONAL_GRAVITY] direction=UP | leader=MIXED | state=DIRECTION_ALIGNED_LEADER_CONFLICT | reliable=false
```

## Amélioration runner

### P2.3 — recent-minutes auto

Objectif : éviter start/end manuels dans `run_powerflow_dashboard_refresh_once.py`.

## Règle live

```powershell
python .\run_powerflow_dashboard_refresh_once.py `
  --skip-cockpit `
  --refresh-cockpit-from-queue `
  --pretty `
  --summary
```

Ne pas utiliser `--skip-cockpit` seul si la queue vient d’être régénérée.
