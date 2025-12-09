"""
AsyncIO Load Test Suite
Validates router performance under high concurrency (50-100 RPS).
Target: Ensure router overhead is <200ms (excluding LLM latency).
"""
import asyncio
import time
import httpx
import pytest
import statistics
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("load-test")

BASE_URL = "http://localhost:8082"
CONCURRENCY = 50
TOTAL_REQUESTS = 200

async def make_request(client, req_id):
    """Make a single request to the routing decision endpoint."""
    prompt = f"Load test request {req_id}: Write a sorting function."
    start = time.perf_counter()
    try:
        # We hit the debug endpoint to measure pure routing overhead
        resp = await client.post(f"{BASE_URL}/debug/router_decision", json={"prompt": prompt})
        resp.raise_for_status()
        latency = (time.perf_counter() - start) * 1000  # ms
        return {"status": "ok", "latency": latency}
    except Exception as e:
        logger.error(f"Req {req_id} failed: {e}")
        return {"status": "error", "latency": 0}

@pytest.mark.asyncio
async def test_router_overhead_under_load():
    """
    Simulate multiple concurrent users hitting the decision engine.
    Pass condition: P95 Latency < 200ms, Error Rate < 1%.
    """
    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from unittest.mock import patch

    # Mock the LLM classifier to avoid 401 retries and test pure router logic latency
    with patch("graph.router.classify_prompt_with_llm") as mock_llm:
        # Mock result irrelevant as heuristic should likely take over, 
        # or we return a dummy compatible with RoutingMeta if called
        from graph.router import RoutingMeta
        mock_llm.return_value = RoutingMeta(task="simple_qa", complexity="low", confidence=1.0)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Warmup
            await client.get("/healthz")

            tasks = []
            for i in range(TOTAL_REQUESTS):
                tasks.append(make_request(client, i))
            
            # Run concurrent batch
            results = await asyncio.gather(*tasks)
        
    # Analysis
    latencies = [r["latency"] for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] == "error"]
    
    if not latencies:
        pytest.fail("All requests failed.")
    
    p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile approximation
    p50 = statistics.median(latencies)
    error_rate = len(errors) / TOTAL_REQUESTS
    
    logger.info(f"Load Test Results: N={TOTAL_REQUESTS}, Concurrency={CONCURRENCY}")
    logger.info(f"P95 Latency: {p95:.2f}ms")
    logger.info(f"P50 Latency: {p50:.2f}ms")
    logger.info(f"Error Rate: {error_rate*100:.1f}%")
    
    # Assertions for "Professional" Grade
    assert error_rate < 0.01, f"Error rate too high: {error_rate:.2%}"
    # 200ms is generous for pure routing logic (usually <50ms), but includes network/overhead
    assert p95 < 200, f"P95 latency too high: {p95:.2f}ms"
