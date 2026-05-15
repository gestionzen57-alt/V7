# LEXIQUE_MASTER_USAGE_RULES.md

Status: T006_C_USAGE_RULES_READY
Date: 2026-05-15 22:37:49 +02:00
Applies to: Docs/LEXIQUE_MASTER.md
LEXIQUE_MASTER_SHA256: DC4696E565EC9B37AC3D439A852DADB5735F7D1E9FEB398DAEAFBDF91AAB1B2D

## 1. Source status

- Docs/LEXIQUE_MASTER.md is the active consolidated lexique for PowerFlow trader-facing language.
- It is not an exact V767-source fusion.
- It was fused from staged V76/V6 candidate sources.
- The missing AVENANT source was recreated as a candidate and must always be marked as RECREATED_CANDIDATE_NOT_ORIGINAL.

## 2. Mandatory usage

Use LEXIQUE_MASTER.md when producing or auditing:

- trader-facing PowerFlow language
- packet summaries
- film descriptions
- terrain descriptions
- requalification wording
- data-limit wording
- anti-signal / anti-certainty wording

## 3. Non-negotiable language constraints

- PowerFlow reads market structure; it does not issue guaranteed trading signals.
- PowerFlow qualifies perception; the trader decides.
- Always separate observation, qualification, hypothesis, confirmation, invalidation, data limits, and trader decision.
- Never phrase PowerFlow output as automatic buy/sell instruction.
- Never use certainty language such as guaranteed, 100%, certain, or infallible.

## 4. Required output contract

Any trader-facing packet should expose these fields when available:

- Film
- Dernier evenement structurel
- Zone active
- Role du mouvement
- Coalitions / antagonistes
- Gravite
- Qualite packet
- Confirmation prix
- Invalidation
- Limites donnees

## 5. GBPUSD and multidevise boundary

- GBPUSD remains the primary trading surface.
- M1 tickvolume/sec remains GBPUSD-only unless explicitly expanded.
- Multidevise context is used for coalitions, antagonists, gravity, and tempo.
- Multidevise context is not a direct trade trigger.
- B8 remains incomplete as a full multicurrency brick until currency-specific tempo is modeled.

## 6. Audit requirements

Future edits to LEXIQUE_MASTER.md must preserve:

- source mode marker
- AVENANT recreated-candidate marker
- provenance section
- fused source corpus or explicit replacement provenance
- trader-facing output contract
- anti-signal language doctrine

## 7. Operational rule

If a future exact V767 source is recovered, do not silently overwrite LEXIQUE_MASTER.md. Create a new audit checkpoint comparing recovered V767 source against the current staged-candidate master.