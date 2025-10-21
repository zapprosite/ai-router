/**
 * idempotency_key: k6-models-2025-10-21-v1
 * Mede p95 e taxa de erro do GET /v1/models enquanto /v1/responses não existe.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';

export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{ep:models}': ['p(95)<1200']
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/v1/models`, { tags: { ep: 'models' }, timeout: '10s' });
  check(res, {
    '200': (r) => r.status === 200,
    'tem data': (r) => {
      try { return Array.isArray(r.json().data); } catch { return false; }
    }
  });
  sleep(0.2);
}
