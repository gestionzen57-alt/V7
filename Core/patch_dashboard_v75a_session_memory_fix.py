from pathlib import Path
import re

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_session_memory_fix_v75a")
backup.write_text(text, encoding="utf-8")

# 1) Add HTML container before cockpit section, or near end if marker changed
if 'id="sessionMemory"' not in text:
    m = re.search(r'(<section[^>]+id=["\']cockpit["\'][^>]*></section>)', text)
    if m:
        text = text[:m.start()] + '  <section class="card wide" id="sessionMemory"></section>\n\n' + text[m.start():]
    elif "</main>" in text:
        text = text.replace("</main>", '  <section class="card wide" id="sessionMemory"></section>\n</main>', 1)
    else:
        text = text.replace("</body>", '  <section class="card wide" id="sessionMemory"></section>\n</body>', 1)

# 2) Add autonomous JS renderer before final script close
if "function renderSessionMemory(" not in text:
    js = r'''
async function pf75LoadJson(path) {
  try {
    const r = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
    if (!r.ok) return null;
    return await r.json();
  } catch (e) {
    return null;
  }
}

function pf75Esc(v) {
  if (v === null || v === undefined) return "";
  if (typeof v === "object") {
    try {
      if (v.label) return String(v.label);
      if (v.message) return String(v.message);
      return JSON.stringify(v);
    } catch (e) {
      return "";
    }
  }
  return String(v)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function pf75Find(obj, keys) {
  if (!obj || typeof obj !== "object") return null;
  const wanted = new Set(keys);
  const stack = [obj];

  while (stack.length) {
    const cur = stack.pop();
    if (!cur || typeof cur !== "object") continue;

    for (const [k, v] of Object.entries(cur)) {
      if (wanted.has(k)) return v;
      if (v && typeof v === "object") stack.push(v);
    }
  }
  return null;
}

function pf75Events(mem) {
  const candidates = [
    pf75Find(mem, ["last_events"]),
    pf75Find(mem, ["events"]),
    pf75Find(mem, ["recent_important_events"])
  ];

  for (const c of candidates) {
    if (Array.isArray(c)) return c.slice(-8).reverse();
  }
  return [];
}

function pf75ReviewBlock(mem) {
  const review = pf75Find(mem, ["trader_review", "review", "revue_trader"]) || {};
  const fields = [
    ["Ce que j'ai vu", "what_i_saw"],
    ["Ce que j'ai ressenti", "what_i_felt"],
    ["Ce que PowerFlow a vu avant moi", "what_powerflow_saw_before_me"],
    ["Ce que PowerFlow a raté", "what_powerflow_missed"],
    ["Leçon", "lesson"]
  ];

  return `
    <div class="muted" style="margin-top:10px">
      <b>Revue trader prête :</b>
      ${fields.map(([label, key]) => `<span class="pill">${pf75Esc(label)}${review[key] ? " ✓" : ""}</span>`).join(" ")}
    </div>
  `;
}

function pf75ProfileMemory(name, mem) {
  const events = pf75Events(mem);
  const total = pf75Find(mem, ["events_total"]) ?? events.length;
  const updated = pf75Find(mem, ["updated_utc", "timestamp_utc", "last_update_utc"]) || "";

  const rows = events.map(e => {
    const ts = e.timestamp_broker || e.timestamp_local_reference || e.timestamp_utc || "";
    const tf = e.timeframe || "";
    const event = e.event_type || e.important_event || "";
    const phase = e.phase_after || e.phase || e.tf_phase || "";
    const bias = e.bias || e.dominant_bias || "";
    const price = e.price ?? e.last_close ?? "";
    const phrase = e.machine_phrase || e.cockpit_phrase || "";

    return `
      <tr>
        <td><b>${pf75Esc(tf)}</b></td>
        <td>${pf75Esc(event)}</td>
        <td>${pf75Esc(phase)}</td>
        <td>${pf75Esc(bias)}</td>
        <td>${pf75Esc(price)}</td>
        <td>${pf75Esc(ts)}</td>
        <td class="muted">${pf75Esc(phrase)}</td>
      </tr>
    `;
  }).join("");

  return `
    <div class="profile-memory" style="margin-top:14px">
      <h3>${pf75Esc(name)} Session Memory <span class="muted">events=${pf75Esc(total)} updated=${pf75Esc(updated)}</span></h3>
      <table>
        <thead>
          <tr>
            <th>TF</th>
            <th>Event</th>
            <th>Phase</th>
            <th>Bias</th>
            <th>Prix</th>
            <th>Temps</th>
            <th>Machine</th>
          </tr>
        </thead>
        <tbody>
          ${rows || `<tr><td colspan="7" class="muted">Aucun moment marquant en mémoire.</td></tr>`}
        </tbody>
      </table>
      ${pf75ReviewBlock(mem)}
    </div>
  `;
}

async function renderSessionMemory() {
  const el = document.getElementById("sessionMemory");
  if (!el) return;

  const paths = [
    ["LTF", "output/dashboard_surface/GBPUSD/ltf_session_memory.json"],
    ["MTF", "output/dashboard_surface/GBPUSD/mtf_session_memory.json"],
    ["HTF", "output/dashboard_surface/GBPUSD/htf_session_memory.json"]
  ];

  const loaded = await Promise.all(paths.map(async ([name, path]) => [name, await pf75LoadJson(path)]));

  el.innerHTML = `
    <h2>Session Memory</h2>
    <p class="muted">Film de session conservé pour comparaison trader / machine.</p>
    ${loaded.map(([name, mem]) => pf75ProfileMemory(name, mem || {})).join("")}
  `;
}

setTimeout(() => {
  try { renderSessionMemory(); } catch (e) { console.error("session memory render failed", e); }
}, 800);
'''

    idx = text.rfind("</script>")
    if idx == -1:
        raise SystemExit("PATCH_FAIL | no script close marker found")
    text = text[:idx] + js + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5a session memory panel active | backup={backup.name}")
