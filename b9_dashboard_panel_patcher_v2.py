"""
PowerFlow V7.6.7 B9 - Dashboard B9 Terrain Panel Patcher V2.

Patch read-only style: modifies only the dashboard HTML file selected by path/root.
Creates one .b9_backup next to the target before first mutation.
No backend mutation. No DB write. No external JS dependency.
"""
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HTML_MARKER_BEGIN = "<!-- BEGIN POWERFLOW B9 TERRAIN PANEL V2 -->"
HTML_MARKER_END = "<!-- END POWERFLOW B9 TERRAIN PANEL V2 -->"
CSS_MARKER_BEGIN = "/* BEGIN POWERFLOW B9 TERRAIN PANEL CSS V2 */"
CSS_MARKER_END = "/* END POWERFLOW B9 TERRAIN PANEL CSS V2 */"
JS_MARKER_BEGIN = "// BEGIN POWERFLOW B9 TERRAIN PANEL JS V2"
JS_MARKER_END = "// END POWERFLOW B9 TERRAIN PANEL JS V2"

DEFAULT_DASHBOARD_CANDIDATES = (
    "dashboard_v74.html",
    "dashboard_powerflow_v74.html",
    "dashboard_live_v7.2.html",
    "static/dashboard.html",
    "templates/dashboard.html",
)

PANEL_HTML = f"""{HTML_MARKER_BEGIN}
<div id="b9-terrain-panel" class="panel dashboard-panel">
    <h3>🎯 Nodes Terrain B9 (Live)</h3>
    <div id="b9-status" class="status-bar">
        <span id="b9-last-update">Chargement...</span>
        <span id="b9-node-count">0 nodes</span>
    </div>
    <div id="b9-nodes-container" aria-live="polite"></div>
</div>
{HTML_MARKER_END}"""

PANEL_CSS = f"""{CSS_MARKER_BEGIN}
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

@media (max-width: 900px) {{
    .b9-node {{
        grid-template-columns: 32px 1fr;
    }}
    .b9-node-confidence,
    .b9-node-time {{
        grid-column: 2;
        text-align: left;
    }}
}}
{CSS_MARKER_END}"""

PANEL_JS = f"""{JS_MARKER_BEGIN}
(function () {{
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
    }};

    function safeText(value, fallback) {{
        if (value === null || value === undefined || value === '') {{
            return fallback;
        }}
        return String(value);
    }}

    function safePrice(value) {{
        const numberValue = Number(value);
        if (!Number.isFinite(numberValue)) {{
            return '?';
        }}
        return numberValue.toFixed(4);
    }}

    function safeTimestamp(value) {{
        if (!value) {{
            return 'N/A';
        }}
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {{
            return String(value);
        }}
        return date.toLocaleTimeString('fr-FR');
    }}

    async function fetchB9Nodes() {{
        try {{
            const url = `${{B9_CONFIG.apiEndpoint}}?symbol=${{encodeURIComponent(B9_CONFIG.symbol)}}&limit=${{B9_CONFIG.maxNodes}}`;
            const response = await fetch(url);

            if (!response.ok) {{
                throw new Error(`API error: ${{response.status}}`);
            }}

            const data = await response.json();
            const nodes = Array.isArray(data.nodes) ? data.nodes : [];
            updateB9Status(nodes.length, data.last_update, false);
            displayB9Nodes(nodes);
        }} catch (error) {{
            console.error('[B9 Panel] Fetch error:', error);
            updateB9Status(0, null, true);
        }}
    }}

    function updateB9Status(nodeCount, lastUpdate, isError) {{
        const statusUpdate = document.getElementById('b9-last-update');
        const statusCount = document.getElementById('b9-node-count');
        if (!statusUpdate || !statusCount) {{
            return;
        }}

        if (isError) {{
            statusUpdate.textContent = '❌ Erreur connexion';
            statusUpdate.style.color = '#ff4444';
        }} else {{
            statusUpdate.textContent = `Dernière mise à jour : ${{safeTimestamp(lastUpdate)}}`;
            statusUpdate.style.color = '#888';
        }}

        statusCount.textContent = `${{nodeCount}} node${{nodeCount > 1 ? 's' : ''}}`;
    }}

    function displayB9Nodes(nodes) {{
        const container = document.getElementById('b9-nodes-container');
        if (!container) {{
            return;
        }}

        if (!nodes || nodes.length === 0) {{
            container.innerHTML = '<div style="padding:20px;text-align:center;color:#666;">Aucun node détecté</div>';
            return;
        }}

        container.innerHTML = nodes.map(createB9NodeHTML).join('');
    }}

    function createB9NodeHTML(node) {{
        const verdict = safeText(node.price_verdict_candidate, 'NEUTRAL_DWELL');
        const safeVerdictClass = verdict.replace(/[^A-Z0-9_]/g, '');
        const emoji = VERDICT_EMOJI[verdict] || '⚪';
        const roleFr = safeText(node.node_role_fr || ZONE_ROLE_FR[node.node_role], safeText(node.node_role, 'Node terrain'));
        const confidence = Math.round((Number(node.confidence) || 0) * 100);
        const timestamp = safeTimestamp(node.timestamp);
        const zoneBounds = node.zone_bounds || {{}};
        const zoneLow = safePrice(zoneBounds.zone_low);
        const zoneHigh = safePrice(zoneBounds.zone_high);
        let zonePips = '?';

        if (Number.isFinite(Number(zoneBounds.zone_high)) && Number.isFinite(Number(zoneBounds.zone_low))) {{
            zonePips = Math.round((Number(zoneBounds.zone_high) - Number(zoneBounds.zone_low)) * 10000).toString();
        }}

        return `
            <div class="b9-node ${{safeVerdictClass}}">
                <div class="emoji">${{emoji}}</div>
                <div class="b9-node-info">
                    <div class="b9-node-role">${{roleFr}}</div>
                    <div class="b9-node-verdict">${{verdict.replace(/_/g, ' ')}}</div>
                    <div class="b9-node-zone">Zone ${{zoneLow}} → ${{zoneHigh}} (${{zonePips}} pips)</div>
                </div>
                <div class="b9-node-confidence">
                    <div class="b9-node-confidence-value">${{confidence}}%</div>
                    <div class="b9-node-confidence-label">Confiance</div>
                </div>
                <div class="b9-node-time">${{timestamp}}</div>
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
}}());
{JS_MARKER_END}"""


@dataclass(frozen=True)
class PatchResult:
    dashboard_path: Path
    status: str
    backup_path: Path
    html_present: bool
    css_present: bool
    js_present: bool


def _case_insensitive_child(root: Path, relative_path: str) -> Path | None:
    current = root
    for part in Path(relative_path).parts:
        if not current.exists() or not current.is_dir():
            return None
        matches = [child for child in current.iterdir() if child.name.lower() == part.lower()]
        if not matches:
            return None
        current = matches[0]
    return current if current.is_file() else None


def find_dashboard_file(root: Path, candidates: Iterable[str] = DEFAULT_DASHBOARD_CANDIDATES) -> Path:
    """Find the dashboard HTML file, preferring dashboard_v74.html exactly."""
    root = root.resolve()
    for candidate in candidates:
        found = _case_insensitive_child(root, candidate)
        if found:
            return found

    html_files = sorted(root.rglob("*.html"), key=lambda path: ("dashboard" not in path.name.lower(), len(path.parts), path.name.lower()))
    dashboard_files = [path for path in html_files if "dashboard" in path.name.lower()]
    if dashboard_files:
        return dashboard_files[0]

    raise FileNotFoundError(f"No dashboard HTML file found under {root}")


def _insert_before_case_insensitive(text: str, marker: str, insertion: str) -> str:
    index = text.lower().rfind(marker.lower())
    if index == -1:
        return text + "\n" + insertion + "\n"
    return text[:index] + insertion + "\n" + text[index:]


def inject_css(text: str) -> str:
    if CSS_MARKER_BEGIN in text:
        return text
    if "</style>" in text.lower():
        return _insert_before_case_insensitive(text, "</style>", PANEL_CSS)
    style_block = f"<style>\n{PANEL_CSS}\n</style>"
    return _insert_before_case_insensitive(text, "</head>", style_block)


def inject_html(text: str) -> str:
    if HTML_MARKER_BEGIN in text:
        return text
    return _insert_before_case_insensitive(text, "</body>", PANEL_HTML)


def inject_js(text: str) -> str:
    if JS_MARKER_BEGIN in text:
        return text
    script_block = f"<script>\n{PANEL_JS}\n</script>"
    return _insert_before_case_insensitive(text, "</body>", script_block)


def patch_dashboard(dashboard_path: Path) -> PatchResult:
    dashboard_path = dashboard_path.resolve()
    original = dashboard_path.read_text(encoding="utf-8")
    backup_path = dashboard_path.with_name(dashboard_path.name + ".b9_backup")

    before = original
    patched = inject_css(original)
    patched = inject_html(patched)
    patched = inject_js(patched)

    status = "ALREADY_PRESENT" if patched == before else "PATCHED"
    if status == "PATCHED":
        if not backup_path.exists():
            shutil.copy2(dashboard_path, backup_path)
        dashboard_path.write_text(patched, encoding="utf-8")

    final_text = dashboard_path.read_text(encoding="utf-8")
    return PatchResult(
        dashboard_path=dashboard_path,
        status=status,
        backup_path=backup_path,
        html_present=HTML_MARKER_BEGIN in final_text,
        css_present=CSS_MARKER_BEGIN in final_text,
        js_present=JS_MARKER_BEGIN in final_text,
    )


def patch_from_root(root: Path) -> PatchResult:
    return patch_dashboard(find_dashboard_file(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject PowerFlow B9 Terrain panel into dashboard HTML.")
    parser.add_argument("--root", default=".", help="Core directory used to find dashboard_v74.html.")
    parser.add_argument("--dashboard", default=None, help="Explicit dashboard HTML path.")
    args = parser.parse_args()

    try:
        if args.dashboard:
            result = patch_dashboard(Path(args.dashboard))
        else:
            result = patch_from_root(Path(args.root))
        print(f"[B9 PATCHER V2] {result.status} {result.dashboard_path}")
        if result.backup_path.exists():
            print(f"[B9 PATCHER V2] Backup: {result.backup_path}")
        print(f"[B9 PATCHER V2] HTML={result.html_present} CSS={result.css_present} JS={result.js_present}")
        return 0 if result.html_present and result.css_present and result.js_present else 2
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[B9 PATCHER V2] ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
