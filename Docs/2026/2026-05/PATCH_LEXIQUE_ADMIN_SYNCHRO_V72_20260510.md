# PATCH LEXIQUE — ADMIN SYNCHRO / PROMPT ROUTING — PowerFlow V7.2

**Date : 2026-05-10**  
**Statut : patch lexique proposé**  
**Domaine : Administration technique, Git, synchronisation de mission, continuité inter-IA**  
**But : éviter que les docs obsolètes ou les coupures de session fassent refaire des briques déjà finalisées**

---

## 19. ADMINISTRATION, GIT ET CONTINUITÉ DE SESSION (V7.2)

### ADMIN_DRIFT

Décalage entre l'état réel du dépôt Git et les documents d'administration.

Exemple :
- un checkpoint dit “B6 à faire” ;
- `git log` montre que B6 est déjà finalisé et pushé.

Risque technique :
- mission répétée ;
- écrasement de code validé ;
- confusion sur la prochaine étape ;
- perte de temps.

Traitement :
- toujours vérifier `git status` + `git log --oneline -12` avant de relancer une mission.

---

### SOURCE_OF_TRUTH_GIT

Principe selon lequel Git devient la source de vérité opérationnelle quand les rapports et checkpoints se contredisent.

Ordre de priorité :

```text
1. git status
2. git log --oneline
3. git log --oneline -- fichier
4. py_compile / runners
5. rapports Markdown
6. anciens prompts
```

Usage :
- décider si une brique est déjà faite ;
- déterminer si un prompt est encore valide ;
- éviter de refaire une mission obsolète.

---

### STALE_CHECKPOINT

Checkpoint devenu partiellement faux car l'état Git a progressé depuis sa rédaction.

Exemple :
un document indique :

```text
À faire : commit B4 Wavelet
```

mais Git montre déjà :

```text
6640dfc B4: finalize Wavelet density standalone
```

Un `STALE_CHECKPOINT` ne doit pas être supprimé aveuglément ; il doit être marqué comme historique ou remplacé par un checkpoint plus récent.

---

### PROMPT_MISMATCH

Situation où un prompt reçu ne correspond pas à la mission réellement nécessaire.

Exemple :
l'utilisateur pense recevoir un prompt pour refaire B6, mais le texte est en réalité :

```text
PROMPT 2 — TEST BATCH COMPLET TOUTES BRIQUES POWERFLOW V7.2
```

Traitement :
- identifier le type réel du prompt ;
- vérifier les commits existants ;
- router vers la bonne opération.

---

### PROMPT_SUPERSEDED

Prompt rendu obsolète par des commits plus récents.

Exemple :
un prompt demande de créer `pf_memory_engine.py`, mais Git montre :

```text
dc0eee1 Memory: V1 pattern indexing engine
e25b0ca B6: finalize Memory Engine pattern indexing
```

Conclusion :
le prompt ne doit pas être exécuté tel quel.

---

### BRIQUE_SUPERSEDED

Brique déjà implémentée dans un commit initial, puis renforcée par un commit final.

Exemple :

```text
dc0eee1 Memory: V1 pattern indexing engine
e25b0ca B6: finalize Memory Engine pattern indexing
```

Dans ce cas :
- `dc0eee1` = version initiale ;
- `e25b0ca` = version finalisée ;
- la brique ne doit pas être recodée.

---

### VALIDATION_COMMIT

Commit dont le rôle n'est pas de créer une nouvelle brique, mais de valider ou outiller des briques existantes.

Exemple :

```text
7c6aa9c Validation: add B1 B4 B6 validation runner
```

Usage :
- ajouter scripts de test ;
- sécuriser un passage production ;
- ne pas confondre avec une brique moteur.

---

### SESSION_CLOSE_HELPER

Script de fin de session qui automatise la synchronisation Git sans polluer le dépôt.

Fichier :

```text
pf_close_session.ps1
```

Rôle :
- restaurer suppressions accidentelles ;
- ignorer outputs runtime ;
- protéger fichiers stables ;
- exécuter py_compile sur les fichiers Core modifiés ;
- commit/push proprement.

Usage normal :

```powershell
.\pf_close_session.ps1 "V7.2: fin de session propre"
```

---

### CLEAN_WORKTREE_GATE

Point de contrôle obligatoire avant de lancer une mission nouvelle.

Commande :

```powershell
git status
```

État attendu :

```text
nothing to commit, working tree clean
```

Si le workspace n'est pas clean :
- ne pas lancer nouvelle mission ;
- nettoyer ou committer d'abord ;
- éviter de mélanger code, docs et output.

---

### CLI_EVIDENCE

Preuve issue de commandes terminales plutôt que d'un rapport narratif.

Exemples :

```powershell
git log --oneline -12
git log --oneline -- Core\pf_memory_engine.py
python -m py_compile Core\pf_memory_engine.py
```

Usage :
- trancher un doute ;
- vérifier qu'une brique existe ;
- confirmer qu'un prompt n'est plus nécessaire.

---

### PROMPT_ROUTE_DECISION

Décision de router un prompt vers :
- recodage ;
- validation ;
- documentation ;
- dashboard ;
- P0 live.

Exemple :

```text
Prompt fourni = Prompt 2 batch tests
Décision = validation globale
Action interdite = refaire B6
```

---

### B6_MEMORY_ALREADY_FINALIZED

État spécifique indiquant que la brique B6 Memory Engine existe déjà et ne doit pas être refaite.

Preuves attendues :

```text
Core/pf_memory_engine.py existe
Core/run_memory_query_once.py existe
git log contient dc0eee1 puis e25b0ca
```

Action :
- passer au batch test ;
- ne pas relancer Prompt 1 B6.

---

### BATCH_TEST_PROMPT_2

Mission de validation globale post-finalisation des briques.

Rôle :
- lancer toutes les briques ;
- produire rapports JSON / HTML / CSV / Markdown ;
- classer PASS / PARTIAL / FAIL / MISSING ;
- identifier conditions weekend/static ;
- préparer Prompt 3 Dashboard.

Ne doit pas :
- modifier B1/B4/B6 ;
- écrire dans la DB ;
- committer automatiquement `output/`.

---

### ROBUST_JSON_CAPTURE

Méthode d'extraction JSON tolérante pour les runners CLI.

Problème évité :
les JSON pretty multi-lignes ne peuvent pas être parsés en gardant seulement les lignes qui commencent par `{` ou `[`.

Méthode recommandée :
- détecter le premier bloc JSON valide dans stdout ;
- sinon stocker `raw_output` ;
- qualifier `FAIL_JSON`, pas crasher.

---

### RUNNER_MISSING_IS_NOT_FAIL

Principe selon lequel un runner absent dans un batch test ne doit pas casser toute la validation.

État à produire :

```json
{
  "status": "MISSING",
  "technical_risks": ["RUNNER_NOT_FOUND"]
}
```

Usage :
- batch test robuste ;
- migration progressive ;
- éviter les faux échecs globaux.

---

### PARTIAL_NOT_FAIL

État intermédiaire pour une brique qui tourne mais dont les données sont limitées.

Exemples :
- `SILENT`
- `SMALL_SAMPLE_SIZE`
- `INSUFFICIENT_DATA`
- `WEEKEND_STATIC`
- `LOW_STATE_DIVERSITY`

`PARTIAL` signifie :
la brique est exécutable, mais la perception est limitée par le contexte de données.

---

### OUTPUT_NOT_SOURCE_OF_TRUTH

Principe selon lequel les fichiers `output/` sont des interfaces runtime, pas la vérité administrative.

Conséquence :
- ils peuvent être régénérés ;
- ils peuvent être ignorés par Git ;
- s'ils doivent être archivés, les copier vers `Docs/2026/2026-05/`.

---

### DOCS_ARCHIVE_COMMIT

Commit dont le but est d'archiver des rapports stabilisés dans `Docs/`.

Exemple :

```text
Docs: archive V7.2 admin sync reports
```

Ne doit pas inclure :
- fichiers runtime massifs ;
- `.pkl` ;
- outputs temporaires ;
- DB.

---

### TECHNICAL_ADMIN_RISK

Risque technique causé par l'administration, pas par le moteur.

Exemples :
- doc obsolète ;
- prompt obsolète ;
- mauvais commit ciblé ;
- output mélangé au code ;
- rapport non synchronisé ;
- workspace sale.

Usage :
- expliciter la friction sans moraliser ;
- corriger le processus.

---

### PROMPT_CONTINUITY_PACKET

Petit paquet de contexte à transmettre à Claude/GPT quand le fil précédent est coupé.

Contenu minimal :

```text
git status = clean
HEAD = <commit>
commits clés = [...]
briques déjà finalisées = [...]
mission interdite = [...]
prochaine mission proposée = [...]
```

But :
éviter que le nouvel agent reparte sur un checkpoint ancien.

---

### ADMIN_SYNC_REPORT

Rapport de synchronisation entre Git, docs et prompts.

Rôle :
- dire ce qui est réellement fait ;
- dire ce qui est obsolète ;
- dire ce qu'il ne faut pas refaire ;
- proposer l'opération suivante.

Fichier recommandé :

```text
RAPPORT_COMPLET_SYNCHRO_ADMIN_V72_YYYYMMDD.md
```

---

### LEXIQUE_ADMIN_PATCH

Patch lexique dédié aux termes d'administration technique.

Fichier recommandé :

```text
PATCH_LEXIQUE_ADMIN_SYNCHRO_V72_YYYYMMDD.md
```

But :
faire entrer dans le langage PowerFlow les risques de friction inter-IA et de dérive documentaire.

---

## PATCH À INTÉGRER DANS LA DOCTRINE DE TRAVAIL

### Règle : Git avant prompt

Avant d'exécuter un prompt reçu d'un autre agent :

```powershell
git status
git log --oneline -12
```

Puis répondre :

```text
Ce prompt est-il encore nécessaire ?
Est-ce une mission de code, test, docs, dashboard ou P0 ?
Quels fichiers risque-t-il d'écraser ?
```

### Règle : ne jamais refaire une brique finalisée sans diff

Si une brique a un commit final visible, ne pas la recoder sans :

```powershell
git diff
git log --oneline -- fichier
```

### Règle : Prompt 2 ne modifie pas Core

Prompt 2 = batch tests / observabilité.

Il peut créer :

```text
test_batch_all_bricks.py
output/*.json
output/*.html
output/*.csv
output/*.md
```

Il ne doit pas modifier :

```text
Core/pf_*.py
Core/run_*.py
```

sauf demande explicite après rapport d'erreur.

### Règle : output lisible, docs archivées

Les outputs sont pour lire vite.  
Les docs sont pour garder trace.  
Ne pas confondre les deux.
