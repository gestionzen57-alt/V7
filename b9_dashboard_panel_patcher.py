"""PowerFlow B9 dashboard panel patcher.

Read-only relative to backend B9: this script only patches the dashboard HTML file.
It is idempotent and creates a .b9_backup before the first modification.
"""
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PANEL_VERSION = "B9_GPT2_DASHBOARD_PANEL_V1"
HTML_START = "<!-- B9_PANEL_START -->"
HTML_END = "<!-- B9_PANEL_END -->"
CSS_START = "/* B9_PANEL_CSS_START */"
CSS_END = "/* B9_PANEL_CSS_END */"
JS_START = "// B9_PANEL_JS_START"
JS_END = "// B9_PANEL_JS_END"

DASHBOARD_CANDIDATES = (
    "dashboard_v74.html",
    "dashboard.html",
    "static/dashboard.html",
    "templates/dashboard.html",
)

HTML_BLOCK = f"""{HTML_START}
<div id=\"b9-terrain-panel\" class=\"panel\" data-panel-version=\"{PANEL_VERSION}\">
    <h3>🎯 Nodes Terrain B9 (Live)</h3>
    <div id=\"b9-status\" class=\"status-bar\">
        <span id=\"b9-last-update\">Chargement...</span>
        <span id=\"b9-node-count\">0 nodes</span>
    </div>
    <div id=\"b9-nodes-container\"></div>
</div>
{HTML_END}"""

CSS_BLOCK = f"""{CSS_START}
#b9-terrain-panel {{
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
}}

#b9-terrain-panel h3 {{
    margin: 0 0 12px 0;
    font-size: 18px;
    color: #fff;
}}

#b9-status {{
    display: flex;
    justify-content: space-between;
    padding: 8px;
    background: #222;
    border-radius: 4px;
    margin-bottom: 12px;
    font-size: 12px;
    color: #888;
}}

#b9-nodes-container {{
    max-height: 400px;
    overflow-y: auto;
}}

.b9-node {{
    background: #222;
    border-left: 4px solid #666;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 8px;
    display: grid;
    grid-template-columns: 40px 1fr 120px 80px;
    gap: 12px;
    align-items: center;
    transition: all 0.2s ease;
}}

.b9-node:hover {{
    background: #2a2a2a;
    transform: translateX(2px);
}}

.b9-node.ACCEPTED {{ border-left-color: #00ff88; }}
.b9-node.REJECTED {{ border-left-color: #ff4444; }}
.b9-node.PULLBACK_ABSORBED {{ border-left-color: #ffaa00; }}
.b9-node.EFFORT_VISIBLE {{ border-left-color: #ff9900; }}
.b9-node.ZONE_CONTESTED {{ border-left-color: #ffdd00; }}
.b9-node.NEUTRAL_DWELL {{ border-left-color: #888888; }}
.b9-node.BREAKOUT_CONFIRMED {{ border-left-color: #00ccff; }}

.b9-node .emoji {{
    font-size: 28px;
    text-align: center;
}}

.b9-node-info {{
    display: flex;
    flex-direction: column;
    gap: 4px;
}}

.b9-node-role {{
    font-size: 14px;
    font-weight: 600;
    color: #fff;
}}

.b9-node-verdict {{
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.b9-node-zone {{
    font-family: 'Courier New', monospace;
    font-size: 11px;
    color: #666;
}}

.b9-node-confidence {{
    background: #333;
    border-radius: 4px;
    padding: 6px 10px;
    text-align: center;
}}

.b9-node-confidence-value {{
    font-size: 18px;
    font-weight: 700;
    color: #fff;
}}

.b9-node-confidence-label {{
    font-size: 9px;
    color: #888;
    text-transform: uppercase;
}}

.b9-node-time {{
    font-size: 11px;
    color: #666;
    text-align: right;
}}

#b9-nodes-container::-webkit-scrollbar {{ width: 6px; }}
#b9-nodes-container::-webkit-scrollbar-track {{ background: #1a1a1a; }}
#b9-nodes-container::-webkit-scrollbar-thumb {{ background: #444; border-radius: 3px; }}
#b9-nodes-container::-webkit-scrollbar-thumb:hover {{ background: #555; }}
{CSS_END}"""

JS_BLOCK = f"""{JS_START}
const B9_CONFIG = {{
    apiEndpoint: '/api/b9-nodes-live',
    pollInterval: 5000,
    maxNodes: 20,
    symbol: 'GBPUSD',
}};

const VERDICT_EMOJI = {{
    'ACCEPTED': '✅',
    'REJECTED': '🔴',
    'PULLBACK_ABSORBED': '🟡',
    'EFFORT_VISIBLE': '🟠',
    'ZONE_CONTESTED': '⚔️',
    'NEUTRAL_DWELL': '⚪',
    'BREAKOUT_CONFIRMED': '🚀',
}};

const ZONE_ROLE_FR = {{
    'RESISTANCE_ACTIVE': 'Résistance Active',
    'SUPPORT_ACTIVE': 'Support Actif',
    'RESISTANCE_STALE': 'Résistance Fatiguée',
    'SUPPORT_STALE': 'Support Fatigué',
    'NEUTRAL': 'Zone Neutre',
    'HIGH_REJECTION_NODE': 'Node rejet zone haute',
    'FAILED_REINTEGRATION_NODE': 'Réintégration échouée',
    'PULLBACK_ABSORBED_NODE': 'Pullback absorbé',
    'ZONE_ACCEPTANCE_NODE': 'Acceptation zone',
    'EFFORT_WITHOUT_RESULT_NODE': 'Effort sans résultat',
    'CENTER_MIGRATION_NODE': 'Migration centre',
    'ROTATION_ANCHOR_NODE': 'Ancre de rotation',
    'ATTENTION_NODE': 'Node attention',
    'UNDEFINED_NODE': 'Node non défini',
}};

async function fetchB9Nodes() {{
    try {{
        const url = `${{B9_CONFIG.apiEndpoint}}?symbol=${{B9_CONFIG.symbol}}&limit=${{B9_CONFIG.maxNodes}}`;
        const response = await fetch(url);
        if (!response.ok) {{
            throw new Error(`API error: ${{response.status}}`);
        }}
        const data = await response.json();
        const nodes = Array.isArray(data.nodes) ? data.nodes : [];
        updateB9Status(nodes.length, data.last_update);
        displayB9Nodes(nodes);
    }} catch (error) {{
        console.error('[B9 Panel] Fetch error:', error);
        updateB9Status(0, null, true);
    }}
}}

function updateB9Status(nodeCount, lastUpdate, isError = false) {{
    const statusUpdate = document.getElementById('b9-last-update');
    const statusCount = document.getElementById('b9-node-count');
    if (!statusUpdate || !statusCount) return;

    if (isError) {{
        statusUpdate.textContent = '❌ Erreur connexion';
        statusUpdate.style.color = '#ff4444';
    }} else {{
        const updateTime = lastUpdate ? new Date(lastUpdate).toLocaleTimeString('fr-FR') : 'N/A';
        statusUpdate.textContent = `Dernière mise à jour : ${{updateTime}}`;
        statusUpdate.style.color = '#888';
    }}
    statusCount.textContent = `${{nodeCount}} node${{nodeCount > 1 ? 's' : ''}}`;
}}

function displayB9Nodes(nodes) {{
    const container = document.getElementById('b9-nodes-container');
    if (!container) return;

    if (!nodes || nodes.length === 0) {{
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Aucun node détecté</div>';
        return;
    }}
    container.innerHTML = nodes.map(node => createB9NodeHTML(node)).join('');
}}

function escapeB9Text(value) {{
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}}

function createB9NodeHTML(node) {{
    const verdict = node.price_verdict_candidate || 'NEUTRAL_DWELL';
    const emoji = VERDICT_EMOJI[verdict] || '⚪';
    const roleKey = node.node_role || node.zone_role || 'NEUTRAL';
    const roleFr = ZONE_ROLE_FR[roleKey] || roleKey;
    const confidence = Math.round((node.confidence || 0) * 100);
    const timestamp = node.timestamp ? new Date(node.timestamp).toLocaleTimeString('fr-FR') : 'N/A';
    const zoneLowRaw = node.zone_bounds?.zone_low;
    const zoneHighRaw = node.zone_bounds?.zone_high;
    const zoneLow = Number.isFinite(zoneLowRaw) ? zoneLowRaw.toFixed(4) : '?';
    const zoneHigh = Number.isFinite(zoneHighRaw) ? zoneHighRaw.toFixed(4) : '?';
    const zonePips = Number.isFinite(zoneLowRaw) && Number.isFinite(zoneHighRaw)
        ? Math.abs((zoneHighRaw - zoneLowRaw) * 10000).toFixed(0)
        : '?';

    return `
        <div class="b9-node ${{escapeB9Text(verdict)}}">
            <div class="emoji">${{emoji}}</div>
            <div class="b9-node-info">
                <div class="b9-node-role">${{escapeB9Text(roleFr)}}</div>
                <div class="b9-node-verdict">${{escapeB9Text(verdict.replace(/_/g, ' '))}}</div>
                <div class="b9-node-zone">Zone ${{zoneLow}} → ${{zoneHigh}} (${{zonePips}} pips)</div>
            </div>
            <div class="b9-node-confidence">
                <div class="b9-node-confidence-value">${{confidence}}%</div>
                <div class="b9-node-confidence-label">Confiance</div>
            </div>
            <div class="b9-node-time">${{escapeB9Text(timestamp)}}</div>
        </div>
    `;
}}

function initB9Panel() {{
    console.log('[B9 Panel] Initialisation...');
    fetchB9Nodes();
    setInterval(fetchB9Nodes, B9_CONFIG.pollInterval);
}}

if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initB9Panel);
}} else {{
    initB9Panel();
}}
{JS_END}"""


@dataclass(frozen=True)
class PatchReport:
    dashboard_path: Path
    changed: bool
    backup_path: Path | None
    html_present: bool
    css_present: bool
    js_present: bool


def find_dashboard(core_path: Path, extra_candidates: Iterable[str] = ()) -> Path:
    candidates = tuple(extra_candidates) + DASHBOARD_CANDIDATES
    for candidate in candidates:
        path = core_path / candidate
        if path.exists() and path.is_file():
            return path

    html_files = sorted(core_path.rglob("*.html"), key=lambda p: ("dashboard" not in p.name.lower(), len(str(p))))
    for path in html_files:
        if "dashboard" in path.name.lower():
            return path

    if html_files:
        return html_files[0]

    raise FileNotFoundError(f"Aucun fichier HTML dashboard trouvé dans {core_path}")


def _insert_before(text: str, marker: str, block: str) -> str:
    index = text.lower().rfind(marker.lower())
    if index == -1:
        return text + "\n" + block + "\n"
    return text[:index] + block + "\n" + text[index:]


def _insert_html(text: str) -> str:
    if HTML_START in text:
        return text
    main_end = text.lower().rfind("</div>")
    body_end = text.lower().rfind("</body>")
    if main_end != -1 and (body_end == -1 or main_end < body_end):
        return text[:main_end] + HTML_BLOCK + "\n" + text[main_end:]
    return _insert_before(text, "</body>", HTML_BLOCK)


def _insert_css(text: str) -> str:
    if CSS_START in text:
        return text
    style_end = text.lower().rfind("</style>")
    if style_end != -1:
        return text[:style_end] + CSS_BLOCK + "\n" + text[style_end:]
    head_end = text.lower().rfind("</head>")
    style_block = f"<style>\n{CSS_BLOCK}\n</style>"
    if head_end != -1:
        return text[:head_end] + style_block + "\n" + text[head_end:]
    return style_block + "\n" + text


def _insert_js(text: str) -> str:
    if JS_START in text:
        return text
    script_block = f"<script>\n{JS_BLOCK}\n</script>"
    return _insert_before(text, "</body>", script_block)


def patch_dashboard(dashboard_path: Path) -> PatchReport:
    dashboard_path = dashboard_path.resolve()
    original = dashboard_path.read_text(encoding="utf-8")

    patched = _insert_html(original)
    patched = _insert_css(patched)
    patched = _insert_js(patched)

    changed = patched != original
    backup_path: Path | None = None
    if changed:
        backup_path = dashboard_path.with_suffix(dashboard_path.suffix + ".b9_backup")
        if not backup_path.exists():
            shutil.copy2(dashboard_path, backup_path)
        dashboard_path.write_text(patched, encoding="utf-8")

    final_text = patched if changed else original
    return PatchReport(
        dashboard_path=dashboard_path,
        changed=changed,
        backup_path=backup_path,
        html_present=HTML_START in final_text and HTML_END in final_text,
        css_present=CSS_START in final_text and CSS_END in final_text,
        js_present=JS_START in final_text and JS_END in final_text,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch PowerFlow dashboard with B9 live nodes panel")
    parser.add_argument("--core", default=".", help="Core directory containing dashboard HTML")
    parser.add_argument("--dashboard", default="", help="Explicit dashboard HTML path")
    parser.add_argument("--apply", action="store_true", help="Apply patch. Without this flag, only locate dashboard")
    args = parser.parse_args()

    core_path = Path(args.core).resolve()
    dashboard_path = Path(args.dashboard).resolve() if args.dashboard else find_dashboard(core_path)

    if not args.apply:
        print(f"[B9 PATCHER] Dashboard trouvé: {dashboard_path}")
        return 0

    report = patch_dashboard(dashboard_path)
    status = "PATCHED" if report.changed else "ALREADY_PRESENT"
    print(f"[B9 PATCHER] {status} {report.dashboard_path}")
    if report.backup_path:
        print(f"[B9 PATCHER] Backup: {report.backup_path}")
    print(f"[B9 PATCHER] HTML={report.html_present} CSS={report.css_present} JS={report.js_present}")
    return 0 if report.html_present and report.css_present and report.js_present else 2


if __name__ == "__main__":
    raise SystemExit(main())
