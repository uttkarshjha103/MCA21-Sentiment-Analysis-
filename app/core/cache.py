"""
In-memory cache with TTL support for frequent queries.
No external dependencies required (uses functools.lru_cache and threading).

Validates: Requirements 9.1, 9.3, 9.5
"""
import time
import threading
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Simple thread-safe in-memory cache with per-entry TTL support.

    Usage::

        cache = TTLCache(default_ttl=300)  # 5-minute default TTL

        # Store a value
        cache.set("my_key", {"data": 42}, ttl=60)

        # Retrieve a value (returns None if missing or expired)
        value = cache.get("my_key")

        # Delete a specific key
        cache.delete("my_key")

        # Clear all entries
        cache.clear()
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Args:
            default_ttl: Default time-to-live in seconds (default 5 minutes).
            max_size: Maximum number of entries before LRU eviction (default 1000).
        """
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry_ts)
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Return cached value or None if missing/expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expiry = entry
            if time.monotonic() > expiry:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store *value* under *key* with an optional TTL override."""
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.monotonic() + ttl
        with self._lock:
            # Evict oldest entry if at capacity
            if len(self._store) >= self.max_size and key not in self._store:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """Remove a key. Returns True if the key existed."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        """Remove all cached entries."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all keys that start with *prefix*. Returns count removed."""
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._store[k]
            return len(keys_to_remove)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Current number of (possibly expired) entries."""
        return len(self._store)

    def stats(self) -> dict:
        """Return cache hit/miss statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "size": self.size,
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
        }

    def purge_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
            return len(expired)


# ---------------------------------------------------------------------------
# Module-level singleton caches
# ---------------------------------------------------------------------------

# Dashboard aggregation cache – 5-minute TTL
dashboard_cache = TTLCache(default_ttl=300, max_size=500)

# Keyword / word-cloud cache – 10-minute TTL
keyword_cache = TTLCache(default_ttl=600, max_size=200)


# ---------------------------------------------------------------------------
# Decorator helpers
# ---------------------------------------------------------------------------

def cached(cache: TTLCache, key_fn: Callable[..., str], ttl: Optional[int] = None):
    """
    Decorator that caches the return value of an *async* function.

    Args:
        cache: The TTLCache instance to use.
        key_fn: A callable that receives the same ``*args, **kwargs`` as the
                decorated function and returns a string cache key.
        ttl: Optional TTL override in seconds.

    Example::

        @cached(dashboard_cache, key_fn=lambda self, **kw: f"stats:{kw}", ttl=120)
        async def get_stats(self, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {key}")
                return cached_value
            logger.debug(f"Cache MISS: {key}")
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
