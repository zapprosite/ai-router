import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    healthz: { executor: "constant-arrival-rate", rate: 15, timeUnit: "1s", duration: "30s", preAllocatedVUs: 10, maxVUs: 50, exec: "healthz" },
    models:  { executor: "constant-arrival-rate", rate: 10, timeUnit: "1s", duration: "30s", preAllocatedVUs: 10, maxVUs: 50, exec: "models" },
  },
  thresholds: {
    "http_req_duration{scenario:healthz}": ["p(95)<300"],
    "http_req_duration{scenario:models}":  ["p(95)<300"],
    checks: ["rate>0.99"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8082";

export function healthz() {
  const res = http.get(BASE_URL + "/healthz", { timeout: "3s" });
  check(res, { "status 200": r => r.status === 200, "ok true": r => r.json("ok") === true });
}

export function models() {
  const res = http.get(BASE_URL + "/v1/models", { timeout: "5s" });
  check(res, { "status 200": r => r.status === 200, "data list": r => Array.isArray(r.json("data")) });
}
