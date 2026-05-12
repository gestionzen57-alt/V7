from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_risk_objects_v74f")
backup.write_text(text, encoding="utf-8")

needle = '''function recursiveFind(obj, keys) {
  if (!obj || typeof obj !== "object") return null;

  if (Array.isArray(obj)) {
    for (const item of obj) {
      const found = recursiveFind(item, keys);
      if (found !== null && found !== undefined && found !== "") return found;
    }
    return null;
  }

  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const v = obj[key];
      if (v !== null && v !== undefined && v !== "") return v;
    }
  }

  for (const v of Object.values(obj)) {
    const found = recursiveFind(v, keys);
    if (found !== null && found !== undefined && found !== "") return found;
  }

  return null;
}
'''

insert = '''function recursiveFind(obj, keys) {
  if (!obj || typeof obj !== "object") return null;

  if (Array.isArray(obj)) {
    for (const item of obj) {
      const found = recursiveFind(item, keys);
      if (found !== null && found !== undefined && found !== "") return found;
    }
    return null;
  }

  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const v = obj[key];
      if (v !== null && v !== undefined && v !== "") return v;
    }
  }

  for (const v of Object.values(obj)) {
    const found = recursiveFind(v, keys);
    if (found !== null && found !== undefined && found !== "") return found;
  }

  return null;
}

function humanizeValue(v) {
  if (v === null || v === undefined || v === "") return "MISSING_FIELD";

  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
    return String(v);
  }

  if (Array.isArray(v)) {
    return v.map(humanizeValue).filter(Boolean).join(" | ");
  }

  if (typeof v === "object") {
    const priority = [
      "risk",
      "code",
      "label",
      "name",
      "type",
      "message",
      "detail",
      "reason",
      "status",
      "field",
      "source"
    ];

    const parts = [];
    for (const k of priority) {
      if (v[k] !== null && v[k] !== undefined && v[k] !== "") {
        parts.push(`${k}=${humanizeValue(v[k])}`);
      }
    }

    if (parts.length) return parts.join(" | ");

    return Object.entries(v)
      .filter(([_, val]) => val !== null && val !== undefined && val !== "")
      .map(([k, val]) => `${k}=${humanizeValue(val)}`)
      .join(" | ") || "EMPTY_OBJECT";
  }

  return String(v);
}

function normalizeList(v) {
  if (v === null || v === undefined || v === "") return [];

  if (Array.isArray(v)) {
    return v.map(humanizeValue).filter(x => x && x !== "EMPTY_OBJECT");
  }

  if (typeof v === "object") {
    return [humanizeValue(v)].filter(Boolean);
  }

  return String(v || "")
    .split("|")
    .map(x => x.trim())
    .filter(Boolean);
}
'''

if needle not in text:
    raise SystemExit("PATCH_FAIL | recursiveFind block not found")

text = text.replace(needle, insert, 1)

old = '''  const normalizedScenarios = Array.isArray(scenarios)
    ? scenarios
    : String(scenarios || "").split("|").map(x => x.trim()).filter(Boolean);

  const normalizedRisks = Array.isArray(risks)
    ? risks
    : String(risks || "").split("|").map(x => x.trim()).filter(Boolean);
'''

new = '''  const normalizedScenarios = normalizeList(scenarios);
  const normalizedRisks = normalizeList(risks);
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | normalizedScenarios block not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.4f risk objects humanized | backup={backup.name}")
