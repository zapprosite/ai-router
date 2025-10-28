import os
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda


def _needs_reasoning(name: str) -> bool:
    n = (name or "").lower()
    # apply only to the full gpt-5 model ("high"); never to nano/mini/codex
    return n == "gpt-5"


def _is_responses_only(name: str) -> bool:
    n = (name or "").lower()
    return n in ("gpt-5-codex",)


def make_openai(model: str, temperature: float = 0.0):
    key = os.getenv("OPENAI_API_KEY_TIER2") or os.getenv("OPENAI_API_KEY")
    base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
    org = os.getenv("OPENAI_ORGANIZATION") or os.getenv("OPENAI_ORG")
    proj = os.getenv("OPENAI_PROJECT")
    timeout = int(os.getenv("OPENAI_TIMEOUT_SEC", "20"))

    if not key:
        # generate a Runnable that fails to trigger fallbacks without breaking imports
        def _raise(_):
            raise RuntimeError("OpenAI disabled: missing OPENAI_API_KEY")
        return RunnableLambda(_raise)

    # Models that require the Responses API (e.g., gpt-5-codex)
    if _is_responses_only(model):
        from openai import OpenAI
        client = OpenAI(api_key=key, organization=org, base_url=base)
        def _call(payload):
            msgs = payload["messages"]
            text = "\n".join(m.get("content", "") for m in msgs if m.get("role") in ("system", "user"))
            resp = client.responses.create(model=model, input=text)
            # attempt to extract plain text
            try:
                for out in getattr(resp, "output", []) or []:
                    if out.get("type") == "message":
                        for part in out.get("content") or []:
                            if part.get("type") == "output_text":
                                return part.get("text", "")
            except Exception:
                pass
            return str(resp)
        return RunnableLambda(_call)

    headers = {}
    if proj:
        headers["OpenAI-Project"] = proj

    kwargs = dict(
        model=model,
        api_key=key,
        organization=org,
        base_url=base,
        timeout=timeout,
        default_headers=headers or None,
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    )

    # Only include reasoning_effort for gpt-5 ("high") and only if env is valid
    if _needs_reasoning(model):
        eff = (os.getenv("OPENAI_REASONING_EFFORT", "") or "").strip().lower()
        if eff in ("low", "medium", "high"):
            kwargs["reasoning_effort"] = eff
    else:
        # standard chat models: use temperature
        kwargs["temperature"] = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))

    llm = ChatOpenAI(**kwargs)
    to_msgs = RunnableLambda(lambda x: x["messages"])
    to_text = RunnableLambda(lambda m: getattr(m, "content", str(m)))
    return to_msgs | llm | to_text
