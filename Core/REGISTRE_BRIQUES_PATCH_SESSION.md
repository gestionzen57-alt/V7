# Registre Patch — Session Overlay V2 + Dashboard Dual Display

## Guard Session — pf_session_overlay.py

```text
Fichier : pf_session_overlay.py
Statut  : V2 complet
Rôle    : injecter SESSION_CONTEXT dans alertes comportementales
Méthode : SESSION_OVERLAY_V2
```

Produit :

```json
{
  "session": "ASIAN | LONDON | NY | OVERLAP | DEAD_ZONE",
  "session_secondary": "NY | null",
  "session_phase": "PRE_OPEN | IGNITION | MID_SESSION | CLOSING | MAX_VELOCITY_BATTLEFIELD | DEAD_ZONE",
  "minutes_since_open": 0,
  "session_bias": "EXPANSION_EXPECTED | COMPRESSION_EXPECTED | ROTATION | MAX_VELOCITY_BATTLEFIELD | DEAD_ZONE",
  "utc_time": "HH:MM:SS",
  "method": "SESSION_OVERLAY_V2",
  "timestamp": "ISO8601 UTC"
}
```

Dépendances : Python stdlib uniquement.

Utilisé par :

```text
pf_behavioral_alert_mapper.py -> session_context
pf_volatility_texture.py      -> qualification session friction possible
Dashboard session card        -> output/session_context.json
```

Règle : session_context ne filtre jamais une alerte.

## Dashboard Freshness Module

```text
Fichier : dashboard_freshness_module.js
Rôle    : calculer age_seconds + freshness et afficher MISSING / STALE explicitement
```

Seuils :

```text
FRESH  < 300s
AGING  >=300s et <600s
STALE  >=600s
MISSING source absente/vide/invalide
```

## Dashboard Dual Display Patch

```text
Fichier : dashboard_dual_display_patch.html
Rôle    : imposer dual display côte à côte
```

Blocs :

```text
regime / B1_LEGACY
regime / B1_HMM
density / B4_ROLLING
density / B4_WAVELET
session / SESSION_OVERLAY_V2
```

Interdits :

```text
Pas de fusion Legacy/HMM
Pas de fusion Rolling/Wavelet
Pas de stale sans signal rouge
Pas de missing silencieux
```
