from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.gpu_queue import GpuQueue


# We need a robust mock for the Redis client that supports await
@pytest.fixture
def mock_redis():
    # redis.asyncio client is an object with async methods.
    # checking manual: client.pipeline() is SYNC, returns pipeline object.
    # calls like client.ping() are ASYNC.
    
    client = MagicMock()
    
    # Async methods
    client.ping = AsyncMock(return_value=True)
    client.rpush = AsyncMock()
    client.lrem = AsyncMock()
    client.scard = AsyncMock()
    client.lindex = AsyncMock()
    client.srem = AsyncMock()
    client.sadd = AsyncMock() # Used if not piping? No, pipe uses it.
    client.close = AsyncMock()
    
    # Pipeline construction is SYNC
    pipeline = MagicMock()
    # Pipeline buffering is SYNC
    pipeline.lpop = MagicMock()
    pipeline.sadd = MagicMock()
    # Pipeline execution is ASYNC
    pipeline.execute = AsyncMock(return_value=["MATCH", 1])
    
    client.pipeline.return_value = pipeline

    return client

@pytest.fixture
def clean_singleton():
    # Reset singleton state before/after
    from services.gpu_queue import _queue
    old_redis = _queue._redis
    old_enabled = _queue._enabled
    
    _queue._redis = None
    _queue._enabled = True # Reset to default expectation
    
    yield
    
    _queue._redis = old_redis
    _queue._enabled = old_enabled

@pytest.mark.asyncio
async def test_queue_connection(mock_redis, clean_singleton):
    # Patch the redis.from_url to return our mock client
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        q = GpuQueue()
        # Force enabled to True initially to test connection logic
        q._enabled = True
        await q.connect()
        
        # Should call ping
        mock_redis.ping.assert_awaited()
        # Should remain enabled
        assert q._enabled == True

@pytest.mark.asyncio
async def test_connection_failure_disables_queue(clean_singleton):
    # Simulate ping failure
    bad_client = AsyncMock()
    bad_client.ping.side_effect = Exception("Connection Refused")
    
    with patch("redis.asyncio.from_url", return_value=bad_client):
        q = GpuQueue()
        q._enabled = True
        await q.connect()
        
        # Should act disabled now
        assert q._enabled == False

@pytest.mark.asyncio
async def test_execution_pass_through_when_disabled(clean_singleton):
    q = GpuQueue()
    q._enabled = False
    
    async def task(x): return x * 2
    
    # Should run immediately without redis calls
    res = await q.execute_limited(task, 10)
    assert res == 20

@pytest.mark.asyncio
async def test_execution_flow_mock(mock_redis, clean_singleton):
    # Full flow test
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        q = GpuQueue()
        q._enabled = True
        await q.connect()
        
        # Setup Redis replies for success path:
        # 1. ping (already set in fixture)
        # 2. rpush -> (anything)
        # 3. scard (active count) -> 0 (allow entry)
        # 4. lindex (head) -> matches "MATCH"
        # 5. pipeline.execute -> ["MATCH", 1] (success move)
        
        mock_redis.scard.return_value = 0
        
        # We need lindex to match the UUID generated inside.
        # So we patch UUID
        with patch("uuid.uuid4", return_value="MATCH"):
             mock_redis.lindex.return_value = "MATCH"
             
             # Pipeline returns match
             pipeline = mock_redis.pipeline.return_value
             pipeline.execute.return_value = ["MATCH", 1]
             
             async def real_task(): return "processed"
             
             result = await q.execute_limited(real_task)
             
             assert result == "processed"
             
             # Verify logic flow
             mock_redis.rpush.assert_awaited_with("gpu:queue", "MATCH")
             mock_redis.srem.assert_awaited_with("gpu:active", "MATCH")

@pytest.mark.asyncio
async def test_timeout_logic(mock_redis, clean_singleton):
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        q = GpuQueue()
        q._enabled = True
        await q.connect()
        
        # Force timeout by making queue check fail forever (until timeout)
        mock_redis.scard.return_value = 100 # FULL
        
        # Speed up the test by patching QUEUE_TIMEOUT
        with patch("services.gpu_queue.QUEUE_TIMEOUT", 0.001):
            async def task(): return "fail"
            
            with pytest.raises(TimeoutError):
                await q.execute_limited(task)
            
            # Should clean up queue
            mock_redis.lrem.assert_awaited()
