import os, requests
from tenacity import retry, stop_after_delay, wait_fixed

def wait_until_healthy(base_url: str, timeout: int | None = None) -> None:
    t = int(os.getenv("WAIT_HEALTH_SECS", "30" if os.getenv("CI") else "60"))
    if timeout is not None: t = timeout
    @retry(stop=stop_after_delay(t), wait=wait_fixed(2), reraise=True)
    def _probe():
        r = requests.get(f"{base_url}/healthz", timeout=3)
        if r.status_code != 200:
            raise RuntimeError(f"healthz status {r.status_code}")
    _probe()
