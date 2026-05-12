from pathlib import Path
import re

path = Path("dashboard_powerflow_v74.html")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_v75d_session_before_footer")
backup.write_text(text, encoding="utf-8")

session_re = re.compile(r'\s*<section[^>]+id=["\']sessionMemory["\'][^>]*></section>\s*', re.I)
session = session_re.search(text)

if not session:
    raise SystemExit("PATCH_FAIL | sessionMemory section not found")

session_html = session.group(0)
text_without = text[:session.start()] + text[session.end():]

# Try to place before footer. Fallback: before </main>, then before </body>.
footer = re.search(r'\s*<footer[\s\S]*?</footer>\s*', text_without, re.I)

if footer:
    text = text_without[:footer.start()] + session_html + text_without[footer.start():]
elif "</main>" in text_without:
    text = text_without.replace("</main>", session_html + "\n</main>", 1)
elif "</body>" in text_without:
    text = text_without.replace("</body>", session_html + "\n</body>", 1)
else:
    raise SystemExit("PATCH_FAIL | no footer/main/body insertion point found")

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | session memory moved before footer | backup={backup.name}")
