# RAPPORT — B9 Scheduler Window Dict Fix V1.3

## Objet

Finir la mission B9 Scheduler Live Integration.

## Bugs corrigés

### 1. `window_data must be a dict`

Le runtime B9 refusait la liste de ticks :

```text
TypeError: window_data must be a dict
```

V1.3 envoie maintenant :

```python
window_data = {
    "symbol": "GBPUSD",
    "ticks": [...],
    "tick_window": [...],
    "window_data": [...],
    "source": "tick_archive.db:tick_stream",
    "source_mode": "SCHEDULER_TICK_ARCHIVE",
    "source_stack": "SCHEDULER_TURBO_WRAPPER",
    "telegram_enabled": False,
    "ENABLE_TELEGRAM": False,
    "metadata": {
        "contract": "B9_WINDOW_DICT_V1"
    }
}
```

### 2. `run_powerflow_live_stack_once.py` ne supporte pas `--once`

V1.3 retire `--once` pour les runners `*_once.py`.

Pour `scheduler_powerflow.py`, `--once` est conservé.

### 3. Variable d'environnement relative

`POWERFLOW_CORE_SCHEDULER=run_powerflow_live_stack_once.py` est maintenant cherché dans :

```text
CoreCore\CoreRepo\Core```

## Contrat

- Telegram OFF.
- `pf_engine_b9.py` non modifié.
- Lecture tick archive read-only.
- B9 fail-soft.
- Pas de BUY/SELL.

## Validation

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD --continue-on-error
python check_b9_live_nodes.py
```

Critère final :

```text
nouvelle node B9 créée par ce run
0 erreur runtime B9
```
