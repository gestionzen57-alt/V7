# Rapport — Contrat B9 ↔ Temporalité

**Branche cible :** `docs/b9-temporality-contract`  
**Commit proposé :** `docs(t009): add B9 temporality contract`  
**Type :** documentation + tests documentaires  
**Runtime impact :** aucun  

---

## 1. Résumé mission

La mission crée un contrat documentaire et testable entre B9 Sequence Summarizer et la brique Temporalité.

B9 reste responsable de la scène locale :

```text
moment_type, parent_scene, zone_memory, effort_role, retest_status,
memory_state, source_profile, proxy_vs_raw_verdict, raw_coverage
```

Temporalité ne répète pas B9. Elle qualifie la maturité temporelle :

```text
WINDOW_YOUNG, WINDOW_ACTIVE, WINDOW_LATE, WINDOW_CLOSED
BIRTH, REACTION, DIGESTION, RETEST, SECOND_LEG, ABSORPTION, EXHAUSTION
WATCH_RETEST, WATCH_SECOND_LEG, WATCH_ABSORPTION, WATCH_INVALIDATION, HONEST_UNKNOWN
```

Phrase de cap retenue :

```text
B9 dit ce qui s’imprime dans la scène.
La Temporalité dit si cette scène est jeune, active, tardive ou consommée.
```

---

## 2. Fichiers livrés

```text
Core/docs/Contracts/B9_TEMPORALITY_CONTRACT.md
Core/docs/Reports/B9_TEMPORALITY_CONTRACT_REPORT.md
Core/tests/test_b9_temporality_contract_docs.py
```

---

## 3. Décisions de contrat

### 3.1 Séparation B9 / Temporalité

B9 fournit les preuves locales. Temporalité produit seulement :

```json
{
  "temporal_phase": "WINDOW_YOUNG | WINDOW_ACTIVE | WINDOW_LATE | WINDOW_CLOSED",
  "temporal_role": "BIRTH | REACTION | DIGESTION | RETEST | SECOND_LEG | ABSORPTION | EXHAUSTION",
  "watch_state": "WATCH_RETEST | WATCH_SECOND_LEG | WATCH_ABSORPTION | WATCH_INVALIDATION | HONEST_UNKNOWN",
  "phase_confidence": 0.0,
  "why_fr": "...",
  "limits": []
}
```

### 3.2 Source-aware / raw coverage

Le contrat impose :

```text
B9 confirmé raw peut renforcer la confiance.
B9 raw unavailable réduit ou cape la confiance.
M1_BAR_PROXY garde un langage prudent : probable, reconstruit, inféré, partiel.
```

### 3.3 Requalifications temporelles clés

```text
Vague progressive tardive -> WINDOW_LATE / WATCH_SECOND_LEG, pas naissance fraîche.
Effort sans résultat + mémoire active -> WATCH_ABSORPTION ou WATCH_RETEST.
Retest échoué -> peut fermer la fenêtre précédente.
Projection decay -> WINDOW_LATE ou WINDOW_CLOSED / WATCH_INVALIDATION.
Preuve contradictoire -> HONEST_UNKNOWN.
```

---

## 4. Tests documentaires ajoutés

Le fichier `Core/tests/test_b9_temporality_contract_docs.py` vérifie :

```text
présence WINDOW_YOUNG / WINDOW_ACTIVE / WINDOW_LATE / WINDOW_CLOSED
présence WATCH_SECOND_LEG / WATCH_ABSORPTION
présence raw_coverage / proxy_vs_raw_verdict
interdiction de langage décisionnel hors section Interdits
séparation claire B9 vs Temporalité
présence des livrables attendus
```

---

## 5. Commandes de validation

Depuis la racine du repo :

```powershell
python -m py_compile Core\tests\test_b9_temporality_contract_docs.py
python -m pytest Core\tests\test_b9_temporality_contract_docs.py -q
```

Si la racine locale est déjà `Core`, les scripts d’installation/Git fournis adaptent automatiquement les chemins :

```powershell
python -m py_compile tests\test_b9_temporality_contract_docs.py
python -m pytest tests\test_b9_temporality_contract_docs.py -q
```

---

## 6. Limites

```text
Pas de code runtime Temporalité ajouté.
Pas de modification de B9 Sequence Summarizer.
Pas de DB write.
Pas de Telegram.
Pas de dashboard mutation.
Pas de fusion B8.
Pas de validation sur données live.
```

---

## 7. Prochain geste architecte

Valider le contrat documentaire, puis décider si la prochaine tâche doit créer une fonction pure de mapping :

```text
pf_b9_temporality_contract.py
map_b9_to_temporality_phase(b9_payload) -> temporal_payload
```

Cette fonction devra rester read-only, sans dépendance dashboard/Telegram, et testée avec fixtures B9 V3.1.
