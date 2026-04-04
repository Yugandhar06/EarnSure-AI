"""
SmartShift+ Redis Cache Layer
Wraps redis-py with automatic fallback to in-memory dict.

Usage:
    from services.cache import cache
    cache.set("zone:Koramangala", score_dict, ttl=900)
    data = cache.get("zone:Koramangala")

If Redis is unavailable (no server, no key), silently falls back to
a thread-safe in-memory dict so the demo NEVER breaks.
"""
import json
import threading
from datetime import datetime, timedelta
from typing import Any, Optional

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Try to connect to Redis ────────────────────────────────────────────────
_redis_client = None
try:
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _r = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
    _r.ping()                           # Test connection
    _redis_client = _r
    print(f"[CACHE] Redis connected at {redis_url}")
except Exception as e:
    print(f"[CACHE] Redis unavailable ({e}) — using in-memory fallback")


# ── In-memory fallback store ───────────────────────────────────────────────
_mem_store: dict = {}
_mem_expiry: dict = {}
_lock = threading.Lock()


class SmartShiftCache:
    """
    Unified cache interface. Automatically uses Redis when available,
    in-memory dict when not. API identical either way.
    """

    def set(self, key: str, value: Any, ttl: int = 900) -> bool:
        """
        Store a value. TTL in seconds (default 900 = 15 min zone refresh cycle).
        Value is JSON-serialised for Redis compatibility.
        """
        try:
            serialised = json.dumps(value)
            if _redis_client:
                return _redis_client.setex(key, ttl, serialised)
            else:
                with _lock:
                    _mem_store[key]  = serialised
                    _mem_expiry[key] = datetime.now() + timedelta(seconds=ttl)
                return True
        except Exception as e:
            print(f"[CACHE] set({key}) error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value. Returns None if missing or expired.
        """
        try:
            if _redis_client:
                raw = _redis_client.get(key)
            else:
                with _lock:
                    if key not in _mem_store:
                        return None
                    if datetime.now() > _mem_expiry.get(key, datetime.min):
                        del _mem_store[key]
                        return None
                    raw = _mem_store[key]
            return json.loads(raw) if raw else None
        except Exception as e:
            print(f"[CACHE] get({key}) error: {e}")
            return None

    def delete(self, key: str) -> bool:
        try:
            if _redis_client:
                return bool(_redis_client.delete(key))
            else:
                with _lock:
                    _mem_store.pop(key, None)
                    _mem_expiry.pop(key, None)
                return True
        except Exception:
            return False

    def is_redis_live(self) -> bool:
        return _redis_client is not None

    def stats(self) -> dict:
        if _redis_client:
            info = _redis_client.info()
            return {"backend": "redis", "keys": _redis_client.dbsize(),
                    "memory": info.get("used_memory_human")}
        else:
            with _lock:
                valid = sum(
                    1 for k in _mem_store
                    if datetime.now() < _mem_expiry.get(k, datetime.min)
                )
            return {"backend": "in-memory", "keys": valid, "memory": "N/A"}


# Singleton instance
cache = SmartShiftCache()

# Zone-specific helpers used by scheduler + score API
ZONE_CACHE_TTL = 900   # 15 minutes

def cache_zone_score(zone_name: str, score_data: dict):
    cache.set(f"zone:{zone_name}", score_data, ttl=ZONE_CACHE_TTL)

def get_cached_zone_score(zone_name: str) -> Optional[dict]:
    return cache.get(f"zone:{zone_name}")

def get_all_cached_zones() -> dict:
    """Returns all cached zone scores. Called by /admin/zone_risk."""
    zones = {}
    zone_names = [
        "Koramangala", "HSR Layout", "JP Nagar", "Indiranagar",
        "Whitefield", "Malleshwaram", "Marathahalli", "Yelahanka", "Electronic City"
    ]
    for z in zone_names:
        cached = get_cached_zone_score(z)
        if cached:
            zones[z] = cached
    return zones
