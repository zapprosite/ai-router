#!/usr/bin/env python3
import sys, json, urllib.request

def call_route(messages, budget="balanced", prefer_code=None):
    body = {"messages": messages, "budget": budget}
    if prefer_code is not None:
        body["prefer_code"] = bool(prefer_code)
    req = urllib.request.Request(
        "http://localhost:8082/route",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Protocolo MCP mínimo via stdio (schema simplificado)
def main():
    for line in sys.stdin:
        msg = json.loads(line)
        if msg.get("method") == "tool/list":
            print(json.dumps({"id": msg.get("id"), "result": [{"name":"ai_router.route","description":"Call /route on local AI Router"}]})); sys.stdout.flush()
        elif msg.get("method") == "tool/call":
            params = msg["params"]; name = params["name"]
            if name != "ai_router.route":
                print(json.dumps({"id": msg.get("id"), "error": {"message":"unknown tool"}})); sys.stdout.flush(); continue
            args = params.get("arguments") or {}
            out = call_route(args.get("messages", []), args.get("budget","balanced"), args.get("prefer_code"))
            result = {"content": out.get("content") or out.get("text") or (out.get("message") or {}).get("content") or out.get("output"), "usage": out.get("usage")}
            print(json.dumps({"id": msg.get("id"), "result": result})); sys.stdout.flush()
        else:
            print(json.dumps({"id": msg.get("id"), "error": {"message":"unknown method"}})); sys.stdout.flush()

if __name__ == "__main__":
    main()

