from __future__ import annotations

import inspect
import json
import pf_currency_energy_probe as mod


def is_public_callable(name: str, obj) -> bool:
    if name.startswith("_"):
        return False
    if inspect.ismodule(obj):
        return False
    return callable(obj)


def main() -> int:
    public_callables = []

    for name in sorted(dir(mod)):
        obj = getattr(mod, name)
        if not is_public_callable(name, obj):
            continue

        try:
            sig = str(inspect.signature(obj))
        except Exception:
            sig = "(signature unavailable)"

        doc = inspect.getdoc(obj) or ""
        doc_first = doc.splitlines()[0] if doc else ""

        public_callables.append({
            "name": name,
            "signature": sig,
            "doc": doc_first,
            "type": type(obj).__name__,
        })

    print("CURRENCY_ENERGY_API_RECO_OK")
    print(json.dumps(public_callables, ensure_ascii=False, indent=2))

    likely = [
        item for item in public_callables
        if any(k in item["name"].lower() for k in [
            "build",
            "compute",
            "energy",
            "probe",
            "analyze",
            "run",
            "state",
        ])
    ]

    print("\nLIKELY_REUSABLE_API:")
    print(json.dumps(likely, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())