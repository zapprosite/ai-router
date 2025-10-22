/**
 * idempotency_key: k6-metrics-200-2025-10-21-v1
 * timeout: 10s
 * retries: 3
 * Simple scrape to ensure /metrics returns 200.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8082';

export const options = {
  vus: 1,
  duration: '10s',
};

export default function () {
  const res = http.get(`${BASE_URL}/metrics`, { timeout: '10s', tags: { ep: 'metrics' } });
  check(res, {
    'status 200': (r) => r.status === 200,
    'text content': (r) => (r.headers['Content-Type'] || '').includes('text/plain'),
  });
  sleep(0.5);
}

