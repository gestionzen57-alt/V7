"""PowerFlow B9 dashboard panel patcher V3.

Patch dashboard_v74.html (or a known dashboard fallback) with:
- French dashboard text replacements
- B9 terrain nodes panel HTML
- B9 terrain nodes CSS
- B9 terrain nodes vanilla JS polling /api/b9-nodes-live

No backend mutation. No DB write. Idempotent patch.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
import shutil
from typing import Iterable

PREFERRED_DASHBOARD_NAMES: tuple[str, ...] = (
    "dashboard_v74.html",
    "dashboard_powerflow_v74.html",
    "dashboard_live_v7.2.html",
    "dashboard_live.html",
    "static/dashboard.html",
    "templates/dashboard.html",
)

BACKUP_SUFFIX = ".backup_20260519"

HTML_START = "<!-- B9_TERRAIN_PANEL_START -->"
HTML_END = "<!-- B9_TERRAIN_PANEL_END -->"
CSS_START = "/* B9_TERRAIN_PANEL_CSS_START */"
CSS_END = "/* B9_TERRAIN_PANEL_CSS_END */"
JS_START = "// B9_TERRAIN_PANEL_JS_START"
JS_END = "// B9_TERRAIN_PANEL_JS_END"

TRANSLATIONS: tuple[tuple[str, str], ...] = (
    ("PowerFlow Dashboard", "Tableau de Bord PowerFlow"),
    ("Live Market Data", "Donnees Marche Live"),
    ("Signal Type", "Type Signal"),
    ("Timeframe", "Periode"),
    ("Strength", "Force"),
    ("Timestamp", "Horodatage"),
    ("Status", "Etat"),
    ("Fresh", "Frais"),
    ("Aging", "Vieillissant"),
    ("Stale", "Perime"),
    ("Loading...", "Chargement..."),
    ("Error", "Erreur"),
    ("Refresh", "Actualiser"),
    ("Auto-refresh", "Actualisation auto"),
)

B9_PANEL_HTML = f"""{HTML_START}
<section id="b9-terrain-panel" class="panel dashboard-panel pf-b9-panel" aria-label="Nodes Terrain B9 Live">
    <div class="pf-b9-panel-header">
        <h3>🎯 Nodes Terrain B9 (Live)</h3>
        <div id="b9-status" class="pf-b9-status" aria-live="polite">
            <span id="b9-last-update">Chargement...</span>
            <span id="b9-node-count">0 nodes</span>
        </div>
    </div>
    <div id="b9-nodes-container" class="pf-b9-nodes-container">
        <div class="pf-b9-empty">Chargement des nodes terrain...</div>
    </div>
</section>
{HTML_END}"""

B9_PANEL_CSS = f"""{CSS_START}
#b9-terrain-panel.pf-b9-panel {{
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0 20px 0;
    box-sizing: border-box;
}}

#b9-terrain-panel .pf-b9-panel-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}}

#b9-terrain-panel h3 {{
    margin: 0;
    font-size: 18px;
    color: #fff;
}}

#b9-status.pf-b9-status {{
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    align-items: center;
    padding: 8px 10px;
    background: #222;
    border-radius: 4px;
    font-size: 12px;
    color: #aaa;
    min-width: 220px;
}}

#b9-status.pf-b9-error {{
    color: #ff4444;
}}

#b9-nodes-container.pf-b9-nodes-container {{
    max-height: 400px;
    overflow-y: auto;
}}

.pf-b9-empty {{
    padding: 20px;
    text-align: center;
    color: #666;
}}

.b9-node {{
    background: #222;
    border-left: 4px solid #666;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 8px;
    display: grid;
    grid-template-columns: 40px minmax(0, 1fr) 120px 90px;
    gap: 12px;
    align-items: center;
    transition: background 0.2s ease, transform 0.2s ease;
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
.b9-node.INCONCLUSIVE {{ border-left-color: #aaaaaa; }}

.b9-node .emoji {{
    font-size: 28px;
    text-align: center;
}}

.b9-node-info {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
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
    color: #999;
    overflow-wrap: anywhere;
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
    color: #777;
    text-align: right;
}}

#b9-nodes-container::-webkit-scrollbar {{ width: 6px; }}
#b9-nodes-container::-webkit-scrollbar-track {{ background: #1a1a1a; }}
#b9-nodes-container::-webkit-scrollbar-thumb {{ background: #444; border-radius: 3px; }}
#b9-nodes-container::-webkit-scrollbar-thumb:hover {{ background: #555; }}

@media (max-width: 900px) {{
    #b9-terrain-panel .pf-b9-panel-header {{
        align-items: flex-start;
        flex-direction: column;
    }}
    #b9-status.pf-b9-status {{
        justify-content: space-between;
        width: 100%;
        min-width: 0;
    }}
    .b9-node {{
        grid-template-columns: 36px 1fr;
    }}
    .b9-node-confidence,
    .b9-node-time {{
        grid-column: 2;
        text-align: left;
    }}
}}
{CSS_END}"""

B9_PANEL_JS = f"""{JS_START}
(function () {{
    'use strict';

    const B9_CONFIG = {{
        apiEndpoint: '/api/b9-nodes-live',
        pollInterval: 5000,
        maxNodes: 20,
        symbol: 'GBPUSD'
    }};

    const VERDICT_EMOJI = {{
        'ACCEPTED': '✅',
        'REJECTED': '🔴',
        'PULLBACK_ABSORBED': '🟡',
        'EFFORT_VISIBLE': '🟠',
        'ZONE_CONTESTED': '⚔️',
        'NEUTRAL_DWELL': '⚪',
        'BREAKOUT_CONFIRMED': '🚀',
        'INCONCLUSIVE': '⚪'
    }};

    const VERDICT_FR = {{
        'ACCEPTED': 'Accepté',
        'REJECTED': 'Rejeté',
        'PULLBACK_ABSORBED': 'Pullback absorbé',
        'EFFORT_VISIBLE': 'Effort visible',
        'ZONE_CONTESTED': 'Zone contestée',
        'NEUTRAL_DWELL': 'Stationnement neutre',
        'BREAKOUT_CONFIRMED': 'Cassure confirmée',
        'INCONCLUSIVE': 'Inconclusif'
    }};

    const ROLE_FR = {{
        'RESISTANCE_ACTIVE': 'Résistance active',
        'SUPPORT_ACTIVE': 'Support actif',
        'RESISTANCE_STALE': 'Résistance fatiguée',
        'SUPPORT_STALE': 'Support fatigué',
        'NEUTRAL': 'Zone neutre',
        'HIGH_REJECTION_NODE': 'Rejet de zone haute',
        'FAILED_REINTEGRATION_NODE': 'Réintégration échouée',
        'PULLBACK_ABSORBED_NODE': 'Pullback absorbé',
        'ZONE_ACCEPTANCE_NODE': 'Acceptation de zone',
        'EFFORT_WITHOUT_RESULT_NODE': 'Effort sans résultat',
        'CENTER_MIGRATION_NODE': 'Migration du centre',
        'ROTATION_ANCHOR_NODE': 'Ancre de rotation',
        'ATTENTION_NODE': 'Point d’attention',
        'UNDEFINED_NODE': 'Nœud non défini'
    }};

    function escapeHtml(value) {{
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }}

    function getNodeVerdict(node) {{
        return node.price_verdict_candidate || node.verdict || 'INCONCLUSIVE';
    }}

    function getNodeRoleFr(node) {{
        return node.node_role_fr || ROLE_FR[node.node_role] || ROLE_FR[node.zone_role] || node.node_role || node.zone_role || 'Nœud terrain';
    }}

    function formatPrice(value) {{
        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric.toFixed(5) : '?';
    }}

    function formatPips(low, high) {{
        const lowNum = Number(low);
        const highNum = Number(high);
        if (!Number.isFinite(lowNum) || !Number.isFinite(highNum)) {{
            return '?';
        }}
        return Math.round(Math.abs(highNum - lowNum) * 10000).toString();
    }}

    async function fetchB9Nodes() {{
        const url = `${{B9_CONFIG.apiEndpoint}}?symbol=${{encodeURIComponent(B9_CONFIG.symbol)}}&limit=${{B9_CONFIG.maxNodes}}`;
        try {{
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
        const status = document.getElementById('b9-status');
        const statusUpdate = document.getElementById('b9-last-update');
        const statusCount = document.getElementById('b9-node-count');
        if (!status || !statusUpdate || !statusCount) {{
            return;
        }}
        status.classList.toggle('pf-b9-error', Boolean(isError));
        if (isError) {{
            statusUpdate.textContent = '❌ Erreur connexion';
        }} else {{
            const updateTime = lastUpdate ? new Date(lastUpdate).toLocaleTimeString('fr-FR') : new Date().toLocaleTimeString('fr-FR');
            statusUpdate.textContent = `Dernière mise à jour : ${{updateTime}}`;
        }}
        statusCount.textContent = `${{nodeCount}} node${{nodeCount > 1 ? 's' : ''}}`;
    }}

    function displayB9Nodes(nodes) {{
        const container = document.getElementById('b9-nodes-container');
        if (!container) {{
            return;
        }}
        if (!nodes.length) {{
            container.innerHTML = '<div class="pf-b9-empty">Aucun node détecté</div>';
            return;
        }}
        container.innerHTML = nodes.map(createB9NodeHTML).join('');
    }}

    function createB9NodeHTML(node) {{
        const verdict = getNodeVerdict(node);
        const verdictSafe = String(verdict).replace(/[^A-Z0-9_]/g, '_');
        const emoji = VERDICT_EMOJI[verdict] || '❓';
        const verdictFr = VERDICT_FR[verdict] || String(verdict).replace(/_/g, ' ');
        const roleFr = getNodeRoleFr(node);
        const confidence = Math.round(Number(node.confidence || 0) * 100);
        const timestamp = node.timestamp ? new Date(node.timestamp).toLocaleTimeString('fr-FR') : '?';
        const bounds = node.zone_bounds || node;
        const zoneLow = formatPrice(bounds.zone_low);
        const zoneHigh = formatPrice(bounds.zone_high);
        const zonePips = formatPips(bounds.zone_low, bounds.zone_high);

        return `
            <article class="b9-node ${{verdictSafe}}">
                <div class="emoji">${{emoji}}</div>
                <div class="b9-node-info">
                    <div class="b9-node-role">${{escapeHtml(roleFr)}}</div>
                    <div class="b9-node-verdict">${{escapeHtml(verdictFr)}} <span style="color:#666">(${{escapeHtml(verdict)}})</span></div>
                    <div class="b9-node-zone">Zone ${{zoneLow}} → ${{zoneHigh}} (${{zonePips}} pips)</div>
                </div>
                <div class="b9-node-confidence">
                    <div class="b9-node-confidence-value">${{confidence}}%</div>
                    <div class="b9-node-confidence-label">Confiance</div>
                </div>
                <div class="b9-node-time">${{timestamp}}</div>
            </article>
        `;
    }}

    function initB9Panel() {{
        if (!document.getElementById('b9-terrain-panel')) {{
            return;
        }}
        console.log('[B9 Panel] Initialisation...');
        fetchB9Nodes();
        window.setInterval(fetchB9Nodes, B9_CONFIG.pollInterval);
    }}

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initB9Panel);
    }} else {{
        initB9Panel();
    }}
}}());
{JS_END}"""


@dataclass(frozen=True)
class PatchResult:
    dashboard_path: Path
    backup_path: Path
    changed: bool
    translated: bool
    html_present: bool
    css_present: bool
    js_present: bool


def _normalize_candidate(root: Path, name: str) -> Path:
    return root / Path(name)


def find_dashboard(root: str | Path) -> Path:
    """Find the dashboard file, preferring dashboard_v74.html."""
    root_path = Path(root).resolve()
    if root_path.is_file():
        return root_path

    for name in PREFERRED_DASHBOARD_NAMES:
        candidate = _normalize_candidate(root_path, name)
        if candidate.exists() and candidate.is_file():
            return candidate

    html_files = sorted(root_path.rglob("*.html"))
    if not html_files:
        raise FileNotFoundError(f"No dashboard HTML found under {root_path}")

    scored: list[tuple[int, str, Path]] = []
    for path in html_files:
        lower = path.name.lower()
        score = 0
        if "dashboard" in lower:
            score -= 20
        if "v74" in lower or "v7.4" in lower:
            score -= 10
        if "powerflow" in lower:
            score -= 5
        scored.append((score, str(path).lower(), path))
    return sorted(scored)[0][2]


def translate_dashboard_text(html: str) -> tuple[str, bool]:
    changed = False
    updated = html
    for source, target in TRANSLATIONS:
        if source in updated:
            updated = updated.replace(source, target)
            changed = True
    return updated, changed


def ensure_backup(path: Path) -> Path:
    backup_path = path.with_name(path.name + BACKUP_SUFFIX)
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
    return backup_path


def _insert_after_body(html: str, block: str) -> str:
    body_match = re.search(r"<body\b[^>]*>", html, flags=re.IGNORECASE)
    if body_match:
        insert_pos = body_match.end()
        return html[:insert_pos] + "\n" + block + "\n" + html[insert_pos:]
    return block + "\n" + html


def _insert_css(html: str, css: str) -> str:
    if "</style>" in html.lower():
        matches = list(re.finditer(r"</style>", html, flags=re.IGNORECASE))
        match = matches[-1]
        return html[:match.start()] + "\n" + css + "\n" + html[match.start():]
    head_match = re.search(r"</head>", html, flags=re.IGNORECASE)
    style_block = f"<style>\n{css}\n</style>"
    if head_match:
        return html[:head_match.start()] + style_block + "\n" + html[head_match.start():]
    return style_block + "\n" + html


def _insert_js(html: str, js: str) -> str:
    body_close = re.search(r"</body>", html, flags=re.IGNORECASE)
    script_block = f"<script>\n{js}\n</script>"
    if body_close:
        return html[:body_close.start()] + script_block + "\n" + html[body_close.start():]
    return html + "\n" + script_block + "\n"


def patch_dashboard(path_or_root: str | Path) -> PatchResult:
    dashboard_path = find_dashboard(path_or_root)
    original = dashboard_path.read_text(encoding="utf-8")
    # Translate only on first V3 injection. This prevents broad EN->FR
    # replacements from touching protected JS identifiers inside the injected
    # panel on subsequent idempotent runs.
    if HTML_START in original:
        updated = original
        translated = False
    else:
        updated, translated = translate_dashboard_text(original)

    changed = translated
    if HTML_START not in updated:
        updated = _insert_after_body(updated, B9_PANEL_HTML)
        changed = True
    if CSS_START not in updated:
        updated = _insert_css(updated, B9_PANEL_CSS)
        changed = True
    if JS_START not in updated:
        updated = _insert_js(updated, B9_PANEL_JS)
        changed = True

    backup_path = ensure_backup(dashboard_path)
    if changed:
        dashboard_path.write_text(updated, encoding="utf-8")

    final = dashboard_path.read_text(encoding="utf-8")
    return PatchResult(
        dashboard_path=dashboard_path,
        backup_path=backup_path,
        changed=changed,
        translated=translated,
        html_present=HTML_START in final and HTML_END in final,
        css_present=CSS_START in final and CSS_END in final,
        js_present=JS_START in final and JS_END in final,
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patch PowerFlow dashboard with B9 terrain nodes panel V3.")
    parser.add_argument("--root", default=".", help="Core directory or dashboard HTML path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        result = patch_dashboard(args.root)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[B9 PATCHER V3] FAIL - {exc}")
        return 1

    state = "PATCHED" if result.changed else "ALREADY_PRESENT"
    print(f"[B9 PATCHER V3] {state} {result.dashboard_path}")
    print(f"[B9 PATCHER V3] Backup: {result.backup_path}")
    print(
        "[B9 PATCHER V3] "
        f"HTML={result.html_present} CSS={result.css_present} JS={result.js_present} "
        f"FR_TRANSLATION={result.translated}"
    )
    if not (result.html_present and result.css_present and result.js_present):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
