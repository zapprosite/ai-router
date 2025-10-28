#!/usr/bin/env python3
import importlib, pathlib, json, os, sys, yaml

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

report = {"modules":{}, "config":{}, "registry":{}}

def mod_info(name):
    try:
        m = importlib.import_module(name)
        f = pathlib.Path(getattr(m,"__file__","")).resolve()
        return {"ok": True, "file": str(f)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

for m in ["app.main","graph.router","providers.openai_client","providers.ollama_client"]:
    report["modules"][m] = mod_info(m)

# Config carregada pelo router
try:
    from graph.router import CONFIG_PATH
    cfg_path = pathlib.Path(CONFIG_PATH).resolve()
    report["config"]["path"] = str(cfg_path)
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)
    report["registry"] = {m["id"]: m for m in cfg.get("models", [])}
except Exception as e:
    report["config"]["error"] = str(e)

# Ambiente mínimo que impacta execução
report["env"] = {
    "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL"),
    "OPENAI_API_KEY": ("SET" if os.getenv("OPENAI_API_KEY") else None),
    "OPENAI_API_KEY_TIER2": ("SET" if os.getenv("OPENAI_API_KEY_TIER2") else None),
    "OPENAI_ORGANIZATION": os.getenv("OPENAI_ORGANIZATION") or os.getenv("OPENAI_ORG"),
    "OPENAI_PROJECT": os.getenv("OPENAI_PROJECT"),
}

print(json.dumps(report, indent=2))
