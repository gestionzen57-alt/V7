from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_cockpit_utf8_v74e")
backup.write_text(text, encoding="utf-8")

# 1) Ajouter helpers recursiveFind + repairMojibake après esc()
needle = '''function esc(v) {
  return String(safe(v, "")).replace(/[&<>"']/g, m => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[m]));
}
'''

insert = '''function esc(v) {
  return String(repairMojibake(safe(v, ""))).replace(/[&<>"']/g, m => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[m]));
}

function repairMojibake(v) {
  let s = String(v ?? "");
  const map = {
    "Ã©": "é",
    "Ã¨": "è",
    "Ãª": "ê",
    "Ã«": "ë",
    "Ã ": "à",
    "Ã¢": "â",
    "Ã´": "ô",
    "Ã¹": "ù",
    "Ã»": "û",
    "Ã§": "ç",
    "Ã®": "î",
    "Ã¯": "ï",
    "â€™": "'",
    "â€œ": "“",
    "â€": "”",
    "â€“": "–",
    "â€”": "—",
    "Â°": "°",
    "Â": ""
  };
  for (const [bad, good] of Object.entries(map)) {
    s = s.split(bad).join(good);
  }
  return s;
}

function recursiveFind(obj, keys) {
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

if needle not in text:
    raise SystemExit("PATCH_FAIL | esc() block not found")

text = text.replace(needle, insert, 1)

# 2) Durcir renderHero cockpit state nested
old = '''      <div class="k">État cockpit</div><div class="v">${esc(cockpit.state || cockpit.etat || cockpit.synthesis)}</div>'''
new = '''      <div class="k">État cockpit</div><div class="v">${esc(recursiveFind(cockpit, ["state", "etat", "main_state", "market_state", "synthesis"]) || "MISSING_FIELD")}</div>'''

if old not in text:
    raise SystemExit("PATCH_FAIL | hero cockpit state line not found")

text = text.replace(old, new, 1)

# 3) Remplacer renderCockpit complet
start = text.find("function renderCockpit(cockpit) {")
if start == -1:
    raise SystemExit("PATCH_FAIL | renderCockpit start not found")

end = text.find("\nasync function main()", start)
if end == -1:
    raise SystemExit("PATCH_FAIL | renderCockpit end not found")

new_render = r'''function renderCockpit(cockpit) {
  const action = recursiveFind(cockpit, ["action", "attention", "status", "decision"]) || "MISSING_FIELD";
  const state = recursiveFind(cockpit, ["state", "etat", "main_state", "market_state"]) || "MISSING_FIELD";
  const reading = recursiveFind(cockpit, ["reading", "synthesis", "multiread_synthesis", "reading_type"]) || "MISSING_FIELD";

  const scenarios =
    recursiveFind(cockpit, ["scenarios", "watch_scenarios"]) ||
    recursiveFind(cockpit, ["scenario_lines"]) ||
    [];

  const risks =
    recursiveFind(cockpit, ["risks", "technical_risks", "useful_risks"]) ||
    [];

  const normalizedScenarios = Array.isArray(scenarios)
    ? scenarios
    : String(scenarios || "").split("|").map(x => x.trim()).filter(Boolean);

  const normalizedRisks = Array.isArray(risks)
    ? risks
    : String(risks || "").split("|").map(x => x.trim()).filter(Boolean);

  document.getElementById("cockpit").innerHTML = `
    <h2>Cockpit source</h2>
    <div class="kv">
      <div class="k">Action</div><div class="v">${esc(action)}</div>
      <div class="k">State</div><div class="v">${esc(state)}</div>
      <div class="k">Reading</div><div class="v">${esc(reading)}</div>
    </div>
    <h3>Scénarios</h3>
    <ul>${normalizedScenarios.map(x => `<li>${esc(x)}</li>`).join("") || "<li class='muted'>MISSING_FIELD: cockpit.scenarios</li>"}</ul>
    <h3>Risques cockpit</h3>
    <ul>${normalizedRisks.map(x => `<li>${esc(x)}</li>`).join("") || "<li class='muted'>Aucun risque cockpit direct.</li>"}</ul>
  `;
}
'''

text = text[:start] + new_render + text[end:]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.4e cockpit recursive rendering + mojibake repair | backup={backup.name}")
