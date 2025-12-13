# ai-router Architecture

## 🧠 The "Autonomous Judge" Logic
The core differentiator of this router is the **Autonomous Judge** (Classifier + Logic). Instead of simple load balancing, it evaluates the *intent* and *expertise* required for each prompt.

```mermaid
flowchart LR
    User[User Prompt] --> Judge{The Autonomous Judge}
    
    Judge -- "Easy / Safe / Code" --> Local[Local GPU (RTX 4090)]
    Judge -- "Critical / ML / Reasoning" --> Cloud[Cloud API (OpenAI)]
    
    subgraph Local [Cost: $0/token]
        DeepSeek[DeepSeek-V2\n(The Engineer)]
        Llama[Llama-3.1\n(The Assistant)]
    end
    
    subgraph Cloud [Cost: $$$]
        O3[O3\n(The Scientist)]
        GPT[GPT-5.2\n(The Writer)]
    end
```

## ⚖️ The Expertise Matrix (Decision Logic)
The Judge selects models based on their verified strengths (Dec 2025):

| Role | Model | Capabilities | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **The Engineer** | `DeepSeek-Coder-V2` (Local) | Python, C++, Refactoring, Algorithms. | Default for `code_gen`, `code_review`. |
| **The Assistant** | `Llama-3.1-8b` (Local) | Chitchat, JSON formatting, Summary. | Default for `simple_qa`, `chitchat`. |
| **The Writer** | `GPT-5.2` (Cloud) | Creative writing, Marketing, Nuance. | `creative_writing`, `research` (High). |
| **The Scientist** | `O3` (Cloud) | Math Proofs, Deadlock Analysis, Security. | `reasoning`, `critical` context. |

## 🛡️ Safety & Cost Guard
- **Cost Guard**: Prevents accidental cloud usage for simple tasks.
- **Privacy**: Local models run 100% offline.
- **Reliability**: If Cloud fails, the router falls back to Local (DeepSeek/Llama).

## ⚙️ Configuration
See `config/router_config.yaml` for:
- Routing Policy Table.
- Model Registry.
- Budget Constraints.
