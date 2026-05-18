# T0174 — T0169 Import Path Hotfix V0

## Résumé

T0174 formalise le correctif du bug T0169 où le builder lancé depuis `tools/` ne trouvait pas le module racine `pf_t009_reality_board_surface_adapter_candidate.py`.

Le correctif ajoute la racine du repo dans `sys.path` avant l'import du module racine.

## États possibles

- `PATCH_APPLIED`
- `ALREADY_PATCHED`
- `PATCH_AVAILABLE_NOT_APPLIED`
- `BLOCKED_T0169_BUILDER_NOT_FOUND`

## Doctrine

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ce hotfix corrige un contrat d'import CLI ; il ne déclenche aucune action live.

## Limites

- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun cockpit live.
- Aucun Telegram.
- Aucun ordre directionnel.
- Aucun taux de réussite.
