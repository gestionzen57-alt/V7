from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75c_session_compact")
backup.write_text(text, encoding="utf-8")

# CSS compact session memory
css = r'''
<style id="pf75c-session-compact-style">
.session-memory-card details {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.35);
}
.session-memory-card summary {
  cursor: pointer;
  font-weight: 800;
  letter-spacing: .05em;
  color: #dbeafe;
}
.session-memory-card .mini-note {
  color: #94a3b8;
  font-size: 12px;
  margin-left: 8px;
}
.session-memory-card table {
  margin-top: 10px;
}
.session-memory-card .review-line {
  margin-top: 8px;
  color: #94a3b8;
  font-size: 12px;
}
</style>
'''

if "pf75c-session-compact-style" not in text:
    text = text.replace("</head>", css + "\n</head>", 1)

# Replace function pf75ProfileMemory body in a robust way
start = text.find("function pf75ProfileMemory(name, mem) {")
if start == -1:
    raise SystemExit("PATCH_FAIL | pf75ProfileMemory not found")

# Find matching function end by next function marker
next_marker = text.find("\nasync function renderSessionMemory", start)
if next_marker == -1:
    raise SystemExit("PATCH_FAIL | renderSessionMemory marker not found")

new_fn = r'''function pf75ProfileMemory(name, mem) {
  const events = pf75Events(mem);
  const total = pf75Find(mem, ["events_total"]) ?? events.length;
  const updated = pf75Find(mem, ["updated_utc", "timestamp_utc", "last_update_utc"]) || "";
  const visible = events.slice(0, 3);
  const hidden = events.length > 3 ? events.slice(3) : [];

  function row(e) {
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
  }

  const visibleRows = visible.map(row).join("");
  const hiddenRows = hidden.map(row).join("");

  return `
    <details class="profile-memory" ${name === "LTF" ? "open" : ""}>
      <summary>
        ${pf75Esc(name)} Session Memory
        <span class="mini-note">events=${pf75Esc(total)} · updated=${pf75Esc(updated)} · visible=${visible.length}/${events.length}</span>
      </summary>

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
          ${visibleRows || `<tr><td colspan="7" class="muted">Aucun moment marquant en mémoire.</td></tr>`}
          ${hiddenRows ? `<tr><td colspan="7" class="muted">— événements plus anciens —</td></tr>${hiddenRows}` : ""}
        </tbody>
      </table>

      <div class="review-line">
        Revue trader prête : Ce que j'ai vu · Ce que j'ai ressenti · Ce que PowerFlow a vu avant moi · Ce que PowerFlow a raté · Leçon
      </div>
    </details>
  `;
}
'''

text = text[:start] + new_fn + text[next_marker:]

# Make parent card identifiable
text = text.replace(
    '<section class="card wide" id="sessionMemory"></section>',
    '<section class="card wide session-memory-card" id="sessionMemory"></section>'
)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5c compact session memory | backup={backup.name}")
