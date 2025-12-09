# Testing Guide

The `ai-router` includes an Enterprise Test Suite located in `tests/`.

## 1. Unit & Semantic Evaluation
Metrics for routing accuracy.
```bash
python3 tests/eval_routing.py
```
*Expectation: >90% Passing.*

## 2. Chaos & Resilience
Tests fallback mechanisms (Blackout, Latency).
```bash
# Requires pytest
pip install pytest
pytest tests/test_chaos.py
```

## 3. Load Testing
Simulates high-traffic scenarios using Locust.
```bash
# Requires locust
pip install locust
locust -f tests/performance/locustfile.py --host http://localhost:8082
```
Access the Locust dashboard at `http://localhost:8089`.

## 4. Manual Smoke Test
```bash
make smoke
```
Or use the "Mission Control" Dashboard at `/guide`.
