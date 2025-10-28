# EVALS — Roteamento e sanidade

Valida se o roteador mantém local‑first e escolhe o modelo correto (Llama vs DeepSeek), com fallback de nuvem apenas quando necessário.

## Métricas alvo
- Acerto de roteamento ≥ 95% nos prompts de ouro.
- p95 de latência local < SLA configurado.
- Sem regressões após mudanças (gate de CI local).

## Prompts de ouro (mínimo viável)
1) Texto curto → Llama local  
   Input: “Explique HVAC em 1 frase.”  
   Esperado: `model_id == "llama-3.1-8b-instruct"`

2) Código explícito → DeepSeek local  
   Input: “Escreva uma função Python soma(n1,n2) com docstring.” com `prefer_code=true`  
   Esperado: `model_id == "deepseek-coder-v2-16b"`

3) Ruído de código (pistas) → DeepSeek local  
   Input: “Corrija o traceback: ValueError… ```python def foo(x): return x*2 ```”  
   Esperado: `model_id == "deepseek-coder-v2-16b"`

## Execução

- Smokes: `make smoke`.
- Runner de evals (gera relatório em `.reports/evals.out`):
```bash
make evals
```
- Script direto (matriz de modelos, opcional):
```bash
scripts/TEST_MODELS.py | python3 -m json.tool
```

Pré‑requisitos: serviço ativo em 8082; `jq` instalado.

## Interpretação e aprovação

- Esperado “PASS” em todos os casos (ou justificativa com evidências de ambiente/SLA).
- Com fallback ON, o runner registra o modelo escolhido; ainda esperamos local na maioria das execuções.
- Regressões de p95 ou escolhas incorretas de modelo devem bloquear merge até correção.

