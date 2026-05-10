# PATCH — Intégration B7+ Volatility Texture dans PowerFlow

**Date : 2026-05-10**  
**Version : VolatilityTextureV0.1Standalone**  
**Statut : patch d'intégration manuel, post-P1**

## Objectif

Ajouter `volatility_texture_context` dans les alertes comportementales sans filtrer les alertes.

La texture qualifie la nature du mouvement : `STRUCTURAL`, `NEWS_SPIKE`, `SESSION_FRICTION`, `MM_NOISE`.
Elle ne prédit rien et ne décide rien.

## Point d'intégration mapper

Fichier cible : `Core/pf_behavioral_alert_mapper.py`

Ajouter un import optionnel près des imports moteur :

```python
try:
    from pf_volatility_texture import VolatilityTextureEngine
except Exception:
    VolatilityTextureEngine = None
```

Au moment où l'alerte est construite, ajouter :

```python
if VolatilityTextureEngine is not None:
    texture_engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
    texture_ctx = texture_engine.analyze_texture(
        force_series=recent_force_series,
        spread_series=recent_spread_series if 'recent_spread_series' in locals() else None,
        session_context=alert.get('session_context'),
        symbol=alert.get('symbol', 'GBPUSD'),
        timeframe=1,
    )
    alert['volatility_texture_context'] = texture_ctx.get('volatility_texture', {})
    alert.setdefault('technical_risks', []).extend(texture_ctx.get('technical_risks', []))
```

## Point d'intégration cockpit

Fichier cible : `Core/cockpit_agentic_state_v01.py`

Lire le dernier résultat :

```python
output/volatility_texture.json
```

Afficher :

```json
{
  "type": "STRUCTURAL",
  "confidence": 0.84,
  "micro_macro_ratio": 1.23,
  "pattern_consistency": 0.81,
  "spread_behavior": "STABLE"
}
```

## Point d'intégration dashboard

Fichier cible : `dashboard_live.html`

Nouvelle card :

```text
VOLATILITY TEXTURE
Type: STRUCTURAL
Confidence: 0.84
Micro/Macro: 1.23
Consistency: 0.81
Spread: STABLE
```

Couleurs suggérées :

```text
STRUCTURAL        vert/bleu
SESSION_FRICTION  jaune/orange
NEWS_SPIKE        rouge technique
MM_NOISE          gris/violet
```

## Commande runner

Depuis `Core` :

```powershell
python run_volatility_texture_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --recent-bars 100 --pretty
python -m json.tool ..\output\volatility_texture.json | Out-Null
```

## Doctrine

- `NEWS_SPIKE` n'est pas une interdiction.
- `MM_NOISE` n'est pas une suppression d'alerte.
- `STRUCTURAL` n'est pas un ordre.
- La texture enrichit la perception. Le trader décide.
