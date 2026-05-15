# CHECKPOINT - T004-G live capture health counter

Date: 2026-05-15T19:29:20.0487751+02:00
Focus: T004-G live capture health counter

## Result

- Live capture health counter created and executed.
- Runtime unchanged.
- DB read-only.
- Dashboard workspace files intentionally left untouched.

## Current git log

```text
eb06eae audit(t004): add live capture health counter for USDJPY
a77195d docs(scheduler): add Telegram safety and surface routing audit
4327a79 [CHECKPOINT] Targeted checkpoint: T004-F capture symbol routing
6adf651 audit(t004): inspect capture symbol routing for USDJPY thin data
78aa872 [CHECKPOINT] Targeted checkpoint: T004-F capture symbol routing
f7a045c audit(t004): inspect capture symbol routing for USDJPY thin data
c0d3aee fix(scheduler): default V7.6 telegram cycle to dry-run
```

## Next step

Use the health counter status to decide whether to fix source routing or rerun during active feed.

