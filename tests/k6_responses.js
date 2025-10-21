/**
 * idempotency_key: k6-responses-cloud-2025-10-21-v1
 * Objetivo: medir latência e taxa de erro do endpoint OpenAI-compatible /v1/responses.
 * Requisitos:
 *  - Router exposto em http://localhost:8082 (governança: porta 8082). 
 *  - CLOUD_ENABLED=true e chaves válidas no /srv-2/secrets/ai-stack/ai-stack.env.
 *  - Modelo default: gpt-5-codex (pode sobrescrever via K6_MODEL).
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';
const MODEL    = __ENV.K6_MODEL || 'gpt-5-codex';

// Carga curta e estável: 10 VUs por 30s. Alvo p95 < 1200 ms e erro < 1%.
export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],                // <1% falhas
    'http_req_duration{ep:responses}': ['p(95)<1200'] // p95 < 1200 ms
  },
};

export default function () {
  const url = `${BASE_URL}/v1/responses`;
  const payload = JSON.stringify({
    model: MODEL,
    input: "ping"
  });
  const params = {
    headers: { 'Content-Type': 'application/json' },
    tags: { ep: 'responses' }
  };

  const res = http.post(url, payload, params);

  const ok = check(res, {
    'status 200': (r) => r.status === 200,
    'tem output': (r) => {
      try {
        const j = r.json();
        return j && (j.output_text || j.output || j.choices);
      } catch { return false; }
    },
  });

  // respiro leve para evitar sincronização de picos
  sleep(0.2);
}
