import json
from fastapi.testclient import TestClient

# idempotency_key: test-route-preview-v1; timeout: 10s; retries: 3

from app import app


def _assert_shape(j):
    assert 'route' in j and j['route'] in ('local', 'cloud')
    assert 'model' in j and j['model'] in (
        'qwen3-14b', 'gpt-5-codex', 'gpt-5-high', 'gpt-5-mini', 'qwen3-8b'
    )
    assert 'rationale' in j and isinstance(j['rationale'], str)
    ce = j.get('cost_estimate')
    assert isinstance(ce, dict)
    assert ce.get('unit') == 'usd'
    assert isinstance(ce.get('prompt_tokens'), int)
    assert ce.get('completion_tokens') == 0
    assert isinstance(ce.get('total'), float)


def test_preview_code_local():
    c = TestClient(app)
    r = c.get('/v1/route/preview', params={'kind': 'code', 'tokens': 300})
    assert r.status_code == 200
    j = r.json()
    assert j['route'] == 'local'
    _assert_shape(j)


def test_preview_docs_cloud():
    c = TestClient(app)
    r = c.get('/v1/route/preview', params={'kind': 'docs', 'tokens': 3500})
    assert r.status_code == 200
    j = r.json()
    assert j['route'] == 'cloud'
    _assert_shape(j)

