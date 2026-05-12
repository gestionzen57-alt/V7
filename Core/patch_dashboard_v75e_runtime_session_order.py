from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75e_runtime_session_order")
backup.write_text(text, encoding="utf-8")

js = r'''
function pf75eForceSessionOrder() {
  const session = document.getElementById("sessionMemory");
  const cockpit = document.getElementById("cockpit");
  const footer = document.querySelector("footer");

  if (session && cockpit && cockpit.parentNode) {
    cockpit.parentNode.insertBefore(session, cockpit);
  }

  if (footer && footer.parentNode) {
    footer.parentNode.appendChild(footer);
  }
}

setTimeout(pf75eForceSessionOrder, 300);
setTimeout(pf75eForceSessionOrder, 1200);
setInterval(pf75eForceSessionOrder, 5000);
'''

if "function pf75eForceSessionOrder()" not in text:
    idx = text.rfind("</script>")
    if idx == -1:
        raise SystemExit("PATCH_FAIL | no script close marker found")
    text = text[:idx] + js + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5e runtime session order enforced | backup={backup.name}")
