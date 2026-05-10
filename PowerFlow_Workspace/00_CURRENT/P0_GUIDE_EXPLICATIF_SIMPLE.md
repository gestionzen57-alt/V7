# P0 — GUIDE EXPLICATIF SIMPLE
**Lundi 12 mai 23h CEST — Asian open**
**Qu'est-ce que tu vérifies et comment le remplir**

---

## CONTEXTE SIMPLIFIÉ

PowerFlow a 4 "capteurs" qui doivent être **VIVANTS** en marché ouvert :

```
B4  → Mesure si les oscillations se compriment (pré-signal de cassure)
B5  → Mesure si deux devises bougent ensemble ou en opposé
EIE → Mesure si une tension élastique se charge (élastique tendu)
Confluence → Accumule B4 + B5 + EIE dans une queue
```

Lundi, tu vérifies que ces 4 capteurs fonctionnent **vraiment**, pas qu'ils sont figés.

---

## LES 4 VÉRIFICATIONS SIMPLES

### 1️⃣ B4 TEMPORAL DENSITY — Teste les cycles

**La question que tu poses :**
> Les oscillations de GBP sur M5 se compriment-elles et se relaxent-elles ?

**Commande :**
```powershell
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
```

**Qu'est-ce que tu regardes dans la sortie :**

Cherche les lignes qui disent `CYCLE_COMPRESSING` ou `CYCLE_EXPANDING`.

```json
{
  "GBPUSD": {
    "TF5": {
      "cycle_state": "CYCLE_COMPRESSING",      ← c'est BON
      "compression_ratio": 0.78,                 ← entre 0 et 1 (1=très comprimé)
      "dominant_period_bars": 24                 ← nombre de barres dans un cycle
    }
  }
}
```

**Comment tu le remplis dans le template :**

```
[ ] dominant_period_bars TF1 : 18 (par exemple)
[ ] dominant_period_bars TF5 : 24 (par exemple)
[ ] cycle_state TF1 : CYCLE_EXPANDING
[ ] cycle_state TF5 : CYCLE_COMPRESSING

Verdict B4 : PASS ou FAIL ?
  PASS  = dominant_period ≠ 1 ET cycle_state = COMPRESSING ou EXPANDING
  FAIL  = dominant_period = 1 partout (figé, marché mort)
```

**Ce que signifie chaque état :**

```
CYCLE_COMPRESSING    = oscillations qui se resserrent → rupture possible bientôt
CYCLE_EXPANDING      = oscillations qui s'élargissent → respiration
CYCLE_STABLE         = oscillations même fréquence
CYCLE_NOISY          = pas de cycle clair (bruit)
```

✅ **PASS B4** = Tu vois du COMPRESSING ou EXPANDING, pas STABLE ou NOISY.

---

### 2️⃣ B5 SPEARMAN GRAVITY — Teste les corrélations paires

**La question que tu poses :**
> Quand GBP monte, USD descend-il vraiment ? Ou est-ce aléatoire ?

**Commande :**
```powershell
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
```

**Qu'est-ce que tu regardes dans la sortie :**

Cherche les colonnes `spearman_rho` (corrélation entre -1.0 et +1.0).

```json
{
  "GBP_USD": {
    "TF5": {
      "spearman_rho": -0.72,                   ← négatif = opposés
      "direction": "DIVERGENT",                 ← label si rho < -0.50
      "tail_signal": "MIXED_PROBABILISTE"      ← détail technique
    }
  }
}
```

**Comment tu le remplis :**

```
[ ] rho GBP_USD TF1  : -0.65 (exemple)
[ ] rho GBP_USD TF5  : -0.72 (exemple)
[ ] Labels non figés  : OUI si les valeurs changent entre snapshots, NON si toujours mêmes rho
[ ] avg_rho fluctuant : OUI si rho TF1 ≠ rho TF5, NON si identiques

Verdict B5 : PASS ou FAIL ?
  PASS  = rho non figé (change), labels varient (SYNCHRO/DIVERGENT/NEUTRAL)
  FAIL  = rho toujours 0.0 ou toujours -0.85 (figé)
```

**Ce que signifie chaque label :**

```
rho > 0.70          = SYNCHRO (devises bougent ensemble)
-0.50 < rho < 0.70  = NEUTRAL (relation faible)
rho < -0.50         = DIVERGENT (devises en opposition)
rho > 0.85          = CODEPENDANT_EXTREME (très liés)
rho < -0.85         = DIVERGENT_EXTREME (très opposés)
```

✅ **PASS B5** = Tu vois des rho qui varient (pas tous -0.72), et les labels changent (SYNCHRO, DIVERGENT, NEUTRAL).

---

### 3️⃣ EIE CONFLUENCE — Teste la tension élastique

**La question que tu poses :**
> Y a-t-il une zone chargée d'énergie élastique prête à relâcher ?

**Commande :**
```powershell
python -c "from lab_elastic import q_eie_snapshot; q_eie_snapshot()"
```

**Qu'est-ce que tu regardes :**

Cherche l'état EIE (Elastic In Extreme).

```json
{
  "EIE_state": "ELASTIC_IN_EXTREME",    ← c'est BON
  "fractalite": 2,                       ← nombre de TF chargés (0-3)
  "elastic_score": 0.84                  ← intensité (0-1)
}
```

**Comment tu le remplis :**

```
[ ] EIE snapshot : ELASTIC_IN_EXTREME (exemple) ou NEUTRAL
[ ] fractalite : 2 (nombre de TF simultanément en zone active)
[ ] elastic_score : 0.84 (entre 0 et 1)
[ ] EIE ≠ NEUTRAL : OUI si ELASTIC_IN_EXTREME, NON si NEUTRAL

Verdict EIE : PASS ou FAIL ?
  PASS  = EIE_state = ELASTIC_IN_EXTREME (pas NEUTRAL)
  FAIL  = EIE_state = NEUTRAL toujours (aucune tension détectée)
```

**Ce que signifie chaque état :**

```
ELASTIC_IN_EXTREME (EIE) = zone active + élastique chargé → relâchement possible
NEUTRAL                  = pas de tension, pas d'alerte
```

✅ **PASS EIE** = Tu vois au moins une fois `ELASTIC_IN_EXTREME`, pas `NEUTRAL` permanent.

---

### 4️⃣ SESSION OVERLAY & ENTROPY — Contexte live

**La question que tu poses :**
> Quelle session est active maintenant ? Combien d'alertes sortent ?

**Commandes :**
```powershell
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
python .\run_session_overlay_once.py --timestamp now --pretty
```

**Qu'est-ce que tu regardes :**

Session overlay :
```json
{
  "session": "ASIAN",              ← lundi 23h CEST = ASIAN ouverture
  "session_phase": "IGNITION",     ← phase du début
  "minutes_since_open": 14         ← 14 minutes après ouverture
}
```

Entropy :
```json
{
  "alert_entropy_state": "NORMAL_ALERT_FLOW",  ← pas saturé
  "normalized_entropy": 0.32,                    ← 0-1 (0=répétitif, 1=varié)
  "duplication_ratio": 0.0                       ← pas d'alertes dupliquées
}
```

**Comment tu le remplis :**

```
Session Overlay :
[ ] session : ASIAN (lundi 23h CEST)
[ ] session_phase : IGNITION ou MID_SESSION
[ ] minutes_since_open : le chiffre que tu vois (ex: 14)
Verdict : CORRECT si session=ASIAN et phase=IGNITION

Entropy :
[ ] alert_entropy_state : NORMAL_ALERT_FLOW (ou BURST_ACTIVE ou SATURATED)
[ ] normalized_entropy : le chiffre (ex: 0.32)
Verdict : NORMAL si NORMAL_ALERT_FLOW
```

✅ **PASS Session** = `session=ASIAN` et `session_phase=IGNITION` à 23h CEST.

---

### 5️⃣ DAEMON CONFLUENCE — Teste la queue

**La question que tu poses :**
> Les alertes EIE s'ajoutent-elles correctement à la queue sans doublon ?

**Commande :**
```powershell
python run_confluence_alert.py --once --dry-run
```

**Qu'est-ce que tu regardes :**

```
behavioral_alert_queue.json doit s'ajouter des entrées (append, pas remplacement).
Aucun JSON invalide.
Aucun doublon massif.
```

**Comment tu le remplis :**

```
[ ] run_confluence_alert.py --once : OK ou FAIL (commande lancée ?)
[ ] behavioral_alert_queue.json mis à jour : OUI ou NON
[ ] Entries sans doublons : OUI ou NON (regarder le fichier)

Verdict Daemon : OK ou FAIL
  OK   = queue écrite, pas de doublon
  FAIL = queue non écrite ou JSON invalide
```

✅ **PASS Daemon** = Queue existe, contient des entrées, JSON valide.

---

## TEMPLATE DE RAPPORT À REMPLIR

Tu dois remplir le template avec tes observations. Voici un exemple complété :

```markdown
# P0 — VALIDATION MARCHÉ OUVERT
Date : 2026-05-12 | Session : ASIAN | Heure début : 23h CEST

## B4 TEMPORAL DENSITY
[x] dominant_period_bars TF1 : 18 (PASS ≠ 1)
[x] dominant_period_bars TF5 : 24 (PASS ≠ 1)
[x] cycle_state TF1 : CYCLE_EXPANDING
[x] cycle_state TF5 : CYCLE_COMPRESSING
Verdict B4 : PASS

## B5 SPEARMAN GRAVITY
[x] rho GBP_USD TF1 : -0.65
[x] rho GBP_USD TF5 : -0.72
[x] Labels non figés : OUI (rho varie, labels changent)
[x] avg_rho fluctuant : OUI
Verdict B5 : PASS

## EIE CONFLUENCE
[x] EIE snapshot : ELASTIC_IN_EXTREME
[x] fractalite : 2
[x] elastic_score : 0.84
[x] EIE ≠ NEUTRAL : OUI
Verdict EIE : PASS

## SESSION OVERLAY
[x] session : ASIAN
[x] session_phase : IGNITION
[x] minutes_since_open : 14
Verdict Session : CORRECT

## ENTROPY
[x] alert_entropy_state : NORMAL_ALERT_FLOW
[x] normalized_entropy : 0.32
Verdict : NORMAL

## DAEMON CONFLUENCE
[x] run_confluence_alert.py --once : OK
[x] behavioral_alert_queue.json mis à jour : OUI
[x] Entries sans doublons : OUI
Verdict Daemon : OK

## VERDICT GLOBAL P0
[x] PASS complet → lancer Task Scheduler P1
```

---

## RÉSUMÉ — LES CRITÈRES P0 PASS

✅ **P0 est PASS si :**

```
B4   : dominant_period_bars ≠ 1 ET cycle_state = COMPRESSING ou EXPANDING
B5   : rho fluctuant ET labels varient (SYNCHRO/DIVERGENT/NEUTRAL)
EIE  : EIE_state ≠ NEUTRAL au moins une fois
Session : session=ASIAN ET session_phase=IGNITION
Entropy : alert_entropy_state ≠ SATURATED
Daemon : queue écrite, pas doublon massif
```

❌ **P0 est FAIL si :**

```
B4   : dominant_period=1 partout (marché mort)
B5   : rho figé (toujours mêmes valeurs)
EIE  : toujours NEUTRAL (aucune tension)
Session : pas ASIAN ou pas IGNITION
Daemon : queue non écrite ou JSON invalide
```

---

## POINTS CLÉS À RETENIR

```
1. Tu n'analyzes PAS le marché toi-même
2. Tu vérifies juste que les capteurs FONCTIONNENT (vivants, pas figés)
3. B4 = oscillations varient-elles ?
4. B5 = devises sont-elles corrélées ou pas ?
5. EIE = y a-t-il une tension ?
6. Session = c'est bien ASIAN ?
7. Entropy = pas saturé d'alertes ?
8. Daemon = queue tourne ?

C'est un test de capteurs, pas un test de trading.
```

---

*Guide P0 — Simple — Remplissable — 2026-05-09*
