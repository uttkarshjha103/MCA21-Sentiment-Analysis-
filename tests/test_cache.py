"""
Unit tests for the in-memory TTL cache (Task 10.1).

Validates: Requirements 9.1, 9.3, 9.5
"""
import time
import pytest
from app.core.cache import TTLCache, cached, dashboard_cache, keyword_cache


# ---------------------------------------------------------------------------
# TTLCache unit tests
# ---------------------------------------------------------------------------

class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key1", {"data": 42})
        assert cache.get("key1") == {"data": 42}

    def test_miss_returns_none(self):
        cache = TTLCache(default_ttl=60)
        assert cache.get("nonexistent") is None

    def test_expired_entry_returns_none(self):
        cache = TTLCache(default_ttl=1)
        cache.set("key", "value", ttl=0)  # expires immediately
        # monotonic time has already passed ttl=0
        time.sleep(0.01)
        assert cache.get("key") is None

    def test_ttl_override(self):
        cache = TTLCache(default_ttl=1)
        cache.set("long", "value", ttl=3600)
        assert cache.get("long") == "value"

    def test_delete(self):
        cache = TTLCache(default_ttl=60)
        cache.set("k", "v")
        assert cache.delete("k") is True
        assert cache.get("k") is None
        assert cache.delete("k") is False  # already gone

    def test_clear(self):
        cache = TTLCache(default_ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0
        assert cache.get("a") is None

    def test_invalidate_prefix(self):
        cache = TTLCache(default_ttl=60)
        cache.set("stats:a", 1)
        cache.set("stats:b", 2)
        cache.set("trends:a", 3)
        removed = cache.invalidate_prefix("stats:")
        assert removed == 2
        assert cache.get("stats:a") is None
        assert cache.get("trends:a") == 3

    def test_max_size_eviction(self):
        cache = TTLCache(default_ttl=60, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # should evict oldest
        assert cache.size == 3

    def test_stats_hit_miss(self):
        cache = TTLCache(default_ttl=60)
        cache.set("x", 10)
        cache.get("x")   # hit
        cache.get("y")   # miss
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_purge_expired(self):
        cache = TTLCache(default_ttl=60)
        cache.set("live", "v", ttl=3600)
        cache.set("dead", "v", ttl=0)
        time.sleep(0.01)
        removed = cache.purge_expired()
        assert removed == 1
        assert cache.get("live") == "v"

    def test_thread_safety(self):
        """Multiple threads writing/reading should not corrupt state."""
        import threading
        cache = TTLCache(default_ttl=60, max_size=1000)
        errors = []

        def writer(n):
            try:
                for i in range(50):
                    cache.set(f"key_{n}_{i}", i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors


# ---------------------------------------------------------------------------
# Module-level singleton sanity checks
# ---------------------------------------------------------------------------

def test_dashboard_cache_singleton():
    dashboard_cache.clear()
    dashboard_cache.set("test", 99)
    assert dashboard_cache.get("test") == 99
    dashboard_cache.clear()


def test_keyword_cache_singleton():
    keyword_cache.clear()
    keyword_cache.set("wc", ["word1", "word2"])
    assert keyword_cache.get("wc") == ["word1", "word2"]
    keyword_cache.clear()


# ---------------------------------------------------------------------------
# cached() decorator test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cached_decorator():
    call_count = 0
    test_cache = TTLCache(default_ttl=60)

    @cached(test_cache, key_fn=lambda x: f"fn:{x}")
    async def expensive(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    result1 = await expensive(5)
    result2 = await expensive(5)  # should be cached
    result3 = await expensive(6)  # different key

    assert result1 == 10
    assert result2 == 10
    assert result3 == 12
    assert call_count == 2  # only 2 actual calls (5 and 6)
