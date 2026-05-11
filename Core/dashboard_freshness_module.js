/* PowerFlow V7.2 dashboard freshness module
 * Contract:
 *   FRESH  age < 300s
 *   AGING  300s <= age < 600s
 *   STALE  age >= 600s
 *   MISSING source absent/empty/invalid
 */
(function (global) {
  "use strict";

  const REFRESH_INTERVAL_MS = 30000;
  const AGING_THRESHOLD_S = 300;
  const STALE_THRESHOLD_S = 600;

  function parseTimestamp(data) {
    return data.timestamp_utc || data.timestamp || data.generated_utc || data.updated_at || null;
  }

  function computeFreshness(data, nowMs) {
    const ts = parseTimestamp(data || {});
    if (!data || !ts) {
      return { freshness: "MISSING", ageSeconds: null, timestampUtc: null };
    }
    const parsed = new Date(ts).getTime();
    if (!Number.isFinite(parsed)) {
      return { freshness: "MISSING", ageSeconds: null, timestampUtc: ts };
    }
    const ageSeconds = Math.max(0, Math.floor(((nowMs || Date.now()) - parsed) / 1000));
    const freshness = ageSeconds >= STALE_THRESHOLD_S ? "STALE" :
      ageSeconds >= AGING_THRESHOLD_S ? "AGING" : "FRESH";
    return { freshness, ageSeconds, timestampUtc: new Date(parsed).toISOString().replace("T", " ").replace(".000Z", " UTC") };
  }

  function setHeader(block, meta) {
    const fresh = block.querySelector(".pf-freshness");
    const ts = block.querySelector(".pf-timestamp");
    const age = block.querySelector(".pf-age");
    block.dataset.freshness = meta.freshness;
    block.dataset.ageSeconds = meta.ageSeconds === null ? "" : String(meta.ageSeconds);
    if (fresh) {
      fresh.className = "pf-freshness " + meta.freshness;
      fresh.textContent = meta.freshness === "MISSING" ? "✕ MISSING" : "● " + meta.freshness;
    }
    if (ts) ts.textContent = meta.timestampUtc || "timestamp missing";
    if (age) age.textContent = meta.ageSeconds === null ? "n/a" : meta.ageSeconds + "s";
  }

  function showMissingState(blockId, source) {
    const block = document.getElementById(blockId);
    if (!block) return;
    setHeader(block, { freshness: "MISSING", ageSeconds: null, timestampUtc: null });
    const content = block.querySelector(".pf-block-content");
    if (content) {
      content.innerHTML = `<div class="pf-missing-data">✕ Donnée absente ou JSON invalide<br><span>${source}</span></div>`;
    }
  }

  function renderKeyValues(block, data) {
    const content = block.querySelector(".pf-block-content");
    if (!content) return;
    if (!data || Object.keys(data).length === 0) {
      content.innerHTML = "<div class=\"pf-missing-data\">✕ JSON vide</div>";
      return;
    }
    const skip = new Set(["timestamp", "timestamp_utc", "generated_utc", "updated_at"]);
    const rows = Object.entries(data)
      .filter(([k]) => !skip.has(k))
      .slice(0, 18)
      .map(([k, v]) => `<div class="pf-kv"><span>${k}</span><strong>${typeof v === "object" ? JSON.stringify(v) : v}</strong></div>`)
      .join("");
    content.innerHTML = rows || "<div class=\"pf-muted\">Aucune donnée métier dans ce JSON.</div>";
  }

  function updateBlock(blockId, data, customRenderer) {
    const block = document.getElementById(blockId);
    if (!block) return;
    const meta = computeFreshness(data);
    setHeader(block, meta);
    if (meta.freshness === "MISSING") {
      showMissingState(blockId, block.dataset.source || "unknown source");
      return;
    }
    if (typeof customRenderer === "function") customRenderer(block, data, meta);
    else renderKeyValues(block, data);
  }

  async function loadAndRefreshBlock(jsonPath, blockId, customRenderer) {
    try {
      const response = await fetch(jsonPath + "?nocache=" + Date.now());
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      if (!data || (Array.isArray(data) && data.length === 0)) throw new Error("empty JSON");
      updateBlock(blockId, data, customRenderer);
    } catch (e) {
      showMissingState(blockId, jsonPath);
    }
  }

  global.PowerFlowFreshness = {
    REFRESH_INTERVAL_MS,
    AGING_THRESHOLD_S,
    STALE_THRESHOLD_S,
    computeFreshness,
    updateBlock,
    loadAndRefreshBlock,
    showMissingState
  };
})(window);
