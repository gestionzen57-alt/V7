from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_autorefresh_v74d")
backup.write_text(text, encoding="utf-8")

# 1) Ajouter source contract check
old_sources = '''  dataHealth: "output/dashboard_surface/data_health.json"
};'''

new_sources = '''  dataHealth: "output/dashboard_surface/data_health.json",
  contract: "output/dashboard_surface/dashboard_v74_contract_check.json"
};'''

if old_sources not in text:
    raise SystemExit("PATCH_FAIL | SOURCES block not found")
text = text.replace(old_sources, new_sources, 1)

# 2) Ajouter style statusbar
old_style = '''    .footer {
      color: var(--muted);
      font-size: 12px;
      padding: 10px 0 30px;
      text-align: center;
    }'''

new_style = '''    .statusbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }

    .pulse {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 12px rgba(47,209,124,.8);
      display: inline-block;
    }

    .footer {
      color: var(--muted);
      font-size: 12px;
      padding: 10px 0 30px;
      text-align: center;
    }'''

if old_style not in text:
    raise SystemExit("PATCH_FAIL | footer style block not found")
text = text.replace(old_style, new_style, 1)

# 3) Ajouter fonctions de fraîcheur avant renderHero
needle = '''function renderHero(reading, bus, cockpit) {'''

insert = '''function parseTime(v) {
  if (!v) return null;
  const t = Date.parse(v);
  if (Number.isNaN(t)) return null;
  return t;
}

function newestTimestamp(...objects) {
  let best = null;
  for (const obj of objects) {
    if (!obj || typeof obj !== "object") continue;
    const candidates = [
      obj.timestamp_utc,
      obj.updated_utc,
      obj.created_utc,
      obj.last_update_utc,
      obj.generated_utc
    ];
    for (const c of candidates) {
      const t = parseTime(c);
      if (t !== null && (best === null || t > best)) best = t;
    }
  }
  return best;
}

function ageSeconds(ts) {
  if (ts === null) return null;
  return Math.max(0, Math.round((Date.now() - ts) / 1000));
}

function freshnessLabel(age, healthStatus) {
  const hs = String(healthStatus || "").toUpperCase();
  if (hs.includes("STALE")) return hs;
  if (age === null) return "UNKNOWN_FRESHNESS";
  if (age <= 30) return "FRESH";
  if (age <= 180) return "WARM";
  return "STALE_VIEW";
}

function renderStatusBar(contract, health, latestTs, age) {
  const contractStatus = safe(contract.status, "UNKNOWN");
  const healthStatus = safe(health.global_status || health.status, "UNKNOWN");
  const freshness = freshnessLabel(age, healthStatus);
  const latestIso = latestTs ? new Date(latestTs).toISOString() : "UNKNOWN";

  return `
    <div class="statusbar">
      <span class="badge ok"><span class="pulse"></span>AUTO REFRESH 10s</span>
      <span class="badge ${badgeClass(contractStatus)}">CONTRACT=${esc(contractStatus)}</span>
      <span class="badge ${badgeClass(healthStatus)}">DATA_HEALTH=${esc(healthStatus)}</span>
      <span class="badge ${badgeClass(freshness)}">FRESHNESS=${esc(freshness)}</span>
      <span class="badge">AGE=${esc(age === null ? "UNKNOWN" : age + "s")}</span>
      <span class="badge mono">LAST=${esc(latestIso)}</span>
    </div>
  `;
}

'''

if needle not in text:
    raise SystemExit("PATCH_FAIL | renderHero not found")
text = text.replace(needle, insert + needle, 1)

# 4) Modifier signature renderHero
old_sig = '''function renderHero(reading, bus, cockpit) {'''
new_sig = '''function renderHero(reading, bus, cockpit, contract, health, latestTs, age) {'''
text = text.replace(old_sig, new_sig, 1)

# 5) Ajouter statusbar dans hero
old_hero_tail = '''    <div class="kv">
      <div class="k">État cockpit</div><div class="v">${esc(cockpit.state || cockpit.etat || cockpit.synthesis)}</div>
      <div class="k">Confiance</div><div class="v">${esc(reading.confidence || bus.confidence)}</div>
      <div class="k">Dernière mise à jour</div><div class="v mono">${esc(bus.timestamp_utc || reading.timestamp_utc || cockpit.timestamp_utc)}</div>
    </div>
  `;'''

new_hero_tail = '''    <div class="kv">
      <div class="k">État cockpit</div><div class="v">${esc(cockpit.state || cockpit.etat || cockpit.synthesis)}</div>
      <div class="k">Confiance</div><div class="v">${esc(reading.confidence || bus.confidence)}</div>
      <div class="k">Dernière mise à jour</div><div class="v mono">${esc(bus.timestamp_utc || reading.timestamp_utc || cockpit.timestamp_utc)}</div>
    </div>
    ${renderStatusBar(contract, health, latestTs, age)}
  `;'''

if old_hero_tail not in text:
    raise SystemExit("PATCH_FAIL | hero tail block not found")
text = text.replace(old_hero_tail, new_hero_tail, 1)

# 6) Modifier Promise.all pour charger contract
old_promise = '''  const [cockpit, evidenceBus, evidenceReading, timeProfiles, phase, b8, dataHealth] = await Promise.all([
    loadJson(SOURCES.cockpit),
    loadJson(SOURCES.evidenceBus),
    loadJson(SOURCES.evidenceReading),
    loadJson(SOURCES.timeProfiles),
    loadJson(SOURCES.phase),
    loadJson(SOURCES.b8),
    loadJson(SOURCES.dataHealth)
  ]);

  renderHero(evidenceReading, evidenceBus, cockpit);
'''

new_promise = '''  const [cockpit, evidenceBus, evidenceReading, timeProfiles, phase, b8, dataHealth, contract] = await Promise.all([
    loadJson(SOURCES.cockpit),
    loadJson(SOURCES.evidenceBus),
    loadJson(SOURCES.evidenceReading),
    loadJson(SOURCES.timeProfiles),
    loadJson(SOURCES.phase),
    loadJson(SOURCES.b8),
    loadJson(SOURCES.dataHealth),
    loadJson(SOURCES.contract)
  ]);

  const latestTs = newestTimestamp(cockpit, evidenceBus, evidenceReading, timeProfiles, phase, b8, dataHealth, contract);
  const age = ageSeconds(latestTs);

  renderHero(evidenceReading, evidenceBus, cockpit, contract, dataHealth, latestTs, age);
'''

if old_promise not in text:
    raise SystemExit("PATCH_FAIL | promise block not found")
text = text.replace(old_promise, new_promise, 1)

# 7) Ajouter auto-refresh
old_end = '''main().catch(err => {
  document.getElementById("hero").innerHTML = `<h2 class="error">Erreur dashboard</h2><pre>${esc(err.stack || err)}</pre>`;
});
</script>'''

new_end = '''main().catch(err => {
  document.getElementById("hero").innerHTML = `<h2 class="error">Erreur dashboard</h2><pre>${esc(err.stack || err)}</pre>`;
});

setInterval(() => {
  main().catch(err => {
    console.error("dashboard_refresh_error", err);
  });
}, 10000);
</script>'''

if old_end not in text:
    raise SystemExit("PATCH_FAIL | main end block not found")
text = text.replace(old_end, new_end, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.4d auto-refresh + freshness badges | backup={backup.name}")
