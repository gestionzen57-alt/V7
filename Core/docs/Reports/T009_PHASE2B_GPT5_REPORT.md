# T009_PHASE2B_GPT5_REPORT

## Résumé

- [x] `pf_telegram_battlefield.py` ✅
- [x] `run_telegram_battlefield_cycle.py` ✅
- [x] Tests Telegram LIVE routing ✅
- [x] Messages FR trader ✅
- [x] Safety gates Telegram ✅

## Livrables

- `Core/pf_telegram_battlefield.py`
  - Format Telegram FR trader
  - Confidence filtering `>= 0.50`
  - RECONSTRUCTED data blocking
  - Rate limiting 1 message / 10 secondes / symbole
  - Retry logic 3 tentatives maximum
  - Telegram Bot HTTP API via `TELEGRAM_BOT_TOKEN`

- `Core/run_telegram_battlefield_cycle.py`
  - CLI Phase 2B
  - Arguments : `--symbol`, `--lookback-min`, `--enable-telegram`, `--events-file`, `--output`
  - Safety checks LIVE : `POWERFLOW_T009_ENABLE_TELEGRAM=1` et `POWERFLOW_T009_DRY_RUN=0`
  - Mode sans `--enable-telegram` = dry-run console

- `Core/tests/test_t009_phase2b_telegram_live.py`
  - 12 tests unitaires / CLI
  - Aucun vrai send Telegram pendant les tests

## Tests

Commande :

```powershell
python -m pytest Core/tests/test_t009_phase2b_telegram_live.py -q
```

Résultat attendu :

```text
12 passed
```

Tests couverts :

- `test_telegram_message_template_battle` ✅
- `test_telegram_message_template_absorption` ✅
- `test_send_battlefield_alert_live_mode` ✅
- `test_send_battlefield_alert_dry_run` ✅
- `test_reconstructed_data_blocked` ✅
- `test_confidence_filter_min_050` ✅
- `test_rate_limiting_10s` ✅
- `test_retry_logic_3_attempts` ✅
- `test_retry_logic_success_after_two_failures` ✅
- `test_telegram_flag_enforcement` ✅
- `test_cli_safety_checks` ✅
- `test_cli_dry_run_no_events_safe` ✅

## Architecture decisions

### 1. Module isolé

`pf_telegram_battlefield.py` ne dépend pas du dashboard ni de l'engine. Il reçoit un packet déjà formé et applique uniquement les règles de routing Telegram.

### 2. LIVE explicit only

Le CLI n'envoie jamais LIVE sans `--enable-telegram`. Même avec l'argument, il refuse si :

```text
POWERFLOW_T009_ENABLE_TELEGRAM != 1
POWERFLOW_T009_DRY_RUN != 0
```

### 3. RECONSTRUCTED bloqué

Tout packet `data_visibility == RECONSTRUCTED` ou `live_telegram_allowed == False` est bloqué, même si le score est élevé.

### 4. Confidence filter

Le seuil LIVE minimal est fixé à `0.50`. Les packets sous ce seuil sont rejetés avec une raison explicite.

### 5. Rate limiting

Le module garde `_last_send[symbol]` et bloque les envois répétés avant 10 secondes par symbole.

### 6. Retry logic

La fonction `_send_telegram_api()` est appelée au maximum 3 fois. Les tests monkeypatchent cette fonction pour éviter tout envoi réel.

## Safety validation

- Aucun Telegram LIVE pendant les tests ✅
- Aucun write `powerflow.db` ✅
- Aucun import dashboard obligatoire ✅
- Aucun import engine obligatoire ✅
- `RECONSTRUCTED` bloqué ✅
- `DRY_RUN=1` bloque LIVE ✅
- `ENABLE_TELEGRAM=0` bloque LIVE ✅

## Commandes de validation

Dry-run CLI :

```powershell
python Core/run_telegram_battlefield_cycle.py --symbol GBPUSD --lookback-min 30
```

LIVE CLI, seulement avec env explicites :

```powershell
$env:POWERFLOW_T009_ENABLE_TELEGRAM="1"
$env:POWERFLOW_T009_DRY_RUN="0"
$env:TELEGRAM_BOT_TOKEN="your_bot_token"
$env:TELEGRAM_CHAT_ID="your_chat_id"
python Core/run_telegram_battlefield_cycle.py --symbol GBPUSD --lookback-min 30 --enable-telegram
```

## Blockers

Aucun blocker code identifié.

Point de prudence technique : la validation LIVE réelle nécessite `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` valides. Les tests restent mockés et ne prouvent pas la délivrabilité Telegram côté réseau/API.

## Next steps

Phase suivante possible :

- Phase 2C : orchestration scheduler contrôlée
- Phase 2D : dashboard status Telegram LIVE / last send / blocked reasons
- Phase 3 : activation production sous contrôle architecte

## Git

Branche cible :

```text
feat/t009-phase2b-telegram-live
```

Commit attendu :

```text
[feat(t009): add Phase 2B Telegram LIVE routing]
```
