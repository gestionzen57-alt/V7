from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75g_quick_nav")
backup.write_text(text, encoding="utf-8")

css = r'''
<style id="pf75g-quick-nav-style">
#pfQuickNav {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 9999;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 520px;
  justify-content: flex-end;
  padding: 10px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(2, 6, 23, 0.82);
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 32px rgba(0,0,0,.35);
}

#pfQuickNav button {
  cursor: pointer;
  border: 1px solid rgba(96, 165, 250, 0.35);
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.95);
  color: #dbeafe;
  font-weight: 800;
  font-size: 11px;
  letter-spacing: .04em;
  padding: 7px 10px;
}

#pfQuickNav button:hover {
  border-color: rgba(34, 211, 238, 0.9);
  color: #ffffff;
  transform: translateY(-1px);
}
</style>
'''

if "pf75g-quick-nav-style" not in text:
    text = text.replace("</head>", css + "\n</head>", 1)

js = r'''
function pf75gFindSectionByTitle(title) {
  const wanted = String(title || "").toLowerCase();
  for (const el of document.querySelectorAll("section, .card")) {
    const h = el.querySelector("h2,h3,h4");
    if (h && h.textContent.toLowerCase().includes(wanted)) return el;
  }
  return null;
}

function pf75gScrollTo(target) {
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function pf75gEnsureQuickNav() {
  if (document.getElementById("pfQuickNav")) return;

  const nav = document.createElement("div");
  nav.id = "pfQuickNav";
  nav.innerHTML = `
    <button data-jump="top">TOP</button>
    <button data-jump="profiles">PROFILES</button>
    <button data-jump="evidence">EVIDENCE</button>
    <button data-jump="memory">MEMORY</button>
    <button data-jump="cockpit">COCKPIT</button>
    <button data-jump="bottom">BOTTOM</button>
  `;

  nav.addEventListener("click", (ev) => {
    const btn = ev.target.closest("button");
    if (!btn) return;

    const jump = btn.dataset.jump;

    if (jump === "top") {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    if (jump === "bottom") {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      return;
    }

    if (jump === "profiles") {
      pf75gScrollTo(pf75gFindSectionByTitle("PROFILS TEMPS"));
      return;
    }

    if (jump === "evidence") {
      pf75gScrollTo(pf75gFindSectionByTitle("EVIDENCE BUS"));
      return;
    }

    if (jump === "memory") {
      pf75gScrollTo(document.getElementById("sessionMemory"));
      return;
    }

    if (jump === "cockpit") {
      pf75gScrollTo(document.getElementById("cockpit") || pf75gFindSectionByTitle("COCKPIT SOURCE"));
      return;
    }
  });

  document.body.appendChild(nav);
}

setTimeout(pf75gEnsureQuickNav, 300);
setTimeout(pf75gEnsureQuickNav, 1200);
setInterval(pf75gEnsureQuickNav, 5000);
'''

if "function pf75gEnsureQuickNav()" not in text:
    idx = text.rfind("</script>")
    if idx == -1:
        raise SystemExit("PATCH_FAIL | no script close marker found")
    text = text[:idx] + js + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5g quick navigation bar | backup={backup.name}")
