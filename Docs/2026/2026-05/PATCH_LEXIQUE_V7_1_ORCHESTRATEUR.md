# PATCH LEXIQUE — PowerFlow V7.1
## Orchestrateur du cycle complet

**Date :** 2026-05-09  
**Patch :** ajout des termes liés à `run_powerflow_cycle_once.py`  
**Statut :** VALIDÉ — cycle complet `COMPLETE`

---

## 19. ORCHESTRATION DU CYCLE V7.1

### POWERFLOW_CYCLE_ORCHESTRATOR

Runner unique :

```text
run_powerflow_cycle_once.py
```

Orchestre un cycle complet PowerFlow V7.1 en déclenchant les runners dans l'ordre défini.

Il ne calcule pas la logique moteur.  
Il ne lit pas directement `pf_*`.  
Il ne décide rien.  
Il transmet l'impulsion d'exécution aux modules spécialisés et trace leur réponse.

Rôle comportemental :

```text
déclencher
mesurer
tracer
continuer
rapporter
```

---

### CYCLE_STEP

Unité atomique d'exécution de l'orchestrateur.

Structure logique :

```json
{
  "step": 1,
  "module": "run_data_quality_guard_once",
  "status": "OK",
  "duration_ms": 117,
  "error": null
}
```

Chaque step correspond à un runner `run_*`.

Un step peut échouer sans interrompre le cycle.

---

### NON_BLOCKING_CYCLE

Mode d'orchestration où un échec technique n'arrête pas les steps suivants.

Principe :

```text
fail -> log -> report -> continue
```

Usage PowerFlow :

```text
Une perception manquée par un module ne doit pas empêcher les autres couches de produire leur état.
```

Ce n'est pas une tolérance molle.  
C'est une stratégie de continuité perceptive.

---

### CYCLE_REPORT

Fichier JSON final produit par l'orchestrateur :

```text
output/cycle_report.json
```

Il contient :

```json
{
  "cycle_id": "uuid4",
  "started_at_utc": "2026-05-09T21:47:38+00:00",
  "total_duration_ms": 44120,
  "steps": [],
  "cycle_status": "COMPLETE"
}
```

Rôle :

```text
trace d'exécution
audit technique
diagnostic scheduler
mémoire du cycle
```

---

### CYCLE_STATUS

État synthétique du cycle.

Valeurs :

```text
COMPLETE  : tous les steps sont OK
PARTIAL   : certains steps OK, certains FAIL
FAILED    : aucun step OK
```

Ce statut ne juge pas le marché.  
Il qualifie uniquement l'exécution technique du cycle.

---

### STEP_STATUS

État individuel d'un step.

Valeurs :

```text
OK
FAIL
```

Un step `OK` signifie :

```text
Le runner a terminé correctement
OU son output JSON attendu existe et a été accepté par règle technique.
```

Un step `FAIL` signifie :

```text
Le runner n'a pas produit de résultat exploitable dans les conditions attendues.
```

---

### ACCEPTED_RETURNCODE_WITH_OUTPUT

Cas technique où un runner retourne un code non nul mais produit correctement son JSON attendu.

Exemple observé :

```text
run_data_quality_guard_once.py     -> returncode=2 + output JSON existant
run_market_open_validator_once.py  -> returncode=2 + output JSON existant
```

Règle orchestrateur V7.1 :

```text
Pour les steps validés, si returncode=2 et output existe -> status OK.
```

Raison :

```text
L'interface JSON est la sortie exploitable du cycle.
Le code retour sera normalisé plus tard dans le runner lui-même.
```

Risque technique :

```text
Ambiguïté entre erreur CLI réelle et diagnostic métier négatif.
```

---

### DRY_RUN_CYCLE

Mode de simulation du cycle sans exécution des subprocess.

Commande :

```powershell
python .\run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD --dry-run
```

Rôle :

```text
vérifier l'ordre
vérifier les arguments CLI
vérifier les paths
vérifier le nettoyage du symbole
vérifier la fenêtre dashboard
```

Le dry-run doit être utilisé avant modification scheduler.

---

### SYMBOL_SANITIZATION

Nettoyage technique du symbole avant transmission aux runners.

Exemple :

```text
GBPUSD. -> GBPUSD
```

Méthode :

```text
strip
rstrip(".")
upper
```

Rôle :

```text
éviter la propagation d'un symbole invalide causé par une ponctuation accidentelle.
```

---

### WINDOWS_UTF8_SUBPROCESS

Mode d'exécution subprocess qui force l'environnement Python en UTF-8 sous Windows.

Variables :

```text
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

Rôle :

```text
éviter les erreurs charmap lors de l'écriture de caractères unicode dans les outputs JSON ou logs.
```

Erreur corrigée :

```text
'charmap' codec can't encode character '\u2192'
```

---

### NODE_TIMEOUT_SECONDS

Timeout dédié au Node Engine dans l'orchestrateur.

Valeur validée :

```text
90 secondes
```

Raison :

```text
run_temporal_node_state_once.py peut dépasser 30s sur DB réelle.
```

Observation validée :

```text
step 5 OK en environ 32s
```

Règle :

```text
Les autres steps gardent TIMEOUT_SECONDS = 30.
Le Node reçoit un timeout spécifique car il est le coeur comportemental lourd.
```

---

### DASHBOARD_WINDOW

Fenêtre temporelle automatique transmise au dashboard refresh.

Valeur par défaut :

```text
180 minutes
```

Arguments générés :

```text
--start YYYY-MM-DDTHH:MM:SS
--end   YYYY-MM-DDTHH:MM:SS
```

Rôle :

```text
satisfaire l'interface cockpit/dashboard sans demander une fenêtre manuelle à chaque cycle.
```

---

### SESSION_OVERLAY_INPUT

Fichier d'entrée synthétique généré par l'orchestrateur :

```text
output/session_overlay_input.json
```

Format minimal :

```json
{
  "alerts": []
}
```

Rôle :

```text
permettre à run_session_overlay_once.py de fonctionner dans le cycle même si aucune queue exploitable n'est encore fournie en entrée.
```

Limite :

```text
Ce fichier valide la mécanique session overlay.
Il ne remplace pas une vraie queue enrichie d'alertes comportementales.
```

---

### SCHEDULER_READY_CYCLE

État d'un cycle PowerFlow pouvant être lancé par Windows Task Scheduler.

Critères :

```text
commande unique
paths explicites
logs console
timeouts
rapport JSON
cycle non bloquant
durée compatible cadence 5 minutes
```

Commande cible :

```powershell
python C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\run_powerflow_cycle_once.py --db C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\powerflow.db --symbol GBPUSD
```

---

### CYCLE_DURATION_PROFILE

Profil de durée observé sur un cycle complet.

Exemple validé :

```text
total cycle          : ~44s
temporal_node_state  : ~32s
currency_energy      : ~11s
autres steps         : <1s chacun
```

Usage :

```text
surveiller la charge runtime
adapter la fréquence scheduler
détecter une dérive de latence
```

Risque technique :

```text
si temporal_node_state ou currency_energy dérive fortement, le cycle peut chevaucher le prochain lancement scheduler.
```

---

## 20. CHECKPOINT LEXIQUE

Ajout recommandé dans `LEXIQUE_GRAMMAIRE_V7.1.md` :

```text
2026-05-09 — Orchestration V7.1
  POWERFLOW_CYCLE_ORCHESTRATOR
  CYCLE_STEP
  NON_BLOCKING_CYCLE
  CYCLE_REPORT
  CYCLE_STATUS
  STEP_STATUS
  ACCEPTED_RETURNCODE_WITH_OUTPUT
  DRY_RUN_CYCLE
  SYMBOL_SANITIZATION
  WINDOWS_UTF8_SUBPROCESS
  NODE_TIMEOUT_SECONDS
  DASHBOARD_WINDOW
  SESSION_OVERLAY_INPUT
  SCHEDULER_READY_CYCLE
  CYCLE_DURATION_PROFILE
```

---

## 21. PHRASE DE SYNTHÈSE

```text
Le cycle n'interprète pas.
Le cycle orchestre.

Il ne décide pas.
Il déclenche, mesure, trace et continue.

La perception reste modulaire.
La décision reste trader.
```
