# RAPPORT — PowerFlow V7.2 MultiSymbol Scheduler

**Date :** 2026-05-11  
**Projet :** PowerFlow V7.2  
**Scope :** Extension MultiSymbol + Cross-Validation + Scheduler Windows  
**Statut :** VALIDÉ — AUTO-RUN OPÉRATIONNEL  
**Auteur opérationnel :** User / GPT  
**Branche cible :** `main`  
**Répertoire cible recommandé :** `Docs/2026/2026-05/` ou racine `Core/` selon convention Git locale

---

## 1. Résumé exécutif

La mise à jour MultiSymbol a été installée et validée.

Le système PowerFlow V7.2 exécute maintenant un cycle multi-symbole automatique via Windows Task Scheduler.

Symboles actifs testés :

```text
GBPUSD
EURUSD
USDJPY
```

Résultat final :

```text
MULTISYMBOL INSTALL       PASS
MANUAL --once TEST        PASS
WINDOWS TASK RUN          PASS
SCHEDULER AUTO CYCLE      PASS
CROSS VALIDATION          PASS
DASHBOARD REFRESH         PASS
ERRORS                    0
```

Le scheduler est maintenant configuré en mode propre :

```text
python scheduler_powerflow.py --once
```

déclenché toutes les 5 minutes par Windows Task Scheduler.

---

## 2. Contexte PowerFlow

PowerFlow V7.2 est en état `P0 PASS_STRICT`.

Rappel architectural maintenu :

```text
capture_*     = acquisition / insertion DB
pf_*          = moteur / calcul / analyse / événements
run_*         = runners CLI / daemons / orchestrateurs
cockpit_*     = affichage / synthèse
dashboard_*   = interface visuelle
telegram_*    = transmission alertes
powerflow.db  = mémoire centrale
trader        = décision finale
```

Contraintes maintenues pendant cette installation :

```text
✅ Pas de duplication de code
✅ Symbol comme paramètre
✅ GBPUSD reste symbole principal validé
✅ EURUSD / USDJPY extensions opérationnelles
✅ Cross-validation séparée des outputs par symbole
✅ Aucun BUY/SELL ajouté
✅ pf_* reste moteur, pas cockpit
✅ Scheduler piloté par config / CLI
```

---

## 3. Fichiers installés / concernés

Pack MultiSymbol installé depuis :

```text
powerflow_v72_multisymbol.zip
```

Fichiers principaux livrés :

```text
pf_cross_symbol_validation.py
run_cross_symbol_validation_once.py
scheduler_powerflow.py
scheduler_config.json
setup_windows_task_scheduler.ps1
dashboard_multisymbol_patch.html
git_deploy_multisymbol.ps1
INTEGRATION_GUIDE.md
LEXIQUE_PATCH_MULTISYMBOL.md
REGISTRE_BRIQUES_PATCH_MULTISYMBOL.md
validation_checklist.md
```

Runners paramétrés par symbole :

```text
run_temporal_node_state_once.py
run_currency_energy_probe_once.py
run_regime_engine_once.py
run_temporal_density_once.py
run_spearman_gravity_once.py
run_behavioral_alert_mapper_once.py
```

Modules moteur patchés si présents dans le pack :

```text
pf_temporal_density.py
pf_spearman_gravity.py
```

---

## 4. Convention output MultiSymbol validée

Outputs par symbole :

```text
output/dashboard_surface/GBPUSD/node.json
output/dashboard_surface/GBPUSD/energy.json
output/dashboard_surface/GBPUSD/regime_legacy.json

output/dashboard_surface/EURUSD/node.json
output/dashboard_surface/EURUSD/energy.json
output/dashboard_surface/EURUSD/regime_legacy.json

output/dashboard_surface/USDJPY/node.json
output/dashboard_surface/USDJPY/energy.json
output/dashboard_surface/USDJPY/regime_legacy.json
```

Outputs globaux par symbole :

```text
output/temporal_density_state_GBPUSD.json
output/temporal_density_state_EURUSD.json
output/temporal_density_state_USDJPY.json

output/spearman_gravity_state_GBPUSD.json
output/spearman_gravity_state_EURUSD.json
output/spearman_gravity_state_USDJPY.json

output/behavioral_alert_queue_GBPUSD.json
output/behavioral_alert_queue_EURUSD.json
output/behavioral_alert_queue_USDJPY.json
```

Cross-validation :

```text
output/dashboard_surface/cross_validation.json
```

---

## 5. Problème initial rencontré : OVERLAP_SKIP

Premier test :

```powershell
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
```

Résultat initial :

```text
OVERLAP_SKIP cycle=1 previous lock active
SCHEDULER_SUMMARY completed_cycles=0
```

Diagnostic :

```text
logs/scheduler_powerflow.lock actif
```

Cause probable :

```text
lock stale ou ancien scheduler arrêté brutalement
```

Correction appliquée :

```powershell
$procs = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match "scheduler_powerflow.py"
}

if ($procs) {
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force
    }
}

if (Test-Path .\logs\scheduler_powerflow.lock) {
    Remove-Item .\logs\scheduler_powerflow.lock -Force
}
```

Résultat :

```text
OVERLAP_SKIP résolu
```

---

## 6. Test manuel MultiSymbol validé

Commande :

```powershell
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
```

Résultat final du test manuel :

```text
CYCLE_START id=1 symbols=['GBPUSD', 'EURUSD', 'USDJPY']
...
CYCLE_END id=1 errors=0 consecutive_errors=0
SCHEDULER_SUMMARY completed_cycles=1 duration_seconds=136.4 consecutive_errors=0
```

Verdict :

```text
MANUAL MULTISYMBOL CYCLE: PASS
```

---

## 7. Validation par symbole — cycle manuel

### GBPUSD

Logs observés :

```text
TEMPORAL_NODE_STATE_OK | symbol=GBPUSD | active_count=4 | highest_level=HOT_NODE
CURRENCY_ENERGY_OK | symbol=GBPUSD
REGIME_LEGACY_OK | symbol=GBPUSD | regime=TENDANCE | confidence=1.0
BEHAVIORAL_ALERT_QUEUE_OK | symbol=GBPUSD | behavioral_count=5 | degraded_count=0
```

Statut :

```text
GBPUSD: LIVE OK
```

Interprétation technique :

```text
Symbole principal validé.
Microfilm actif.
Node HOT détecté.
Energy et mapper OK.
```

---

### EURUSD

Logs observés :

```text
TEMPORAL_NODE_STATE_OK | symbol=EURUSD | active_count=1 | highest_level=NODE_CONFIRMED
CURRENCY_ENERGY_OK | symbol=EURUSD
REGIME_LEGACY_OK | symbol=EURUSD | regime=UNKNOWN | confidence=0.0
BEHAVIORAL_ALERT_QUEUE_OK | symbol=EURUSD | behavioral_count=2 | degraded_count=1
```

Statut :

```text
EURUSD: ENGINE OK / REGIME HTF INCOMPLETE
```

Risque technique :

```text
EURUSD_HTF_CONTEXT_INCOMPLETE
EURUSD_REGIME_UNKNOWN
```

Interprétation :

```text
Le moteur exécute EURUSD correctement.
Le régime HTF reste UNKNOWN, probablement par historique HTF incomplet ou capture partielle.
```

---

### USDJPY

Logs observés :

```text
TEMPORAL_NODE_STATE_OK | symbol=USDJPY | active_count=0 | highest_level=NONE
CURRENCY_ENERGY_OK | symbol=USDJPY
REGIME_LEGACY_OK | symbol=USDJPY | regime=UNKNOWN | confidence=0.0
BEHAVIORAL_ALERT_QUEUE_OK | symbol=USDJPY | behavioral_count=1 | degraded_count=0
```

Cross-validation evidence :

```text
symbol: USDJPY
timestamp: 2026-05-04T12:20:00+00:00
rows: 1
timeframe: 1
```

Statut :

```text
USDJPY: ENGINE OK / DATA STALE_OR_THIN
```

Risques techniques :

```text
USDJPY_STALE_DATA
USDJPY_INSUFFICIENT_ROWS
USDJPY_CROSS_VALIDATION_LOW_CONFIDENCE
```

Interprétation :

```text
Le moteur sait exécuter USDJPY.
La DB ne fournit pas encore un flux USDJPY live exploitable.
La priorité n’est pas le scheduler mais la capture/historique USDJPY.
```

---

## 8. Cross-symbol validation

Commande appelée par le scheduler :

```powershell
python run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
```

Résultat observé :

```text
STEP_END cross_symbol_validation status=OK returncode=0
```

Sortie observée :

```text
USD label: WEAK
JPY label: STRONG
driver: cross-symbol computed
symbols_used: GBPUSD, EURUSD, USDJPY
```

Caveat technique :

```text
USDJPY contribue avec rows=1 et timestamp ancien.
EURUSD timestamp plus ancien que GBPUSD.
```

Conclusion :

```text
CROSS_VALIDATION_ENGINE: PASS
CROSS_VALIDATION_DATA_QUALITY: DEGRADED_BY_USDJPY
```

---

## 9. Dashboard refresh

Commande appelée par le scheduler :

```powershell
python run_powerflow_dashboard_refresh_once.py --skip-cockpit --refresh-cockpit-from-queue --pretty --summary
```

Résultat :

```text
DASHBOARD_FULL_REFRESH_OK
dashboard_out=dashboard_data.json
behavioral_flow=PRESENT
top_alert=FIRST_DETACHMENT_WITH_CLEAN_RELAY
top_level=HOT
has_hot=True
```

Statut :

```text
DASHBOARD_REFRESH: PASS
```

Note technique :

```text
Le refresh dashboard actuel reste principalement GBPUSD côté dashboard_data.json legacy.
Les outputs MultiSymbol sont disponibles dans output/dashboard_surface/{symbol}/.
```

---

## 10. Windows Task Scheduler

Tâche créée :

```text
PowerFlow_V72_MultiSymbol_Scheduler
```

Commande initiale créée :

```powershell
cmd.exe /c cd /d C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core && python scheduler_powerflow.py >> C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\logs\task_scheduler.log 2>&1
```

Correction appliquée pour éviter daemon permanent relancé toutes les 5 minutes :

```powershell
schtasks /Change /TN "PowerFlow_V72_MultiSymbol_Scheduler" /TR "cmd.exe /c cd /d C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core && python scheduler_powerflow.py --once >> C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\logs\task_scheduler.log 2>&1"
```

Commande effective validée :

```text
cmd.exe /c cd /d C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core && python scheduler_powerflow.py --once >> C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\logs\task_scheduler.log 2>&1
```

Planification :

```text
Répéter : toutes les 5 minutes
Mode : Interactive uniquement
Statut : Activée
```

---

## 11. Run automatique validé

Exécution forcée :

```powershell
schtasks /Run /TN "PowerFlow_V72_MultiSymbol_Scheduler"
```

Process observés :

```text
cmd.exe /c cd /d ... && python scheduler_powerflow.py ...
python scheduler_powerflow.py
pythoncore-3.14-64\python.exe scheduler_powerflow.py
```

Cycle automatique observé :

```text
CYCLE_START id=2 symbols=['GBPUSD', 'EURUSD', 'USDJPY']
...
CYCLE_END id=2 errors=0
```

Preuve finale :

```text
2026-05-11T14:03:47.526936+00:00 CYCLE_END id=2 errors=0
```

Verdict :

```text
WINDOWS TASK AUTO-RUN: PASS
```

---

## 12. Résultats successifs observés

### Cycle manuel

```text
cycle id=1
completed_cycles=1
duration_seconds=136.4
errors=0
```

### Cycle Windows automatique

```text
cycle id=2
errors=0
GBPUSD OK
EURUSD OK
USDJPY OK
cross_symbol_validation OK
dashboard_refresh OK
```

---

## 13. État Git observé pendant l’installation

Tentative de commit MultiSymbol :

```powershell
git commit -m "MultiSymbol: parametric symbol extension + cross-validation + scheduler"
```

Résultat :

```text
no changes added to commit
```

Interprétation :

```text
Les fichiers MultiSymbol étaient déjà copiés / identiques côté Git ou non modifiés au moment du commit.
L’échec git commit n’est pas un échec d’installation.
```

Changements non liés observés :

```text
modified: dashboard_data.json
untracked: _docs_pass_strict_update/
untracked: run_confluence_alert_production.ps1
untracked: run_telegram_v7.ps1
untracked: telegram_alert_dispatcher_v7.py
untracked: ../install_update_powerflow_multisymbol.ps1
```

Recommandation :

```text
Ne pas mélanger ces fichiers avec le commit MultiSymbol.
dashboard_data.json est probablement un output runtime.
Telegram doit faire l’objet d’un commit séparé.
```

---

## 14. Commandes de contrôle post-installation

### Vérifier tâche Windows

```powershell
schtasks /Query /TN "PowerFlow_V72_MultiSymbol_Scheduler" /V /FO LIST
```

### Vérifier scheduler log

```powershell
Get-Content .\logs\scheduler.log -Tail 80
```

### Vérifier task scheduler log

```powershell
Get-Content .\logs\task_scheduler.log -Tail 80
```

### Lancer cycle manuel si besoin

```powershell
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
```

### Tester cross-validation seule

```powershell
python run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
```

---

## 15. Recommandation intervalle scheduler

Intervalle actuel :

```text
5 minutes
```

Durée cycle observée :

```text
136 à 160 secondes environ
```

Conclusion :

```text
5 minutes est acceptable.
```

Si `OVERLAP_SKIP` devient fréquent :

```powershell
schtasks /Change /TN "PowerFlow_V72_MultiSymbol_Scheduler" /RI 10
```

---

## 16. Risques techniques restants

### 16.1 USDJPY data stale/thin

Preuve :

```text
USDJPY timestamp = 2026-05-04T12:20:00+00:00
USDJPY rows = 1
```

Impact :

```text
Cross-validation JPY/USD techniquement calculable mais faible confiance.
JPY_SAFE_HAVEN ou USD_WEAKNESS_DOMINANT peuvent être biaisés par donnée ancienne.
```

Action recommandée :

```text
Vérifier capture MT4 / bridge pour USDJPY.
Vérifier que USDJPY est bien dans les symboles actifs côté EA / capture.
Vérifier insertion DB force_snapshots WHERE symbol='USDJPY'.
```

---

### 16.2 EURUSD régime UNKNOWN

Preuve :

```text
EURUSD regime=UNKNOWN confidence=0.0
```

Impact :

```text
EURUSD fonctionne au niveau node/energy/mapper.
Le contexte HTF est incomplet.
```

Action recommandée :

```text
Accumuler historique HTF EURUSD.
Vérifier TF240 / TF1440 / TF10080 pour EURUSD.
```

---

### 16.3 Dashboard legacy encore GBPUSD-centric

Preuve :

```text
run_powerflow_dashboard_refresh_once.py affiche symbol=GBPUSD
dashboard_data.json reste legacy.
```

Impact :

```text
Les outputs MultiSymbol existent.
Mais le dashboard legacy central reste orienté GBPUSD.
```

Action recommandée :

```text
Intégrer dashboard_multisymbol_patch.html ou étendre dashboard_live_v7.2_final.html.
Ajouter tabs/dropdown GBPUSD/EURUSD/USDJPY/XAUUSD.
Lire output/dashboard_surface/{symbol}/.
```

---

## 17. Prochaines actions recommandées

Priorité 1 — Capture multi-symbol réelle :

```text
Vérifier pourquoi USDJPY n’a que 1 row.
Vérifier pourquoi EURUSD latest timestamp est ancien.
Confirmer que MT4/EA pousse bien GBPUSD, EURUSD, USDJPY.
```

Priorité 2 — Dashboard multi-symbol UI :

```text
Brancher les tabs symboles.
Afficher cross_validation card.
Afficher freshness par symbole.
```

Priorité 3 — Git propre :

```text
Créer un commit docs pour ce rapport.
Créer un commit Telegram séparé si les scripts Telegram sont validés.
Éviter de commit dashboard_data.json si c’est un output runtime.
```

---

## 18. Commit recommandé pour ce rapport

Depuis `Core` ou racine repo selon emplacement du fichier :

```powershell
git add Docs/2026/2026-05/RAPPORT_MULTISYMBOL_SCHEDULER_20260511.md
git commit -m "Docs: add MultiSymbol scheduler validation report"
git push
```

Si placé directement dans `Core` :

```powershell
git add RAPPORT_MULTISYMBOL_SCHEDULER_20260511.md
git commit -m "Docs: add MultiSymbol scheduler validation report"
git push
```

---

## 19. Verdict architecte

```text
PowerFlow V7.2 MultiSymbol Scheduler est opérationnel.

La boucle automatique fonctionne.
La garde anti-overlap fonctionne.
Le mode Windows Task Scheduler --once est propre.
Le cycle multi-symbol exécute GBPUSD, EURUSD, USDJPY.
La cross-validation s’exécute.
Le dashboard refresh s’exécute.
Aucune erreur moteur sur le cycle automatique validé.

Le blocage restant n’est pas scheduler.
Le blocage restant est data quality multi-symbol, surtout USDJPY.
```

Verdict final :

```text
MULTISYMBOL AUTO-RUN VALIDÉ ✅
GO DATA CAPTURE AUDIT EURUSD/USDJPY
```

---

## 20. Annexes — commandes exactes utiles

### Stopper anciens schedulers si besoin

```powershell
$procs = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match "scheduler_powerflow.py"
}

foreach ($p in $procs) {
    Stop-Process -Id $p.ProcessId -Force
}
```

### Supprimer lock stale

```powershell
if (Test-Path .\logs\scheduler_powerflow.lock) {
    Remove-Item .\logs\scheduler_powerflow.lock -Force
}
```

### Relancer test propre

```powershell
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
```

### Exécuter tâche Windows maintenant

```powershell
schtasks /Run /TN "PowerFlow_V72_MultiSymbol_Scheduler"
```

### Vérifier tâche

```powershell
schtasks /Query /TN "PowerFlow_V72_MultiSymbol_Scheduler" /V /FO LIST
```

### Vérifier dernier cycle

```powershell
Get-Content .\logs\scheduler.log -Tail 80
```

---

*Rapport généré pour archivage Git — PowerFlow V7.2 MultiSymbol Scheduler — 2026-05-11*
