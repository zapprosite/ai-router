#!/usr/bin/env python3
import sys
from router_contract import route_headers, format_header

def demo():
    code_prompt = """
Please implement and test:

```python
def sum_two(a: int, b: int) -> int:
    return a + b
```
""".strip()
    docs_prompt = """
Explique brevemente os benefícios de Prompt Caching em APIs de IA.
""".strip()

    for name, p in [("code", code_prompt), ("docs", docs_prompt)]:
        h = route_headers(p)
        print(f"{name}: {format_header(h)}")

if __name__ == "__main__":
    demo()
