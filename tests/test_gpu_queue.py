from unittest.mock import AsyncMock, patch

import pytest

from services.gpu_queue import GpuQueue


@pytest.fixture
def mock_redis():
    # Reset singleton state
    from services.gpu_queue import _queue
    _queue._redis = None
    _queue._enabled = True
    
    with patch("redis.asyncio.from_url") as mock_from_url:
        # Client needs to support pipeline context manager
        client = AsyncMock()
        mock_from_url.return_value = client
        
        # Pipeline mock
        pipeline = AsyncMock()
        client.pipeline.return_value = pipeline
        pipeline.execute.return_value = ["mock_request_id", 1] # Simulate success
        
        yield client
        
        # Teardown
        _queue._redis = None

@pytest.fixture(autouse=True)
def reset_queue():
    from services.gpu_queue import _queue
    _queue._redis = None
    _queue._enabled = True

@pytest.mark.asyncio
async def test_queue_connection(mock_redis):
    q = GpuQueue()
    await q.connect()
    mock_redis.ping.assert_awaited()
    assert q._enabled == True

@pytest.mark.asyncio
async def test_execution_pass_through_when_disabled():
    q = GpuQueue()
    q._enabled = False
    
    async def task(): return "ok"
    
    res = await q.execute_limited(task)
    assert res == "ok"

@pytest.mark.asyncio
async def test_execution_flow_mock(mock_redis):
    q = GpuQueue()
    await q.connect()
    
    # Mock Redis State for success
    # 1. ping -> ok
    # 2. rpush -> ok
    # 3. scard (active count) -> 0 (below max)
    # 4. lindex (head) -> matches our ID
    # 5. Pipeline (lpop, sadd) -> successes
    
    mock_redis.scard.return_value = 0
    
    async def side_effect_lindex(*args):
        # Return the request_id created by execute_limited (which we don't know yet)
        # But we can cheat: if we control logic
        return "MATCH" 
        
    mock_redis.lindex.side_effect = side_effect_lindex
    
    # Needs to match what lindex returns
    with patch("uuid.uuid4", return_value="MATCH"):
        pipeline_mock = mock_redis.pipeline.return_value
        pipeline_mock.execute.return_value = ["MATCH", 1] # lpop result, sadd result
        
        async def real_task(): return "processed"
        
        result = await q.execute_limited(real_task)
        
        assert result == "processed"
        # Verify acquired lock
        mock_redis.rpush.assert_awaited()
        # Verify released lock
        mock_redis.srem.assert_awaited()

@pytest.mark.asyncio
async def test_timeout_logic(mock_redis):
    # Simulate queue ALWAYS full or head blocked
    q = GpuQueue()
    q._redis = None
    q._enabled = True
    await q.connect()
    
    # Override configured timeout logic:
    # We patch time.time to simulate passage of time instantly
    # OR we patch the constant.
    
    # Let's use side_effect on sleep to advance time or break loop
    # But simpler: Patch QUEUE_TIMEOUT to very small, and ensure loop runs at least once
    
    with patch("services.gpu_queue.QUEUE_TIMEOUT", 0.001):
        # Make loop never succeed on logic check
        mock_redis.lindex.return_value = "OTHER_GUY"
        mock_redis.scard.return_value = 0 # Active is low, but head is blocked
        
        async def task(): return "fail"
        
        with pytest.raises(TimeoutError):
            await q.execute_limited(task)
            
        # Verify cleanup
        mock_redis.lrem.assert_awaited()
