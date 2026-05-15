# T006-D - CLAUDE.md Lexique Master binding

Date: 
2026-05-15 22:55:34 +02:00
Mission: wire LEXIQUE_MASTER usage rules into Docs/CLAUDE.md
Status: T006_D_CLAUDE_BINDING_READY

## Updated file

- Docs/CLAUDE.md
- SHA256=
7B508C29DE970ADC2AE214BD1DCFDFB32BE476828E387D07838C98AA63CC32C3

## Canonical references

- Docs/LEXIQUE_MASTER.md
- LEXIQUE_MASTER_SHA256=
DC4696E565EC9B37AC3D439A852DADB5735F7D1E9FEB398DAEAFBDF91AAB1B2D
- Docs/LEXIQUE_MASTER_USAGE_RULES.md
- LEXIQUE_MASTER_USAGE_RULES_SHA256=
BD830D96A529870A4F6C8229A554EA211A9D7AEA0E2153C7043925AB55ABEA54

## Bound doctrine

- PowerFlow reads market structure; it does not issue guaranteed trading signals.
- PowerFlow qualifies perception; the trader decides.
- Trader-facing language must follow LEXIQUE_MASTER and usage rules.
- Required packet fields are now listed in CLAUDE.md.
- Source status warning is preserved: AVENANT is recreated candidate, not original V767.

## Operational conclusion

- CLAUDE.md now references the active lexique master and usage rules.
- No code, DB, scheduler, dashboard, or runtime file was intentionally modified.