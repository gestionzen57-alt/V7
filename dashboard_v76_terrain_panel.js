(function () {
  "use strict";

  const PANEL_ID = "pf-v76-terrain-live-panel";
  const NAV_ID = "pf-v76-terrain-nav";
  const SYMBOL = "GBPUSD";

  function byId(id) {
    return document.getElementById(id);
  }

  function esc(value) {
    if (value === null || value === undefined || value === "") return "—";
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  async function fetchJson(path) {
    try {
      const response = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
      if (!response.ok) return null;
      return await response.json();
    } catch (_) {
      return null;
    }
  }

  async function fetchText(path) {
    try {
      const response = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
      if (!response.ok) return "";
      return await response.text();
    } catch (_) {
      return "";
    }
  }

  function chip(label, cls) {
    return `<span class="pf-v76-chip ${cls || ""}">${esc(label)}</span>`;
  }

  function line(label, value) {
    return `<div class="pf-v76-line"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
  }

  function paragraph(label, value) {
    return `
      <div class="pf-v76-block">
        <div class="pf-v76-block-title">${esc(label)}</div>
        <div class="pf-v76-block-text">${esc(value)}</div>
      </div>`;
  }

  function importantClass(value) {
    const v = String(value || "").toUpperCase();
    if (v.includes("UNKNOWN")) return "muted";
    if (v.includes("RISK") || v.includes("EXHAUSTION") || v.includes("REJECTION")) return "warn";
    if (v.includes("UNWIND") || v.includes("SECOND_LEG") || v.includes("CONTINUATION")) return "hot";
    return "";
  }

  function installShell() {
    if (byId(PANEL_ID)) return;

    const style = document.createElement("style");
    style.id = "pf-v76-terrain-style";
    style.textContent = `
      #${PANEL_ID} {
        margin: 16px 18px;
        padding: 16px;
        border: 1px solid rgba(122, 162, 255, 0.22);
        border-radius: 16px;
        background: linear-gradient(180deg, rgba(13, 22, 38, 0.98), rgba(11, 18, 31, 0.98));
        color: #e9f1ff;
        box-shadow: 0 12px 32px rgba(0,0,0,0.25);
      }
      #${PANEL_ID} .pf-v76-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 12px;
        margin-bottom: 14px;
      }
      #${PANEL_ID} h2 {
        margin: 0;
        font-size: 18px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      #${PANEL_ID} .pf-v76-subtitle {
        margin-top: 6px;
        color: #9fb0c8;
        font-size: 12px;
      }
      #${PANEL_ID} .pf-v76-grid {
        display: grid;
        grid-template-columns: minmax(280px, 1.2fr) minmax(280px, 1fr);
        gap: 14px;
      }
      #${PANEL_ID} .pf-v76-card {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        background: rgba(255,255,255,0.025);
        padding: 14px;
      }
      #${PANEL_ID} .pf-v76-card h3 {
        margin: 0 0 10px;
        color: #dfeaff;
        font-size: 13px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }
      #${PANEL_ID} .pf-v76-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0 0;
      }
      #${PANEL_ID} .pf-v76-chip {
        display: inline-flex;
        align-items: center;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 999px;
        padding: 5px 9px;
        background: rgba(255,255,255,0.04);
        font-size: 11px;
        font-weight: 700;
      }
      #${PANEL_ID} .pf-v76-chip.hot { color: #ffdf7b; border-color: rgba(255, 201, 80, .45); }
      #${PANEL_ID} .pf-v76-chip.warn { color: #ff9f8d; border-color: rgba(255, 117, 89, .45); }
      #${PANEL_ID} .pf-v76-chip.good { color: #91f5bd; border-color: rgba(88, 220, 143, .45); }
      #${PANEL_ID} .pf-v76-chip.muted { color: #9fb0c8; }
      #${PANEL_ID} .pf-v76-line {
        display: grid;
        grid-template-columns: 160px 1fr;
        gap: 10px;
        padding: 5px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        font-size: 12px;
      }
      #${PANEL_ID} .pf-v76-line span { color: #9fb0c8; }
      #${PANEL_ID} .pf-v76-line strong { color: #f3f7ff; }
      #${PANEL_ID} .pf-v76-block {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(255,255,255,0.06);
      }
      #${PANEL_ID} .pf-v76-block-title {
        color: #8fb6ff;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .06em;
        margin-bottom: 5px;
        font-weight: 800;
      }
      #${PANEL_ID} .pf-v76-block-text {
        color: #edf3ff;
        line-height: 1.45;
        font-size: 13px;
        white-space: pre-wrap;
      }
      #${PANEL_ID} .pf-v76-message {
        white-space: pre-wrap;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12px;
        line-height: 1.45;
        color: #eaf2ff;
        max-height: 380px;
        overflow: auto;
        border-radius: 12px;
        background: rgba(0,0,0,0.18);
        padding: 12px;
      }
      #${PANEL_ID} .pf-v76-small {
        color: #8fa0b8;
        font-size: 11px;
      }
      #${PANEL_ID} .pf-v76-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      #${PANEL_ID} button.pf-v76-btn {
        border: 1px solid rgba(122,162,255,.35);
        background: rgba(122,162,255,.1);
        color: #eaf2ff;
        border-radius: 999px;
        padding: 8px 12px;
        cursor: pointer;
        font-weight: 800;
        font-size: 11px;
      }
      #${PANEL_ID} button.pf-v76-btn:hover {
        background: rgba(122,162,255,.18);
      }
      #${NAV_ID} {
        position: fixed;
        right: 120px;
        bottom: 18px;
        z-index: 9999;
        border: 1px solid rgba(122,162,255,.35);
        background: rgba(10,16,28,.94);
        color: #eaf2ff;
        border-radius: 999px;
        padding: 9px 13px;
        cursor: pointer;
        font-weight: 900;
        font-size: 11px;
        letter-spacing: .03em;
      }
      @media (max-width: 980px) {
        #${PANEL_ID} .pf-v76-grid { grid-template-columns: 1fr; }
        #${PANEL_ID} .pf-v76-line { grid-template-columns: 120px 1fr; }
      }
    `;
    document.head.appendChild(style);

    const panel = document.createElement("section");
    panel.id = PANEL_ID;
    panel.innerHTML = `
      <div class="pf-v76-header">
        <div>
          <h2>PowerFlow V7.6 — Terrain Live GBPUSD</h2>
          <div class="pf-v76-subtitle">Lecture utile trader : terrain packet, mémoire B6, playbook, état Telegram.</div>
        </div>
        <div class="pf-v76-actions">
          <button class="pf-v76-btn" type="button" data-pf-refresh>Rafraîchir</button>
        </div>
      </div>
      <div data-pf-v76-content class="pf-v76-small">Chargement V7.6...</div>
    `;

    const anchor = document.querySelector("main") || document.body;
    const firstSection = anchor.querySelector("section");
    if (firstSection && firstSection.parentNode) {
      firstSection.parentNode.insertBefore(panel, firstSection.nextSibling);
    } else {
      anchor.insertBefore(panel, anchor.firstChild);
    }

    const nav = document.createElement("button");
    nav.id = NAV_ID;
    nav.type = "button";
    nav.textContent = "TERRAIN V7.6";
    nav.addEventListener("click", () => panel.scrollIntoView({ behavior: "smooth", block: "start" }));
    document.body.appendChild(nav);

    panel.querySelector("[data-pf-refresh]").addEventListener("click", loadAndRender);
  }

  function render(content, packet, memory, playbook, messageFr, cycle) {
    const risks = Array.isArray(packet.technical_risks) ? packet.technical_risks : [];
    const similar = Array.isArray(packet.similar_historical_days) ? packet.similar_historical_days : (Array.isArray(memory.similar_historical_days) ? memory.similar_historical_days : []);
    const similarText = similar.slice(0, 3).map((x) => {
      if (!x || typeof x !== "object") return "";
      return `${x.day || "?"} — ${x.label_fr || x.film_id || "film"} (${x.confidence ?? "?"})`;
    }).filter(Boolean).join("\n");

    content.innerHTML = `
      <div class="pf-v76-chips">
        ${chip(packet.symbol || SYMBOL, "good")}
        ${chip(packet.film_state, importantClass(packet.film_state))}
        ${chip(packet.qualified_bias, importantClass(packet.qualified_bias))}
        ${chip(packet.packet_quality, importantClass(packet.packet_quality))}
        ${chip(packet.data_visibility, importantClass(packet.data_visibility))}
      </div>

      <div class="pf-v76-grid" style="margin-top:14px;">
        <div class="pf-v76-card">
          <h3>Lecture terrain</h3>
          ${line("Film", packet.film_state)}
          ${line("Dernier événement", packet.last_structural_event)}
          ${line("Zone", packet.current_zone || `${packet.current_zone_low || "?"}-${packet.current_zone_high || "?"}`)}
          ${line("Rôle mouvement", packet.current_move_role)}
          ${line("Raw bias", packet.raw_bias)}
          ${line("Bias qualifié", packet.qualified_bias)}
          ${line("Prix", packet.price_confirmation)}
          ${line("Propagation", packet.propagation_state)}
          ${line("Texture", packet.detachment_texture)}
          ${line("Risques", risks.length ? risks.join(", ") : "—")}
          ${paragraph("À surveiller", packet.watch_condition_fr || packet.watch_condition)}
          ${paragraph("Invalidation", packet.invalidation_condition_fr || packet.invalidation_condition)}
        </div>

        <div class="pf-v76-card">
          <h3>Scénario trader</h3>
          ${line("Playbook", packet.playbook_label_fr || playbook.playbook_label_fr)}
          ${line("État", packet.playbook_state || playbook.playbook_state)}
          ${paragraph("Contexte", packet.playbook_context_fr || playbook.playbook_context_fr)}
          ${paragraph("Plan", packet.watch_plan_fr || playbook.watch_plan_fr)}
          ${paragraph("Invalidation", packet.invalidation_fr || playbook.invalidation_fr)}
          ${paragraph("Avertissement", packet.no_trade_warning_fr || playbook.no_trade_warning_fr)}
        </div>

        <div class="pf-v76-card">
          <h3>Mémoire B6</h3>
          ${line("Film proche", packet.memory_match || memory.memory_match)}
          ${line("Confiance", packet.memory_confidence ?? memory.memory_confidence)}
          ${paragraph("Raison", packet.memory_reason_fr || memory.memory_reason_fr)}
          ${paragraph("Films proches", similarText || "—")}
        </div>

        <div class="pf-v76-card">
          <h3>Telegram / Message final</h3>
          ${line("Mode dernier cycle", cycle?.telegram?.telegram_mode || "—")}
          ${line("Retour Telegram", cycle?.telegram?.returncode ?? "—")}
          ${line("Fingerprint", cycle?.telegram?.fingerprint || packet.fingerprint || "—")}
          <div class="pf-v76-message">${esc(messageFr || "terrain_packet_fr.txt indisponible")}</div>
        </div>
      </div>
    `;
  }

  async function loadAndRender() {
    installShell();
    const content = byId(PANEL_ID).querySelector("[data-pf-v76-content]");
    content.textContent = "Chargement V7.6...";

    const base = "output/dashboard_surface/GBPUSD/";
    const packet = await fetchJson(base + "terrain_packet.json") || {};
    const memory = await fetchJson(base + "film_memory_match.json") || {};
    const playbook = await fetchJson(base + "trader_playbook.json") || {};
    const cycle = await fetchJson(base + "v76_telegram_cycle_result.json") || {};
    const messageFr = await fetchText(base + "terrain_packet_fr.txt");

    render(content, packet, memory, playbook, messageFr, cycle);
  }

  function start() {
    installShell();
    loadAndRender();
    setInterval(loadAndRender, 10000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
