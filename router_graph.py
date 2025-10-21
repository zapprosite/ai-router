from typing import List, Dict
def get_models() -> List[Dict]:
    return [{"id": m} for m in ["qwen3-8b","qwen3-14b","gpt-5-nano","gpt-5-mini","gpt-5-codex","gpt-5-high"]]
