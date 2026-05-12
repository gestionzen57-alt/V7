from pathlib import Path

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75f_session_full_width")
backup.write_text(text, encoding="utf-8")

css = r'''
<style id="pf75f-session-full-width-style">
#sessionMemory {
  width: 100% !important;
  max-width: none !important;
  grid-column: 1 / -1 !important;
  display: block !important;
  box-sizing: border-box;
}

#sessionMemory table {
  width: 100% !important;
  table-layout: auto !important;
}

#sessionMemory th,
#sessionMemory td {
  white-space: nowrap;
  vertical-align: top;
}

#sessionMemory th:nth-child(7),
#sessionMemory td:nth-child(7) {
  white-space: normal;
  min-width: 360px;
  max-width: 720px;
  line-height: 1.45;
}

#sessionMemory details {
  width: 100%;
  box-sizing: border-box;
}

#sessionMemory .session-scroll {
  overflow-x: auto;
  width: 100%;
}
</style>
'''

if "pf75f-session-full-width-style" not in text:
    text = text.replace("</head>", css + "\n</head>", 1)

# Wrap session memory tables into horizontal scroll containers.
# Safe defensive browser-side patch.
js = r'''
function pf75fWidenSessionMemory() {
  const session = document.getElementById("sessionMemory");
  if (!session) return;

  session.classList.add("wide");
  session.style.gridColumn = "1 / -1";
  session.style.width = "100%";

  for (const table of session.querySelectorAll("table")) {
    if (!table.parentElement.classList.contains("session-scroll")) {
      const wrap = document.createElement("div");
      wrap.className = "session-scroll";
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    }
  }
}

setTimeout(pf75fWidenSessionMemory, 300);
setTimeout(pf75fWidenSessionMemory, 1200);
setInterval(pf75fWidenSessionMemory, 5000);
'''

if "function pf75fWidenSessionMemory()" not in text:
    idx = text.rfind("</script>")
    if idx == -1:
        raise SystemExit("PATCH_FAIL | no script close marker found")
    text = text[:idx] + js + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.5f session memory full width | backup={backup.name}")
