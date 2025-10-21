from __future__ import annotations
from typing import Dict, Any, Literal
from pydantic import BaseModel
import os, re, math, json, asyncio, httpx

# --- ENV / defaults (alinha com env unificado) ---
OLLAMA = (os.getenv("OLLAMA_URL","http://127.0.0.1:11434")).rstrip("/")
CLOUD  = (os.getenv("CLOUD_RESPONSES_BASE", os.getenv("CLOUD_API_BASE","https://api.openai.com/v1"))).rstrip("/")
CLOUD_KEY = os.getenv("CLOUD_API_KEY") or os.getenv("OPENAI_API_KEY","")
LOCAL_CHAT = os.getenv("LOCAL_CHAT_MODEL","qwen3:8b")
LOCAL_CODE = os.getenv("LOCAL_CODE_MODEL","qwen3:14b")
CLOUD_DEFAULT = os.getenv("CLOUD_RESPONSES_MODEL","gpt-5-codex")
JUDGE_MODEL = os.getenv("JUDGE_MODEL","gpt-5-nano")

# --- Policy load ---
def load_yaml_policy() -> Dict[str, Any]:
    import yaml
    path = os.getenv("ROUTER_POLICY","router_policy.yaml")
    if os.path.exists(path):
        with open(path,"r") as f:
            return yaml.safe_load(f) or {}
    return {}

POLICY = load_yaml_policy()
THR = POLICY.get("thresholds", {"docs":{"small_tokens":600,"medium_tokens":3000},"code":{"small_tokens":400,"medium_tokens":2000}})
TIMEOUTS = POLICY.get("timeouts_ms", {"ollama_generate":20000,"cloud_chat":25000})

# --- Token estimation ---
def count_tokens(txt:str)->int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(txt))
    except Exception:
        # Aproximação: 1 token ~ 4 chars
        return math.ceil(len(txt)/4)

# --- Heurística de domínio/complexidade ---
CODE_HINTS = re.compile(r"```|class\s+\w+:|def\s+\w+\(|function\s+\w+\(|#include\s|SELECT\s|INSERT\s|<\w+>|curl\s-|\bpytest\b|\basync\s+def\b|\bconst\b|\bvar\b|\blet\b", re.I)
DOCS_HINTS = re.compile(r"\b(resumo|explicar|documentar|política|processo|brief|proposta|análise)\b", re.I)

def heuristic_judge(inp:str)->Dict[str,str]:
    is_code = bool(CODE_HINTS.search(inp))
    is_docs = bool(DOCS_HINTS.search(inp))
    domain = "code" if is_code and not is_docs else "docs"
    tk = count_tokens(inp)
    # complexidade: linhas, blocos de código, pedidos de múltiplos artefatos
    lines = inp.count("\n")+1
    code_blocks = inp.count("```")
    asks = len(re.findall(r"\b(e|and|;)\b", inp))
    complexity = "high" if code_blocks>=2 or lines>150 or tk>2500 or asks>6 else ("mid" if lines>40 or tk>800 else "low")
    return {"domain":domain, "complexity":complexity}

async def llm_judge(inp:str)->Dict[str,str]:
    """Classifica via LLM rápido quando CLOUD_KEY existir; cai para heurística em erro/timeout."""
    if not CLOUD_KEY: return heuristic_judge(inp)
    prompt = (
      "You are a strict classifier. Task: decide domain and complexity.\n"
      "Output JSON only: {\"domain\":\"code|docs\",\"complexity\":\"low|mid|high\"}.\n"
      "domain=code if user asks for programming, scripts, queries, APIs, configs.\n"
      "complexity=high if long, multi-file, tests, or many steps; low if short.\n"
      f"INPUT:\n{inp[:6000]}"
    )
    try:
        async with httpx.AsyncClient(timeout=1.6) as c:
            r = await c.post(f"{CLOUD}/chat/completions",
                headers={"authorization":f"Bearer {CLOUD_KEY}"},
                json={"model":JUDGE_MODEL,"messages":[{"role":"user","content":prompt}],"temperature":0})
            if r.status_code==200:
                txt = r.json()["choices"][0]["message"]["content"]
                # tenta extrair JSON
                m = re.search(r"\{.*\}", txt, re.S)
                if m:
                    data = json.loads(m.group(0))
                    if data.get("domain") in ("code","docs") and data.get("complexity") in ("low","mid","high"):
                        return {"domain":data["domain"],"complexity":data["complexity"]}
    except Exception:
        pass
    return heuristic_judge(inp)

# --- Seleção de modelo ---
def select_model(domain:str, tokens:int, complexity:str)->str:
    if domain=="code":
        if tokens <= THR["code"]["small_tokens"] and complexity!="high":
            return LOCAL_CODE  # code local
        elif tokens <= THR["code"]["medium_tokens"]:
            return "gpt-5-codex"
        else:
            return "gpt-5-high"
    else: # docs
        if tokens <= THR["docs"]["small_tokens"] and complexity!="high":
            return LOCAL_CHAT  # docs local rápido
        elif tokens <= THR["docs"]["medium_tokens"]:
            return "gpt-5-mini"
        else:
            return "gpt-5-high"

def provider_of(model_id:str)->Literal["local","cloud"]:
    return "local" if ":" in model_id and model_id.startswith(("qwen","llama","phi","mistral")) else "cloud"

# --- Execução no modelo escolhido ---
async def run_local_ollama(model:str, prompt:str)->str:
    payload = {"model":model,"prompt":prompt,"stream":False}
    async with httpx.AsyncClient(timeout=TIMEOUTS["ollama_generate"]/1000) as c:
        r = await c.post(f"{OLLAMA}/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response","")

async def run_cloud_chat(model:str, prompt:str)->str:
    payload = {"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0}
    async with httpx.AsyncClient(timeout=TIMEOUTS["cloud_chat"]/1000) as c:
        r = await c.post(f"{CLOUD}/chat/completions",
                         headers={"authorization":f"Bearer {CLOUD_KEY}"},
                         json=payload)
        r.raise_for_status()
        j=r.json()
        return j["choices"][0]["message"]["content"]

async def route_and_generate(user_input:str, forced_model:str|None=None)->Dict[str,Any]:
    # 1) Julgamento
    judge_used = "heuristic"
    judge = await llm_judge(user_input)
    if CLOUD_KEY: judge_used = "llm"
    tokens = count_tokens(user_input)

    # 2) Seleção
    model = forced_model or select_model(judge["domain"], tokens, judge["complexity"])
    route = provider_of(model)

    # 3) Execução com fallback
    try:
        if route=="local":
            out = await run_local_ollama(model, user_input)
        else:
            out = await run_cloud_chat(model, user_input)
    except Exception as e:
        # Fallback: tentar caminho alternativo
        if route=="local" and CLOUD_KEY:
            model_fallback = "gpt-5-mini" if judge["domain"]=="docs" else "gpt-5-codex"
            out = await run_cloud_chat(model_fallback, user_input)
            route = "cloud"
            model = model_fallback
        elif route=="cloud":
            out = await run_local_ollama(LOCAL_CHAT if judge["domain"]=="docs" else LOCAL_CODE, user_input)
            route = "local"
            model = LOCAL_CHAT if judge["domain"]=="docs" else LOCAL_CODE
        else:
            raise e

    return {
        "output":[{"content":[{"type":"output_text","text":out}]}],
        "meta":{"domain":judge["domain"],"complexity":judge["complexity"],"tokens":tokens,"model":model,"route":route,"judge_used":judge_used}
    }
