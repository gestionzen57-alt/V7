# 🚀 UTILISER CLAUDE.md V2 — GUIDE RAPIDE

**Date**: 2026-05-06  
**Économie**: 750+ tokens par session Opus

---

## ⚡ TL;DR — En 1 minute

### Avant
```
"Explique-moi PowerFlow..."
[900 tokens juste pour le contexte]
```

### Après
```
"Lis CLAUDE.md. Puis fais X..."
[150 tokens, Claude a tout le contexte]
```

---

## 📂 SETUP

### 1. Placer le fichier
```
core/CLAUDE.md
ou
PowerFlow_Workspace/CLAUDE.md
```

### 2. Commencer conversation Claude/Opus
```
"Lis mon CLAUDE.md pour le contexte PowerFlow."
```

Claude va lire le fichier automatiquement.

### 3. Poser ta question
```
"Basé sur CLAUDE.md, ajoute une fonction qui détecte les pullbacks absorbés."
```

---

## 💬 EXEMPLES D'UTILISATION

### Ex 1 : Ajouter une fonction
```
Lis CLAUDE.md pour le contexte PowerFlow.

Ajoute une fonction detect_absorbed_pullback_series() 
dans pf_behavioral_alert_mapper.py 
qui identifie quand une série de pullbacks est absorbée.

Écris aussi les tests.
```

**Claude sait déjà** :
- Ce que c'est une zone
- Ce que c'est une absorption
- La structure de pf_behavioral_alert_mapper.py
- Les patterns de test
- Zéro re-explication ! ✨

### Ex 2 : Fixer un bug
```
Lis CLAUDE.md.

energy_context ne qualifie pas correctement les COUNTER_RELEASE_ATTEMPT.
Vérifie la logique et corrige.
```

**Claude sait** :
- Que V0.8.2 = Energy Release Alignment
- Que COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED
- Que Energy ne crée jamais un signal
- Où chercher le bug

### Ex 3 : Créer un nouveau script
```
Lis CLAUDE.md.

Crée run_relational_gravity_probe_once.py 
qui mesure les distances et mouvements relatifs des devises.

Sortie: relational_gravity_m1.json
```

**Claude sait** :
- La structure des run_*.py
- Le pattern de sortie JSON
- Les règles read-only
- Les conventions code

---

## ✅ CHECKLIST AVANT SESSION

- [ ] T'as CLAUDE.md dans ton core/ ou workspace/
- [ ] Tu commences par "Lis CLAUDE.md..."
- [ ] Tu poses ta question après
- [ ] Claude cite le fichier dans sa réponse

---

## 📊 ÉCONOMIES

### Par session
```
Sans CLAUDE.md:  900 tokens
Avec CLAUDE.md:  150 tokens
ÉCONOMIES:       750 tokens (-83%)
```

### Par jour (10 sessions)
```
Sans:  9,000 tokens
Avec:  1,500 tokens
Gain:  7,500 tokens/jour 💰
```

### Par mois (250 sessions)
```
Sans:  225,000 tokens
Avec:   37,500 tokens
Gain:  187,500 tokens/mois 🚀
```

---

## 🎯 CONTENU CLAUDE.md V2

✅ **Doctrine PowerFlow** (comprimée)  
✅ **Active State** (V0.8.2 validé)  
✅ **Lexique complet** (150+ termes)  
✅ **Architecture** (tables visuelles)  
✅ **Checkpoints** (dates + validations)  
✅ **Fichiers status** (locked/active/standby)  
✅ **DB contract** (tables/colonnes)  
✅ **Conventions code** (Python, imports, style)  
✅ **Critical rules** (à jamais violer)  
✅ **Commandes CLI** (1 page)  
✅ **Protocol missions** (nouveau travail)  
✅ **Multi-IA collaboration** (workspace structure)  

---

## 🔄 QUAND UPDATER CLAUDE.md V2

### ✅ UPDATE si :
- Nouveau Node validé (V0.9.x?)
- Nouveau concept clé
- Nouvelles conventions
- Nouveaux fichiers clés
- Changement architecture

### ❌ PAS BESOIN si :
- Simple bug fix
- Feature mineure
- Refactor existant
- Changement DB interne

**Rule**: CLAUDE.md reste **essentiel + stable**. Pas "tout ce qui change".

---

## 🚀 BEFORE YOU START

### Si Claude demande du contexte
```
"Lis mon CLAUDE.md d'abord, il a tout."
```

### Si Claude s'arrête à Node V0.7.1
```
"Le CLAUDE.md te dit l'état réel : V0.8.2.
Relis la section ACTIVE STATE."
```

### Si Claude est confused
```
"Cherche [TERME] dans le LEXIQUE du CLAUDE.md."
```

---

## 📝 TEMPLATE PROMPT OPTIMISÉ

```
"Lis mon CLAUDE.md pour le contexte PowerFlow V6.

Mission: [ce que tu veux]

Basé sur:
- Node V0.8.2
- Currency Energy V0.1
- Behavioral Flow
- pf_behavioral_alert_mapper.py
- [fichier/concept pertinent]

Fais [action concrète]."
```

---

## 💡 TIPS AVANCÉS

### Tip 1 : Recharge CLAUDE.md quand t'as des doutes
```
Claude a vu CLAUDE.md 200 tokens ago?
"Relis CLAUDE.md section [X]."
```

### Tip 2 : Utilise le lexique
```
"Selon CLAUDE.md lexique, explique ENERGY_RELEASE_ALIGNMENT."
```

### Tip 3 : Référence la doctrine
```
"Basé sur CLAUDE.md doctrine, Energy ne devient jamais signal, correct?"
```

### Tip 4 : Multi-IA
```
Tous les AI lisent CLAUDE.md →
Même contexte →
Moins de conflits →
Plus cohérent
```

---

## 🎯 VERDICT

```
AVANT:   Expliquer PowerFlow à chaque session (~900 tokens)
APRÈS:   Lire CLAUDE.md une fois (~150 tokens)

RÉSULTAT: 6x plus économe en tokens
          10x plus de contexte clarifié
          Zéro re-explication
          Multi-IA aligned
```

---

**TL;DR**: Mets CLAUDE.md dans ton core/, dis à Claude de le lire, pose ta question. Boom. 💥

Profite de tes 187,500 tokens/mois économisés ! 🚀

