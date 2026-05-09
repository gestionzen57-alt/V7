# PLAN D’ACTION À LEVIER — POWERFLOW V6.1
## Objectif : ne plus être esclave de PowerFlow

---

## Vision

PowerFlow doit devenir un copilote de session :

```text
il voit
il traduit
il alerte
il se tait quand rien n’est frais
il signale quand sa chaîne est cassée
```

Le trader doit pouvoir tester / affiner son trading sans surveiller 15 scripts.

---

# Priorité 0 — Freeze des nouvelles briques marché

Durée recommandée :

```text
3 à 7 jours
```

Décision :

```text
Ne pas créer de nouveau détecteur marché tant que la chaîne live n’est pas stable.
```

Pourquoi :

```text
Les briques actuelles suffisent pour produire de la valeur :
Node / Release / Energy / Relational Gravity / Behavioral Flow / Trader Alert / Telegram.
```

Angle mort évité :

```text
accumuler de l’intelligence sans exploitation claire.
```

---

# Priorité 1 — Runtime Health Check renforcé

## Levier

Très fort.

## Pourquoi

PowerFlow doit te dire s’il est fiable maintenant.

## Fichier cible

```text
pf_runtime_health_check.py
```

## Sortie

```text
output/runtime_health.json
```

## Résumé voulu

```text
RUNTIME_HEALTH_OK
ou
RUNTIME_HEALTH_WARN:
- dashboard stale
- queue plus récente que cockpit
- Telegram non configuré
- double writer suspect
```

## Angle mort actuel

Le système peut fonctionner partiellement sans que ce soit visible immédiatement.

Exemples :

```text
dashboard frais mais trader_alert ancien
queue fraîche mais cockpit non refresh
Telegram configuré mais trader_alert_ready=false
double writer dashboard
```

---

# Priorité 2 — Dashboard Trader Panel

## Levier

Très fort pour concentration.

## Pourquoi

Le dashboard affiche encore beaucoup de logique moteur.
Le trader a besoin d’un bloc simple.

## Source

```text
output/trader_alert_state.json
```

## Affichage cible

```text
TRADER ALERT
HOT / WATCH / INFO / SILENCE
message court
âge
freshness
contradictions
action = WATCH / SILENCE
```

## Angle mort actuel

Behavioral Flow est utile mais encore moteur.
Trader Alert State est plus proche du besoin réel.

---

# Priorité 3 — Core Audit / Module Registry

## Levier

Fort pour ne plus se perdre.

## Fichiers

```text
POWERFLOW_MODULE_REGISTRY.json
pf_core_audit.py
```

## Catégories

```text
ACTIVE_CORE
ACTIVE_ENGINE
ACTIVE_RUNNER
ACTIVE_DASHBOARD
ACTIVE_TELEGRAM
TEST
FIXTURE
REPORT
PATCH
BACKUP
LEGACY
ARCHIVE_CANDIDATE
```

## Angle mort actuel

Le Core contient :

```text
backups
patchs
versions before_*
fixtures
reports
anciens runners
modules actifs
legacy
```

Sans registry, un nettoyage peut casser la chaîne.

---

# Priorité 4 — Git checkpoint + cleanup branch

## Levier

Fort pour sécurité.

## Ordre

```powershell
git status
git checkout -b checkpoint/v61-livecycle
git add .
git commit -m "checkpoint: PowerFlow V6.1 live cycle trader alert telegram"
git checkout -b chore/core-cleanup-v61
```

## Angle mort actuel

Trop de modifications validées runtime peuvent être perdues ou mélangées.

---

# Priorité 5 — Boucle live contrôlée

## Levier

Moyen / fort, mais à ne faire qu’après Health Check.

## Pourquoi attendre

Une boucle 30s sans Health Check peut spammer ou masquer une incohérence.

## Fichier futur

```text
run_powerflow_live_loop.ps1
```

## Règles

```text
cooldown
logs JSONL
health check
mode Telegram explicite
stop propre
pas deux instances
```

---

# Priorité 6 — Dashboard State V2

## Levier

Fort long terme.

## Pourquoi

dashboard_data.json est devenu un agrégat patché.
Il faut stabiliser une sortie officielle.

## Fichiers

```text
PF_COCKPIT_DASHBOARD_STATE_V2_SPEC.md
pf_cockpit_dashboard_state.py
```

## Angle mort actuel

Plus on patch le dashboard, plus il devient fragile.

---

# Priorité 7 — Moyen / long terme

À garder pour plus tard :

```text
TemporalDensity production
TemporalWindowActive
multi-symbol broader mode
session profiles
weekly / daily structures
```

Pourquoi plus tard :

```text
PowerFlow doit d’abord être exploitable sur ton profil court terme.
```

---

# Synthèse priorité

```text
P0 Freeze market features
P1 Runtime Health Check
P2 Dashboard Trader Panel
P3 Core Audit / Registry
P4 Git checkpoint
P5 Live Loop controlled
P6 Dashboard State V2
P7 Medium-long expansion
```

---

# Phrase noyau

```text
Le prochain niveau de PowerFlow n’est pas plus de détection.
C’est moins de friction, plus de clarté, plus d’automatisation sûre.
```
