# Message prêt à envoyer à Claude / architecte — T0150 B9 Golden Terrain Cases V1

Branche proposée : `docs/t0150-b9-golden-terrain-cases-v1`

Mission : produire la première bibliothèque de golden terrain cases B9, sans code moteur, sans dashboard, sans Telegram, sans DB write.

Fichiers livrés :

```text
docs/Reports/T0150_B9_GOLDEN_TERRAIN_CASES_V1.md
docs/Reports/T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv
docs/Reports/MESSAGE_CLAUDE_T0150_B9_GOLDEN_TERRAIN_CASES_V1.md
```

Tests passés / à exécuter localement par script :

```powershell
python -m compileall -q .
python -m pytest -q
```

Commande CLI : non applicable. Mission documentaire uniquement.

Résumé :

```text
11 cas golden terrain préparés :
- release UP acceptée ;
- pullback absorbé ;
- rejet haut ;
- failed reintegration ;
- deuxième jambe baissière ;
- zone basse défendue ;
- effort sans résultat ;
- absorption + centre descendant ;
- absorption + centre montant ;
- vague progressive réelle ;
- rebond correctif sans progrès durable.
```

Cas READY_T009_PRECISE prioritaires :

```text
GTC_B9_007 — 2026-05-15 08:00–08:14 — effort sans résultat
GTC_B9_008 — 2026-05-15 11:00–11:31 — absorption + centre descendant
GTC_B9_009 — 2026-05-15 10:00–10:23 — absorption + centre montant
GTC_B9_010 — 2026-05-15 13:38–13:53 — vague progressive réelle
GTC_B9_011 — 2026-05-15 15:48–17:00 — rebond correctif sans progrès durable
```

Limites / blockers :

```text
Les cas 2026-05-06 à 2026-05-14 sont solides comme familles B6 mais doivent être horodatés depuis replay avant automatisation.
Les cas 2026-05-15 restent M1_BAR_PROXY / RECONSTRUCTED : pas de footprint exact, pas de delta brut confirmé.
Le remap horaire shifted doit rester surveillé avant transformation en fixtures.
La vague 13:38–13:53 demande une scène parent, sinon le summarizer risque de la fragmenter.
```

Prochain geste attendu côté architecte :

```text
1. Valider la bibliothèque V1 comme source terrain.
2. Transformer GTC_B9_007 à GTC_B9_011 en fixtures replay read-only.
3. Recaler GTC_B9_001 à GTC_B9_006 sur horaires précis via replay / packets.
4. Ne pas merger automatiquement dans main sans revue.
```

Phrase de verrouillage :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
```
