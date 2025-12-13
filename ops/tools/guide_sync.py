#!/usr/bin/env python3
import json
import re
from pathlib import Path

H = Path("public/Guide.html")
J = Path("public/guide_cmds.json")

html = H.read_text(encoding="utf-8")
data = json.loads(J.read_text(encoding="utf-8"))

# Garante marcadores (janela auto) – não altera o visual existente
START = "<!-- CMDS_AUTO_START -->"
END   = "<!-- CMDS_AUTO_END -->"
if START not in html or END not in html:
    # tenta inserir após a área de comandos
    html = html.replace(
        '<div class="cmds">',
        '<div class="cmds">\n' + START + '\n<div id="cmds-list"></div>\n' + END
    )

# Monta bloco (comentário visível + botão numerado que copia APENAS o comando)
rows = []
items = data if isinstance(data, list) else data.get("terminal", [])
for it in items:
    num = it.get("num","?")
    cmd = it.get("cmd","")
    cmt = it.get("comment","—")
    safe_cmd = cmd.replace("\\","\\\\").replace('"',"&quot;")
    rows.append(
        f'  <div class="cmd"># {num}) {cmt}\n{cmd}</div>\n'
        f'  <button class="num" data-cmd="{safe_cmd}">{num}</button>\n'
    )
block = "\n".join(rows) if rows else "  <!-- sem itens no guide_cmds.json -->"

html = re.sub(
    r'(' + re.escape(START) + r')[\s\S]*?(' + re.escape(END) + r')',
    START + "\n" + block + "\n" + END,
    html,
    count=1
)

H.write_text(html, encoding="utf-8")
print("OK: Guide.html sincronizado a partir do JSON")
