import redis
import logging
import os
import time
import uuid

logger = logging.getLogger(__name__)


class RedisStockLock:
    """Redis distributed lock for stock management.
    Prevents race conditions during concurrent stock updates.
    """

    def __init__(self):
        self.client = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'redis'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
        )
        self.lock_timeout = 10  # seconds

    def acquire_lock(self, product_id, timeout=10):
        """Acquire a distributed lock for a product."""
        lock_key = f'stock_lock:{product_id}'
        lock_value = str(uuid.uuid4())
        end_time = time.time() + timeout

        while time.time() < end_time:
            if self.client.set(lock_key, lock_value, nx=True, ex=self.lock_timeout):
                return lock_value
            time.sleep(0.01)

        logger.warning(f'Failed to acquire lock for product {product_id}')
        return None

    def release_lock(self, product_id, lock_value):
        """Release a distributed lock."""
        lock_key = f'stock_lock:{product_id}'
        pipe = self.client.pipeline(True)
        try:
            pipe.watch(lock_key)
            if pipe.get(lock_key) == lock_value:
                pipe.multi()
                pipe.delete(lock_key)
                pipe.execute()
                return True
        except redis.WatchError:
            pass
        return False

    def get_stock_cache(self, product_id):
        """Get cached stock from Redis."""
        key = f'stock:{product_id}'
        value = self.client.get(key)
        return int(value) if value else None

    def set_stock_cache(self, product_id, quantity, ttl=300):
        """Cache stock quantity in Redis."""
        key = f'stock:{product_id}'
        self.client.setex(key, ttl, quantity)

    def invalidate_stock_cache(self, product_id):
        """Invalidate stock cache."""
        key = f'stock:{product_id}'
        self.client.delete(key)

    # --- Temporary Lock Counting Methods ---

    def lock_stock(self, product_id, quantity=1):
        """Increment the temporary locked stock for a product."""
        key = f'product_locked:{product_id}'
        return self.client.incrby(key, quantity)

    def release_lock(self, product_id, quantity=1):
        """Decrement the temporary locked stock for a product (e.g. on cancel)."""
        key = f'product_locked:{product_id}'
        # Don't let it go below 0 ideally
        current = self.client.decrby(key, quantity)
        if current < 0:
            self.client.set(key, 0)
            return 0
        return current

    def get_locked_stock(self, product_id):
        """Get the current locked stock quantity."""
        key = f'product_locked:{product_id}'
        val = self.client.get(key)
        return int(val) if val else 0
