from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75h_quick_nav_autohide")
backup.write_text(text, encoding="utf-8")

css = r'''
<style id="pf75h-quick-nav-autohide-style">
#pfQuickNav {
  opacity: 0.42;
  transform: translateY(8px);
  transition: opacity .18s ease, transform .18s ease, box-shadow .18s ease;
}

#pfQuickNav:hover,
#pfQuickNav.pf-nav-active {
  opacity: 1;
  transform: translateY(0);
}

#pfQuickNav button {
  min-width: 58px;
}

@media (max-width: 1200px) {
  #pfQuickNav {
    left: 18px;
    right: 18px;
    bottom: 12px;
    max-width: none;
    justify-content: center;
  }
}
</style>
'''

if "pf75h-quick-nav-autohide-style" not in text:
    text = text.replace("</head>", css + "\n</head>", 1)

js = r'''
function pf75hNavActivity() {
  const nav = document.getElementById("pfQuickNav");
  if (!nav) return;

  let t = null;
  const wake = () => {
    nav.classList.add("pf-nav-active");
    clearTimeout(t);
    t = setTimeout(() => nav.classList.remove("pf-nav-active"), 1800);
  };

  window.addEventListener("mousemove", wake, { passive: true });
  window.addEventListener("scroll", wake, { passive: true });
  nav.addEventListener("mouseenter", wake);
  wake();
}

setTimeout(pf75hNavActivity, 500);
'''

if "function pf75hNavActivity()" not in text:
    idx = text.rfind("</script>")
    if idx == -1:
        raise SystemExit("PATCH_FAIL | no script close marker found")
    text = text[:idx] + js + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5h quick nav autohide | backup={backup.name}")
