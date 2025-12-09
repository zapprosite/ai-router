#!/usr/bin/env python3
import sys, os, argparse
try:
    import yaml
except Exception:
    print("PyYAML é obrigatório: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REQ_ROLES = {"chat","autocomplete","edit","apply"}

def validate(path: str) -> list[str]:
    errs = []
    if not os.path.exists(path):
        return [f"missing {path}"]
    with open(path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f) or {}

    # models.router-auto
    models = d.get("models") or []
    m = next((x for x in models if (x or {}).get("name") == "router-auto"), None)
    if not m:
        errs.append("models: router-auto model missing")
    else:
        if m.get("provider") != "openai":
            errs.append("models.router-auto.provider must be 'openai'")
        if m.get("model") != "router-auto":
            errs.append("models.router-auto.model must be 'router-auto'")
        api_base = str(m.get("apiBase",""))
        if not api_base.endswith("/v1"):
            errs.append("models.router-auto.apiBase must end with '/v1'")
        roles = set(m.get("roles") or [])
        miss = sorted(list(REQ_ROLES - roles))
        if miss:
            errs.append(f"models.router-auto.roles missing: {', '.join(miss)}")
        if "apiKey" not in m:
            errs.append("models.router-auto.apiKey field must exist (value not validated)")

    # agent.*
    a = d.get("agent") or {}
    for k in ["chatModel","editModel","applyModel","autocompleteModel"]:
        if a.get(k) != "router-auto":
            errs.append(f"agent.{k} must be 'router-auto'")

    # MCP opcional: só validar se presente
    mcps = d.get("mcpServers")
    if mcps is not None:
        if not isinstance(mcps, list):
            errs.append("mcpServers must be a list if present")
        else:
            srv = next((s for s in mcps if (s or {}).get("name") == "ai_router_mcp"), None)
            if srv:
                if not srv.get("command"):
                    errs.append("mcpServers.ai_router_mcp.command missing")
                args = srv.get("args")
                if not isinstance(args, list) or not args:
                    errs.append("mcpServers.ai_router_mcp.args missing or empty")
    return errs

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--path", default=".continue/config.yaml")
    args = p.parse_args()
    errs = validate(args.path)
    if errs:
        print("\n".join(errs)); sys.exit(1)
    print("continue-config: OK")

if __name__ == "__main__":
    main()
