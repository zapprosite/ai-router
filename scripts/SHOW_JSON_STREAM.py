#!/usr/bin/env python3
import os, json, time, threading, queue, sys, subprocess, textwrap
import urllib.request

BASE = "http://localhost:8082"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("OPENAI_API_KEY_TIER2", None)
os.environ["ENABLE_OPENAI_FALLBACK"] = "0"

LOG = "showtime.jsonl"
open(LOG, "w").close()

def post_route(payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}/route", data=data, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def pretty_line(obj: dict) -> str:
    mdl = obj.get("model_id") or obj.get("usage",{}).get("resolved_model_id")
    lat = obj.get("usage",{}).get("latency_ms_router")
    out = (obj.get("output") or "").replace("\n"," ")
    if out and len(out) > 160: out = out[:160] + "…"
    return json.dumps({"model_id": mdl, "latency_ms_router": lat, "output": out}, ensure_ascii=False)

CHAT_LONG = ("Explique, com exemplos práticos, fundamentos de HVAC, "
            "carga térmica, dutos (Darcy-Weisbach) e checklist. ") * 12
CODE_PROMPT = "Escreva um CLI Python parseador de nvidia-smi em JSON; inclua docstring e exemplo."

def worker_text(qout: queue.Queue, count: int):
    for _ in range(count):
        o = post_route({"messages":[{"role":"user","content":CHAT_LONG}]})
        qout.put(("CHAT", o))
def worker_code(qout: queue.Queue, count: int):
    for _ in range(count):
        o = post_route({"messages":[{"role":"user","content":CODE_PROMPT}], "prefer_code": True})
        qout.put(("CODE", o))

def main():
    total_each = int(os.environ.get("EACH", "6"))  # 6 chat + 6 code
    qout: queue.Queue = queue.Queue()
    t1 = threading.Thread(target=worker_text, args=(qout, total_each), daemon=True)
    t2 = threading.Thread(target=worker_code, args=(qout, total_each), daemon=True)
    t1.start(); t2.start()

    got = 0; total = total_each*2
    cyan="\033[36m"; green="\033[32m"; dim="\033[2m"; reset="\033[0m"
    print(f"\n\033[38;5;214m== SHOW JSON STREAM • local GPU • {total_each} chat + {total_each} code ==\033[0m")
    while got < total:
        try:
            kind, obj = qout.get(timeout=300)
        except queue.Empty:
            break
        got += 1
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        line = pretty_line(obj)
        color = cyan if kind == "CHAT" else green
        print(f"{color}[{kind}]{reset} {line}")
    print(f"\n\033[38;5;214m== FIM • log: {LOG} ==\033[0m")

if __name__ == "__main__":
    main()
