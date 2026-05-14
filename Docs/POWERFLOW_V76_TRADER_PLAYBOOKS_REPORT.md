# POWERFLOW V7.6 — TRADER PLAYBOOKS GBPUSD REPORT

## 0. Mission

Ajouter une couche playbook d'attention trader pour GBPUSD, sans execution automatique et sans signal de trading.

La couche lit un `terrain_packet.json` deja produit par V7.6 et ajoute :

```text
playbook_state
playbook_label_fr
playbook_context_fr
watch_plan_fr
invalidation_fr
no_trade_warning_fr
```

## 1. Scope

```text
Instrument : GBPUSD only
Mode       : read JSON -> write JSON
Execution  : aucune
Telegram   : aucune activation automatique
Dashboard  : aucune refonte
```

## 2. Fichiers ajoutes

```text
patch/pf_trader_playbook_once.py
schema/playbook_labels_fr_v76.json
tests/test_trader_playbook_v76.py
Docs/POWERFLOW_V76_TRADER_PLAYBOOKS_REPORT.md
```

## 3. Principe d'architecture

Le module est volontairement add-only :

```text
terrain_packet.json
   -> pf_trader_playbook_once.py
      -> trader_playbook.json
      -> terrain_packet_with_playbook.json optionnel
```

Il ne modifie pas le moteur `pf_*`, ne depend pas de `telegram_*`, ne touche pas a la DB, ne produit pas d'ordre.

## 4. Playbooks prioritaires

| playbook_state | Role terrain |
|---|---|
| HIGH_ZONE_EXHAUSTION_RISK | Zone haute mature, extension tardive, consommation ou rejet possible |
| POST_HIGH_UNWIND | Deroulement apres rejet de zone haute |
| SECOND_LEG_DOWN | Reprise descendante apres counter-breath rejete ou lower lock |
| POST_RELEASE_COUNTER_BREATH | Respiration inverse apres une release structurelle |
| POST_LOW_COUNTER_BREATH | Reaction/counter-breath depuis zone basse |
| HONEST_UNKNOWN | Lecture limitee ou inconnue honnete |

## 5. Champs lus

Le module lit les champs terrain suivants, en format plat ou imbrique :

```text
symbol
film_state
last_structural_event
current_move_role
raw_bias
qualified_bias
packet_quality
price_confirmation
propagation_state
detachment_texture
data_visibility
watch_condition
invalidation_condition
current_zone
current_zone_status
```

## 6. Non-surinterpretation

Le playbook ne transforme jamais `PAIR_UP` ou `PAIR_DOWN` en decision. Le `raw_bias` est seulement une piece de contexte.

Si les donnees sont insuffisantes, le module produit `HONEST_UNKNOWN` ou ajoute `no_trade_warning_fr`.

Exemples de data limitee :

```text
READING_PARTIAL
MICROFILM_MISSING
PACKETS_STALE
CROSS_VALIDATION_DEGRADED
B5_B8_DEGRADED
HONEST_UNKNOWN
UNKNOWN
```

## 7. Exemple attendu

Input :

```json
{
  "symbol": "GBPUSD",
  "qualified_bias": "HIGH_ZONE_EXHAUSTION_RISK",
  "price_confirmation": "PRICE_REJECTED_LOW",
  "data_visibility": "READING_PARTIAL"
}
```

Output extrait :

```json
{
  "playbook_state": "HIGH_ZONE_EXHAUSTION_RISK",
  "playbook_label_fr": "Risque d’épuisement en zone haute",
  "watch_plan_fr": "Ne pas chase. Surveiller acceptation propre au-dessus de la zone haute ou rejet confirmé avec perte de tenue du prix.",
  "invalidation_fr": "Acceptation propre au-dessus de la zone haute avec propagation non dégradée et prix qui tient la zone.",
  "no_trade_warning_fr": "Lecture partielle : prudence analytique, ne pas traiter comme lecture complete."
}
```

## 8. Test PowerShell

```powershell
Set-Location "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"

python -m pytest .\tests\test_trader_playbook_v76.py -q

python .\patch\pf_trader_playbook_once.py `
  --symbol GBPUSD `
  --input .\output\dashboard_surface\GBPUSD\terrain_packet.json `
  --labels .\schema\playbook_labels_fr_v76.json `
  --output .\output\dashboard_surface\GBPUSD\trader_playbook.json `
  --packet-output .\output\dashboard_surface\GBPUSD\terrain_packet_with_playbook.json
```

## 9. PASS / FAIL attendu

```text
pytest: 7 passed
runtime: trader_playbook.json cree
GBPUSD only: PASS
Pas de BUY/SELL/ENTRY/EXIT/TARGET/STOP: PASS
Telegram non active: PASS
```

## 10. Integration optionnelle formatter FR

Integration dormante recommandee : le formatter FR peut lire `output/dashboard_surface/GBPUSD/trader_playbook.json` et afficher :

```text
Scenario : {playbook_label_fr}
Contexte : {playbook_context_fr}
Watch : {watch_plan_fr}
Invalidation : {invalidation_fr}
Data : {no_trade_warning_fr}
```

Ne pas declencher Telegram automatiquement depuis ce module.

