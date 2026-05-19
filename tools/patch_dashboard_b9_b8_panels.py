"""Inject B9/B8 dashboard panels into dashboard_powerflow_v74.html.

Idempotent, read-modify-write with backup. No external dependency.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

MARKER_START = "<!-- B9_B8_PANELS_START -->"
MARKER_END = "<!-- B9_B8_PANELS_END -->"

PANEL_HTML = r'''
<!-- B9_B8_PANELS_START -->
<section id="pf-b9-b8-panels" class="pf-b9-b8-panels">
  <style>
    .pf-b9-b8-panels { margin: 16px 0; padding: 12px; border: 1px solid #334155; border-radius: 12px; background: rgba(15,23,42,0.72); color: #e5e7eb; font-family: system-ui, Arial, sans-serif; }
    .pf-b9-b8-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
    .pf-b9-card { border: 1px solid #475569; border-radius: 10px; padding: 12px; background: rgba(30,41,59,0.82); }
    .pf-b9-card h3 { margin: 0 0 8px 0; font-size: 16px; }
    .pf-b9-meta { font-size: 12px; opacity: 0.82; margin-bottom: 8px; }
    .pf-b9-node { border-top: 1px solid #334155; padding: 8px 0; }
    .pf-b9-node:first-of-type { border-top: 0; }
    .pf-b9-verdict { font-weight: 700; }
    .pf-b9-risk { color: #fbbf24; font-size: 12px; }
    .pf-b8-group { margin-top: 8px; }
    .pf-b8-row { display: grid; grid-template-columns: 84px 1fr 64px; gap: 8px; align-items: center; font-size: 13px; margin: 5px 0; }
    .pf-b8-bar { height: 8px; border-radius: 999px; background: linear-gradient(90deg, #64748b, #e5e7eb); opacity: 0.9; }
    .pf-b9-empty { opacity: 0.75; font-size: 13px; }
    .pf-b9-stale { color: #f59e0b; }
  </style>
  <div class="pf-b9-b8-grid">
    <article class="pf-b9-card">
      <h3>🧠 B9 Nodes Terrain</h3>
      <div id="pf-b9-status" class="pf-b9-meta">Chargement B9...</div>
      <div id="pf-b9-nodes"><div class="pf-b9-empty">En attente nodes...</div></div>
    </article>
    <article class="pf-b9-card">
      <h3>🌐 B8 Coalitions USD</h3>
      <div id="pf-b8-status" class="pf-b9-meta">Chargement B8...</div>
      <div id="pf-b8-context"><div class="pf-b9-empty">En attente coalition...</div></div>
    </article>
  </div>
  <script>
    (function () {
      const API = 'http://localhost:8880';
      function verdictEmoji(v) {
        const text = String(v || '').toUpperCase();
        if (text.includes('REJECT') || text.includes('DOWN')) return '🔴';
        if (text.includes('ACCEPT') || text.includes('UP') || text.includes('PROGRESSIVE')) return '🟢';
        if (text.includes('PARTIAL') || text.includes('UNKNOWN')) return '🟡';
        return '⚡';
      }
      function pct(x) {
        const n = Number(x || 0);
        return Math.max(0, Math.min(100, Math.round(n * 100)));
      }
      async function fetchJson(path) {
        const res = await fetch(API + path, { cache: 'no-store' });
        if (!res.ok) throw new Error(path + ' HTTP ' + res.status);
        return await res.json();
      }
      function renderB9(data) {
        const status = document.getElementById('pf-b9-status');
        const box = document.getElementById('pf-b9-nodes');
        status.textContent = `count=${data.count || 0} visibility=${data.data_visibility || 'UNKNOWN'} ${data.timestamp || ''}`;
        if (data.technical_risks && data.technical_risks.length) status.classList.add('pf-b9-stale');
        if (!data.nodes || !data.nodes.length) {
          box.innerHTML = `<div class="pf-b9-empty">Aucun node récent. ${(data.technical_risks || []).join(', ')}</div>`;
          return;
        }
        box.innerHTML = data.nodes.map(n => {
          const verdict = n.verdict || n.requalified_event || n.event || n.status || 'NODE';
          const conf = pct(n.confidence || n.requalified_confidence || n.score || 0);
          const ts = n.timestamp || '';
          return `<div class="pf-b9-node"><div><span class="pf-b9-verdict">${verdictEmoji(verdict)} ${verdict}</span> — ${conf}%</div><div class="pf-b9-meta">${ts}</div><div>${n.reading_fr || n.message || n.requalified_event_fr || ''}</div></div>`;
        }).join('');
      }
      function renderGroup(title, rows) {
        if (!rows || !rows.length) return `<div class="pf-b8-group"><b>${title}</b><div class="pf-b9-empty">vide</div></div>`;
        return `<div class="pf-b8-group"><b>${title}</b>` + rows.map(r => {
          const sym = r.symbol || r.pair || r.name || 'n/a';
          const strength = Number(r.strength || r.score || r.value || 0);
          const width = Math.max(5, Math.min(100, Math.round(Math.abs(strength) * 100)));
          return `<div class="pf-b8-row"><span>${sym}</span><span><span class="pf-b8-bar" style="display:block;width:${width}%"></span></span><span>${strength.toFixed ? strength.toFixed(2) : strength}</span></div>`;
        }).join('') + `</div>`;
      }
      function renderB8(data) {
        const status = document.getElementById('pf-b8-status');
        const box = document.getElementById('pf-b8-context');
        status.textContent = `visibility=${data.data_visibility || 'UNKNOWN'} ${data.timestamp || ''}`;
        if (data.technical_risks && data.technical_risks.length) status.classList.add('pf-b9-stale');
        box.innerHTML = renderGroup('USD Quote', data.usd_quote) + renderGroup('USD Base', data.usd_base) + renderGroup('GBP Cross', data.gbp_cross);
      }
      async function pollB9() {
        try { renderB9(await fetchJson('/api/b9-nodes-live?symbol=GBPUSD&limit=10')); }
        catch (e) { document.getElementById('pf-b9-status').textContent = 'B9 API unreachable: ' + e.message; }
      }
      async function pollB8() {
        try { renderB8(await fetchJson('/api/b8-coalition-context?symbol=GBPUSD')); }
        catch (e) { document.getElementById('pf-b8-status').textContent = 'B8 API unreachable: ' + e.message; }
      }
      pollB9(); pollB8();
      setInterval(pollB9, 5000);
      setInterval(pollB8, 10000);
    })();
  </script>
</section>
<!-- B9_B8_PANELS_END -->
'''


def find_dashboard(repo_root: Path, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = repo_root / path
        return path
    candidates = [
        repo_root / "Core" / "dashboard_powerflow_v74.html",
        repo_root / "dashboard_powerflow_v74.html",
    ]
    for path in candidates:
        if path.exists():
            return path
    matches = list(repo_root.rglob("dashboard_powerflow_v74.html"))
    if matches:
        return matches[0]
    return candidates[0]


def patch_dashboard(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Dashboard file not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".b9_backup_{stamp}")
    backup.write_text(text, encoding="utf-8")

    if MARKER_START in text and MARKER_END in text:
        before = text.split(MARKER_START)[0]
        after = text.split(MARKER_END, 1)[1]
        new_text = before + PANEL_HTML.strip() + after
        action = "updated existing B9/B8 panel block"
    elif "</body>" in text.lower():
        idx = text.lower().rfind("</body>")
        new_text = text[:idx] + "\n" + PANEL_HTML.strip() + "\n" + text[idx:]
        action = "inserted B9/B8 panel block before </body>"
    else:
        new_text = text + "\n" + PANEL_HTML.strip() + "\n"
        action = "appended B9/B8 panel block"

    path.write_text(new_text, encoding="utf-8")
    return f"{action}; backup={backup}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path.cwd().parent if Path.cwd().name.lower() == "core" else Path.cwd()))
    parser.add_argument("--dashboard", default=None)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    dashboard = find_dashboard(repo_root, args.dashboard)
    print(f"[B9-DASHBOARD] repo_root={repo_root}")
    print(f"[B9-DASHBOARD] dashboard={dashboard}")
    result = patch_dashboard(dashboard)
    print(f"[B9-DASHBOARD] {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
