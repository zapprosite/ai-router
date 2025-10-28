# PRD — Task Master (Fases)
**F0 Diagnóstico**: mapa do repo, versões, riscos (I/O sem timeout, imports, ausência de HEAD/healthz).  
**F1 Hardening**: timeouts/retries, SLA gate, HEAD /healthz e /guide, fallback seguro.  
**F2 Observabilidade**: logs estruturados + `latency_ms_router`, `resolved_model_id`.  
**F3 Evals**: golden prompts de roteamento (texto curto→Llama, código→DeepSeek, casos ambíguos).  
**F4 V2 Canário**: feature flag `ROUTER_V2=0/1` + canário 10% + rollback.  
**Gate**: cada fase só avança com VERIFY (smoke+evals) e owners se tocar roteamento.
