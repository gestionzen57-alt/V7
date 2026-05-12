from pathlib import Path
import re

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75b_cockpit_risks_session_order")
backup.write_text(text, encoding="utf-8")

# 1) Humanize label= leaks globally in rendered text helpers.
# Add a small JS helper if absent.
if "function pf75HumanText(" not in text:
    js = r'''
function pf75HumanText(v) {
  if (v === null || v === undefined) return "";
  if (typeof v === "object") {
    if (v.label) return pf75HumanText(v.label);
    if (v.message) return pf75HumanText(v.message);
    if (v.code) return pf75HumanText(v.code);
    try { return JSON.stringify(v); } catch (e) { return ""; }
  }

  let s = String(v);
  s = s.replace(/^label=/i, "");
  s = s.replace(/^message=/i, "");
  s = s.replace(/^code=/i, "");
  s = s.replaceAll("Ã¨", "è")
       .replaceAll("Ã©", "é")
       .replaceAll("Ãª", "ê")
       .replaceAll("Ã ", "à")
       .replaceAll("Ã§", "ç")
       .replaceAll("Ã´", "ô")
       .replaceAll("â€™", "'")
       .replaceAll("â€œ", '"')
       .replaceAll("â€", '"');
  return s;
}
'''
    idx = text.rfind("</script>")
    if idx == -1:
        raise SystemExit("PATCH_FAIL | no script close marker found")
    text = text[:idx] + js + "\n" + text[idx:]

# 2) Ensure pf75Esc uses pf75HumanText when present.
text = re.sub(
    r'function pf75Esc\(v\) \{\s*if \(v === null \|\| v === undefined\) return "";\s*if \(typeof v === "object"\) \{.*?return String\(v\)\s*\.replaceAll\("&", "&amp;"\)\s*\.replaceAll\("<", "&lt;"\)\s*\.replaceAll\(">", "&gt;"\)\s*\.replaceAll\(\'"\', "&quot;"\);\s*\}',
    '''function pf75Esc(v) {
  const clean = (typeof pf75HumanText === "function") ? pf75HumanText(v) : (v === null || v === undefined ? "" : String(v));
  return String(clean)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}''',
    text,
    flags=re.S
)

# 3) Patch generic list rendering: remove visible label= in any template output.
# This is defensive: browser-side cleanup after render.
if "function pf75CleanVisibleLeaks(" not in text:
    js2 = r'''
function pf75CleanVisibleLeaks() {
  const root = document.body;
  if (!root) return;

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  for (const n of nodes) {
    if (!n.nodeValue) continue;
    let s = n.nodeValue;
    s = s.replace(/\blabel=/gi, "");
    s = s.replace(/\bmessage=/gi, "");
    s = s.replace(/\bcode=/gi, "");
    s = s.replaceAll("Ã¨", "è")
         .replaceAll("Ã©", "é")
         .replaceAll("Ãª", "ê")
         .replaceAll("Ã ", "à")
         .replaceAll("Ã§", "ç")
         .replaceAll("Ã´", "ô")
         .replaceAll("â€™", "'")
         .replaceAll("â€œ", '"')
         .replaceAll("â€", '"');
    if (s !== n.nodeValue) n.nodeValue = s;
  }
}

setInterval(pf75CleanVisibleLeaks, 1500);
setTimeout(pf75CleanVisibleLeaks, 500);
setTimeout(pf75CleanVisibleLeaks, 2000);
'''
    idx = text.rfind("</script>")
    text = text[:idx] + js2 + "\n" + text[idx:]

# 4) Ensure Session Memory section appears before Cockpit Source if both exist.
session = re.search(r'\s*<section[^>]+id=["\']sessionMemory["\'][^>]*></section>\s*', text)
cockpit = re.search(r'\s*<section[^>]+id=["\']cockpit["\'][^>]*></section>\s*', text)

if session and cockpit and session.start() > cockpit.start():
    session_html = session.group(0)
    text = text[:session.start()] + text[session.end():]
    cockpit = re.search(r'\s*<section[^>]+id=["\']cockpit["\'][^>]*></section>\s*', text)
    if cockpit:
        text = text[:cockpit.start()] + session_html + text[cockpit.start():]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5b cockpit risk cleanup + session order | backup={backup.name}")
