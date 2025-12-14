import asyncio
import logging
import os
import time
import uuid

import redis.asyncio as redis

logger = logging.getLogger("ai-router.gpu-queue")

# Config from Env
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MAX_WORKERS = int(os.getenv("GPU_QUEUE_MAX_WORKERS", "1"))
QUEUE_TIMEOUT = int(os.getenv("GPU_QUEUE_TIMEOUT", "60"))

# Check if queue should be enabled (only if Redis URL is set)
ENABLED = bool(os.getenv("REDIS_URL") or os.getenv("GPU_QUEUE_ENABLED"))

class GpuQueue:
    def __init__(self):
        self._redis = None
        self._enabled = ENABLED

    async def connect(self):
        if not self._enabled:
            return
        if not self._redis:
            self._redis = redis.from_url(REDIS_URL, decode_responses=True)
            try:
                await self._redis.ping()
                logger.info(f"Connected to Redis at {REDIS_URL}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis queue: {e}. Queue disabled logic.")
                self._enabled = False

    async def close(self):
        if self._redis:
            await self._redis.close()

    async def execute_limited(self, func, *args, **kwargs):
        """
        Executes an async function ensuring max concurrency on GPU.
        If Disabled or Redis fail, runs immediately (fallback).
        """
        if not self._enabled or not self._redis:
            return await func(*args, **kwargs)

        request_id = str(uuid.uuid4())
        queue_key = "gpu:queue"
        active_key = "gpu:active"
        
        t0 = time.time()
        
        # 1. Enqueue
        # We push to list to maintain order
        await self._redis.rpush(queue_key, request_id)
        logger.info(f"Enqueued request {request_id[:8]}. Waiting for slot...")

        try:
            # 2. Wait for Slot
            while True:
                # Check timeout
                if time.time() - t0 > QUEUE_TIMEOUT:
                    await self._redis.lrem(queue_key, 0, request_id)
                    raise TimeoutError(f"GPU Queue Timeout ({QUEUE_TIMEOUT}s)")

                # Try to move from Queue to Active
                # We need atomic check: Count(Active) < Max
                # Simplified Pattern:
                # Watch active set? No, just poll count.
                # Improvement: Lua script for atomic move if count < max.
                
                active_count = await self._redis.scard(active_key)
                
                # Check if we are at head of queue?
                # Strictly FIFO: Check if LINDEX 0 is us.
                head = await self._redis.lindex(queue_key, 0)
                
                if head == request_id and active_count < MAX_WORKERS:
                    # Atomic move attempts
                    # We pop us from List and add to Set
                    # Use pipeline
                    pipe = self._redis.pipeline()
                    pipe.lpop(queue_key)
                    pipe.sadd(active_key, request_id)
                    results = await pipe.execute()
                    
                    if results[0] == request_id:
                        # Success: We consumed ourselves from head
                        logger.info(f"Acquired GPU slot for {request_id[:8]} (Active: {active_count+1}/{MAX_WORKERS})")
                        break
                    else:
                        # Race condition or logic flip, retry loop
                        pass
                
                # Backoff wait
                await asyncio.sleep(0.5)

            # 3. Execute
            try:
                return await func(*args, **kwargs)
            finally:
                # 4. Release
                await self._redis.srem(active_key, request_id)
                logger.info(f"Released GPU slot for {request_id[:8]}")

        except Exception as e:
            # Cleanup if we crashed during wait
            await self._redis.lrem(queue_key, 0, request_id)
            await self._redis.srem(active_key, request_id)
            raise e

    async def get_metrics(self):
        """Returns queue depth and active workers."""
        if not self._enabled or not self._redis:
            return {"enabled": False}
        
        queue_len = await self._redis.llen("gpu:queue")
        active_count = await self._redis.scard("gpu:active")
        return {
            "enabled": True,
            "queue_depth": queue_len,
            "active_workers": active_count,
            "max_workers": MAX_WORKERS
        }

# Validating singleton
_queue = GpuQueue()

async def get_queue() -> GpuQueue:
    if _queue._redis is None:
        await _queue.connect()
    return _queue

# Helper for wrapping logic
async def run_on_gpu(func, *args, **kwargs):
    q = await get_queue()
    return await q.execute_limited(func, *args, **kwargs)
