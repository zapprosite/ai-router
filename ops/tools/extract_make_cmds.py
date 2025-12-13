#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MK   = ROOT / "Makefile"
OUT  = ROOT / "public" / "guide_cmds.json"

# Prefer only explicit panel commands declared in Makefile as '## data-cmd: <command>'
mk_text = MK.read_text(encoding="utf-8") if MK.exists() else ""
data_cmd_re = re.compile(r'^\s*##\s*data-cmd:\s*(.+?)\s*$', re.MULTILINE)
items = [{"cmd": m.group(1), "comment": ""} for m in data_cmd_re.finditer(mk_text)]

# Write output strictly from data-cmd items (no fallbacks)
out = {"terminal": [{"num": i+1, **it} for i,it in enumerate(items)]}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(f"Wrote {OUT} with {len(out['terminal'])} items (data-cmd only)")
