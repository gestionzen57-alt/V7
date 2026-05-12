from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_session_memory_v75a")
backup.write_text(text, encoding="utf-8")

# 1) Ajouter chargement des mémoires session dans main()
old = '''    const [
      cockpit,
      evidenceBus,
      evidenceReading,
      timeProfiles,
      phaseSynthesis,
      b8,
      dataHealth,
      contract
    ] = await Promise.all([
      loadJson("output/dashboard_surface/trader_cockpit.json"),
      loadJson("output/dashboard_surface/evidence_bus.json"),
      loadJson("output/dashboard_surface/evidence_reading.json"),
      loadJson("output/dashboard_surface/time_profiles_dashboard.json"),
      loadJson("output/dashboard_surface/phase_synthesis.json"),
      loadJson("output/dashboard_surface/b8_cross_surface.json"),
      loadJson("output/dashboard_surface/data_health.json"),
      loadJson("output/dashboard_surface/dashboard_v74_contract_check.json")
    ]);
'''

new = '''    const [
      cockpit,
      evidenceBus,
      evidenceReading,
      timeProfiles,
      phaseSynthesis,
      b8,
      dataHealth,
      contract,
      ltfMemory,
      mtfMemory,
      htfMemory
    ] = await Promise.all([
      loadJson("output/dashboard_surface/trader_cockpit.json"),
      loadJson("output/dashboard_surface/evidence_bus.json"),
      loadJson("output/dashboard_surface/evidence_reading.json"),
      loadJson("output/dashboard_surface/time_profiles_dashboard.json"),
      loadJson("output/dashboard_surface/phase_synthesis.json"),
      loadJson("output/dashboard_surface/b8_cross_surface.json"),
      loadJson("output/dashboard_surface/data_health.json"),
      loadJson("output/dashboard_surface/dashboard_v74_contract_check.json"),
      loadJson("output/dashboard_surface/GBPUSD/ltf_session_memory.json"),
      loadJson("output/dashboard_surface/GBPUSD/mtf_session_memory.json"),
      loadJson("output/dashboard_surface/GBPUSD/htf_session_memory.json")
    ]);
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | main Promise.all block not found")

text = text.replace(old, new, 1)

# 2) Ajouter appel renderSessionMemory()
old_call = '''    renderEvidenceBus(evidenceBus);
    renderRisks(evidenceBus, evidenceReading, dataHealth);
    renderCockpit(cockpit);
'''

new_call = '''    renderEvidenceBus(evidenceBus);
    renderRisks(evidenceBus, evidenceReading, dataHealth);
    renderSessionMemory(ltfMemory, mtfMemory, htfMemory);
    renderCockpit(cockpit);
'''

if old_call not in text:
    raise SystemExit("PATCH_FAIL | render call block not found")

text = text.replace(old_call, new_call, 1)

# 3) Ajouter container HTML avant Cockpit Source
old_html = '''  <section class="card wide" id="cockpit"></section>
'''

new_html = '''  <section class="card wide" id="sessionMemory"></section>

  <section class="card wide" id="cockpit"></section>
'''

if old_html not in text:
    raise SystemExit("PATCH_FAIL | cockpit section not found")

text = text.replace(old_html, new_html, 1)

# 4) Ajouter fonction renderSessionMemory avant renderCockpit
marker = "function renderCockpit(cockpit) {"
if marker not in text:
    raise SystemExit("PATCH_FAIL | renderCockpit marker not found")

fn = r'''
function renderSessionMemory(ltf, mtf, htf) {
  const profiles = [
    ["LTF", ltf],
    ["MTF", mtf],
    ["HTF", htf]
  ];

  function eventsOf(mem) {
    const ev =
      recursiveFind(mem, ["last_events"]) ||
      recursiveFind(mem, ["events"]) ||
      recursiveFind(mem, ["recent_important_events"]) ||
      [];
    return Array.isArray(ev) ? ev.slice(-6).reverse() : [];
  }

  function profileBlock(name, mem) {
    const events = eventsOf(mem);
    const total = recursiveFind(mem, ["events_total"]) ?? events.length;
    const updated = recursiveFind(mem, ["updated_utc", "timestamp_utc", "last_update_utc"]) || "";

    const rows = events.map(e => {
      const ts = e.timestamp_broker || e.timestamp_local_reference || e.timestamp_utc || "";
      const tf = e.timeframe || "";
      const event = e.event_type || e.important_event || "";
      const phase = e.phase_after || e.phase || e.tf_phase || "";
      const bias = e.bias || e.dominant_bias || "";
      const price = e.price ?? e.last_close ?? "";
      const phrase = e.machine_phrase || recursiveFind(e, ["machine_phrase", "cockpit_phrase"]) || "";

      return `
        <tr>
          <td><b>${esc(tf)}</b></td>
          <td>${esc(event)}</td>
          <td>${esc(phase)}</td>
          <td>${esc(bias)}</td>
          <td>${esc(price)}</td>
          <td>${esc(ts)}</td>
          <td class="muted">${esc(phrase)}</td>
        </tr>
      `;
    }).join("");

    return `
      <div class="profile-memory">
        <h3>${esc(name)} Session Memory <span class="muted">events=${esc(total)} updated=${esc(updated)}</span></h3>
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
      </div>
    `;
  }

  document.getElementById("sessionMemory").innerHTML = `
    <h2>Session Memory</h2>
    <p class="muted">Film de session conservé pour comparaison trader / machine.</p>
    ${profiles.map(([name, mem]) => profileBlock(name, mem)).join("")}
    <div class="review-grid">
      <div><h3>Revue trader</h3></div>
      <div class="muted">Ce que j'ai vu · Ce que j'ai ressenti · Ce que PowerFlow a vu avant moi · Ce que PowerFlow a raté · Leçon</div>
    </div>
  `;
}

'''

text = text.replace(marker, fn + marker, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5a session memory panel added | backup={backup.name}")
