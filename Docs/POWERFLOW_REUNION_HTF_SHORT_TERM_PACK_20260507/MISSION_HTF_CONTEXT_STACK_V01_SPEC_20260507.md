# MISSION — HTF CONTEXT STACK V0.1 SPEC

Objectif :
Préparer une spec pour intégrer W/D/H4/H1 comme contexte primaire de PowerFlow.

---

# Questions à résoudre

```text
1. Où est la gravité Weekly ?
2. Où est la mémoire Daily ?
3. H4 autorise-t-il ou contredit-il la lecture tactique ?
4. H1 traduit-il une phase intraday exploitable ?
5. M15/M5/M1 commencent-ils à rattraper le retard HTF ?
```

---

# Sortie cible future

```json
"htf_context_stack": {
  "weekly": {},
  "daily": {},
  "h4": {},
  "h1": {},
  "state": "HTF_DELAYED_WINDOW_ACTIVE",
  "lag_state": "LTF_CATCHUP_BEGINNING",
  "gravity_bias": "...",
  "quality": "OK/PARTIAL/MIXED",
  "next_watch": []
}
```

---

# Règle

```text
HTF_CONTEXT_STACK doit informer le cockpit.
Il ne doit pas produire de BUY/SELL.
```
