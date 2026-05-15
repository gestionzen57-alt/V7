# 🚀 PowerFlow V7.6.7 — Installation Infrastructure

**Date:** 2026-05-15  
**Objectif:** Installer automatisations Git, checkpoints, lexique, cleanup

---

## 📦 Contenu livraison

Fichiers créés par Claude Sonnet 4.5:

```
scripts/
├── auto_git_sync.ps1              # Synchronisation Git automatique
├── auto_checkpoint_claude.ps1     # Checkpoint fin session Claude
├── sync_lexique.ps1               # Consolidation lexique unifié
└── cleanup_backups.ps1            # Nettoyage backups anarchiques

Docs/
├── CLAUDE.md                      # État central PowerFlow (auto-généré)
├── LEXIQUE_MASTER.md              # Lexique unifié (à générer)
├── DISPATCH_STATUS.json           # Coordination 6 IA
├── Checkpoints/                   # Checkpoints sessions (auto)
└── Archive/                       # Archives anciennes versions

git/
└── sync.log                       # Log Git automatique
```

---

## ⚡ Installation rapide (5 min)

### Étape 1 : Copier fichiers

Depuis le répertoire où tu as téléchargé les fichiers Claude:

```powershell
# Créer structure
New-Item -ItemType Directory -Path "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\scripts" -Force
New-Item -ItemType Directory -Path "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Docs\Checkpoints" -Force
New-Item -ItemType Directory -Path "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Docs\Archive" -Force
New-Item -ItemType Directory -Path "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\git" -Force

# Copier scripts
Copy-Item -Path ".\auto_git_sync.ps1" -Destination "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\scripts\" -Force
Copy-Item -Path ".\auto_checkpoint_claude.ps1" -Destination "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\scripts\" -Force
Copy-Item -Path ".\sync_lexique.ps1" -Destination "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\scripts\" -Force
Copy-Item -Path ".\cleanup_backups.ps1" -Destination "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\scripts\" -Force

# Copier docs
Copy-Item -Path ".\CLAUDE.md" -Destination "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Docs\" -Force
Copy-Item -Path ".\DISPATCH_STATUS.json" -Destination "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Docs\" -Force
```

### Étape 2 : Test Git sync

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
.\scripts\auto_git_sync.ps1 -Verbose
```

**Résultat attendu:**
```
🔄 PowerFlow Git Auto-Sync V7.6.7
📊 Vérification changements...
📝 X fichier(s) modifié(s) détecté(s)
➕ Staging fichiers...
💬 Message: 📋 Infrastructure automation scripts + Docs/ structure
💾 Commit en cours...
⬇️ Pull dernières modifications...
⬆️ Push vers GitHub...
✅ SYNCHRONISATION RÉUSSIE
```

### Étape 3 : Générer LEXIQUE_MASTER.md

```powershell
.\scripts\sync_lexique.ps1 -Verbose
```

**Résultat attendu:**
```
📚 PowerFlow Lexique Consolidator V7.6.7
🔍 Recherche patches lexique...
📄 28 patch(es) trouvé(s)
🔨 Génération LEXIQUE_MASTER.md...
✅ LEXIQUE_MASTER.md généré
✅ CONSOLIDATION LEXIQUE TERMINÉE
```

### Étape 4 : Checkpoint initial

```powershell
.\scripts\auto_checkpoint_claude.ps1 -Verbose
```

**Résultat attendu:**
```
📋 PowerFlow Checkpoint Auto-Generator V7.6.7
🎯 Focus détecté: Infrastructure Admin
📝 X fichier(s) modifié(s)
💾 Génération checkpoint...
✅ Checkpoint créé: CHECKPOINT_20260515_XXXXXX.md
📄 Mise à jour CLAUDE.md...
✅ CLAUDE.md mis à jour
🔄 Synchronisation Git...
✅ CHECKPOINT COMPLET
```

### Étape 5 : Scan backups (sans suppression)

```powershell
.\scripts\cleanup_backups.ps1
```

**Résultat attendu:**
```
🧹 PowerFlow Backup Cleaner V7.6.7
⚠️ MODE SCAN — Aucune modification ne sera effectuée
🔍 Recherche backups...
📁 X backup(s) détecté(s)

📊 ANALYSE BACKUPS
[Liste des backups par catégorie]

📈 STATISTIQUES
Backups trouvés:     X
Backups à conserver: Y
Backups à supprimer: Z
Espace libéré:       XX MB
```

---

## 🔄 Usage quotidien

### Fin de session Claude

**Automatique** (recommandé):
```powershell
.\scripts\auto_checkpoint_claude.ps1
```

**Manuel** (si besoin focus custom):
```powershell
.\scripts\auto_checkpoint_claude.ps1 -Focus "Dashboard refactor" -NoGit
```

### Sync Git ad-hoc

**Auto-détection message:**
```powershell
.\scripts\auto_git_sync.ps1
```

**Message custom:**
```powershell
.\scripts\auto_git_sync.ps1 -Message "🐛 Hotfix USDJPY capture bridge"
```

**Force push (même sans changements):**
```powershell
.\scripts\auto_git_sync.ps1 -Force
```

### Consolidation lexique (hebdomadaire)

**Consolidation simple:**
```powershell
.\scripts\sync_lexique.ps1
```

**Avec archivage patches:**
```powershell
.\scripts\sync_lexique.ps1 -Archive
```

### Nettoyage backups (mensuel)

**Scan seulement:**
```powershell
.\scripts\cleanup_backups.ps1
```

**Exécution réelle:**
```powershell
.\scripts\cleanup_backups.ps1 -Execute
```

**Sans archivage:**
```powershell
.\scripts\cleanup_backups.ps1 -Execute -NoArchive
```

---

## 📋 Workflow recommandé

### Début de session Claude

1. Lire `Docs/CLAUDE.md` pour contexte
2. Consulter `Docs/DISPATCH_STATUS.json` pour tâches
3. Travailler normalement

### Fin de session Claude

```powershell
# Automatique (recommandé)
.\scripts\auto_checkpoint_claude.ps1

# OU manuel si modifications importantes
.\scripts\auto_git_sync.ps1 -Message "🚀 Feature X completed"
.\scripts\auto_checkpoint_claude.ps1 -Focus "Feature X" -NoGit
```

### Hebdomadaire (vendredi soir)

```powershell
# Consolidation lexique
.\scripts\sync_lexique.ps1 -Archive

# Sync final
.\scripts\auto_git_sync.ps1 -Message "📚 Weekly lexique consolidation"
```

### Mensuel (fin de mois)

```powershell
# Nettoyage backups
.\scripts\cleanup_backups.ps1 -Execute

# Sync
.\scripts\auto_git_sync.ps1 -Message "🧹 Monthly backup cleanup"
```

---

## 🔧 Dépannage

### Erreur: "Execution of scripts is disabled"

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erreur Git: "fatal: not a git repository"

Vérifier que `.git` existe:
```powershell
Test-Path "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\.git"
```

Si `False`, initialiser Git:
```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
git init
git remote add origin https://github.com/gestionzen57-alt/V7.git
git pull origin main
```

### Erreur: "Cannot find path"

Vérifier chemins dans scripts (variables `$RepoPath`).

### Script bloqué

Tuer processus PowerShell:
```powershell
Get-Process powershell | Stop-Process -Force
```

---

## 📊 Vérification installation

**Checklist post-installation:**

- [ ] `scripts/` existe avec 4 fichiers .ps1
- [ ] `Docs/CLAUDE.md` existe
- [ ] `Docs/DISPATCH_STATUS.json` existe
- [ ] `Docs/LEXIQUE_MASTER.md` généré (via sync_lexique.ps1)
- [ ] `Docs/Checkpoints/` existe
- [ ] Git sync fonctionne (test avec -Verbose)
- [ ] Checkpoint auto fonctionne
- [ ] Scan backups affiche résultats

**Commande test rapide:**
```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
.\scripts\auto_git_sync.ps1 -Verbose
```

---

## 📞 Support

**En cas de problème:**

1. Vérifier logs Git: `git\sync.log`
2. Vérifier execution policy PowerShell
3. Relancer script avec `-Verbose` pour debug
4. Consulter `DISPATCH_STATUS.json` pour état système
5. Créer checkpoint manuel si auto échoue

**Rétablir état précédent:**
```powershell
git reset --hard HEAD~1
```

---

*Installation générée par Claude Sonnet 4.5*  
*PowerFlow V7.6.7 — Infrastructure Automation Pack*  
*2026-05-15*
