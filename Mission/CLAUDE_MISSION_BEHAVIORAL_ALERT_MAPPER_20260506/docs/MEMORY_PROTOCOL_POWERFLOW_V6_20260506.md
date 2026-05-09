# MEMORY_PROTOCOL — POWERFLOW V6

Date : 2026-05-06
Statut : protocole mémoire sereine

## Règle centrale

```text
Le Drive garde les fichiers.
CURRENT_STATE et CHECKPOINT_LATEST disent la vérité actuelle.
```

## À chaque fin de mission

Chaque fil IA doit produire :

```text
1. RAPPORT
2. CHECKPOINT COURT
3. LEXIQUE À INTÉGRER
4. CURRENT_STATE UPDATE
5. NEXT ACTION
```

## Dossiers cibles

```text
00_CURRENT/CURRENT_STATE.md
00_CURRENT/CHECKPOINT_LATEST.md
00_CURRENT/ROADMAP_ACTIVE.md
00_CURRENT/LEXIQUE_UPDATE_QUEUE.md

04_CHECKPOINTS/YYYY/YYYY-MM/YYYY-MM-DD/
03_REPORTS/YYYY/YYYY-MM/YYYY-MM-DD/
02_DOCS_ACTIVE/LEXIQUE_GRAMMAIRE/
07_SPECS/SPECS_ACTIVE/
```

## Nouveau fil IA — protocole obligatoire

```text
Lis d’abord :
00_CURRENT/CURRENT_STATE.md
00_CURRENT/CHECKPOINT_LATEST.md
00_CURRENT/ROADMAP_ACTIVE.md
00_CURRENT/LEXIQUE_UPDATE_QUEUE.md

Puis dis-moi quel est le dernier état PowerFlow que tu vois.
Si tu t’arrêtes à Node V0.7.1, ton contexte est obsolète.
Dernier état attendu :
Node V0.8.1 + Currency Energy V0.1.
```

## Agents futurs

```text
Runtime Snapshot Agent
Behavioral Alert Agent
Dashboard Sync Agent
Checkpoint Agent
Lexique Queue Agent
```

Ordre :

```text
D’abord voir.
Ensuite alerter.
Ensuite afficher.
Ensuite mémoriser.
```
