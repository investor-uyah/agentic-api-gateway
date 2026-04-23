import httpx
import time
import asyncio
from api.config import TARGET_API, get_service_from_token
from api.cache import get_or_wait, set_in_flight, store_result, get_lock, in_flight, cache
from api.metrics import record_request, record_hit, record_miss, record_swr, record_error, record_latency

client = httpx.AsyncClient()

async def fetch_from_api(url, params):
    # Clean params (don't send internal token to target API)
    api_params = {k: v for k, v in params.items() if k != "token"}
    response = await client.get(url, params=api_params, timeout=10.0)
    return response.json()

async def handle_request(service, params):
    start_time = time.time()

    target = TARGET_API.get(service)
    if not target:
        return {"status": "error", "message": "Service not supported"}

    record_request(service)

    try:
        url = target["base_url"]
        strategy = target.get("cache_strategy", "ttl")
        ttl = target.get("ttl", 60)
        key = f"{service}:{str(sorted(params.items()))}"

        # ----------------------------
        # 1. NO CACHE
        # ----------------------------
        if strategy == "no_cache":
            data = await safe_fetch(url, params)
            record_miss(service)
            return data

        # ----------------------------
        # 2. CHECK CACHE (single entry point)
        # ----------------------------
        entry = cache.get(key)

        # ---- CACHE HIT (TTL or SWR base) ----
        if entry:
            # SWR handling (only here — no duplicate paths)
            if strategy == "swr":
                lock = get_lock(key)

                if not lock.locked() and key not in in_flight:
                    async def refresh():
                        async with lock:
                            try:
                                data = await safe_fetch(url, params)
                                await store_result(key, data, ttl)
                            except:
                                record_error(service)

                    asyncio.create_task(refresh())

                record_hit(service)
                record_swr(service)
                return entry["data"]

            # Normal TTL hit
            record_hit(service)
            return entry["data"]

        # ----------------------------
        # 3. CACHE MISS (single path)
        # ----------------------------
        lock = get_lock(key)

        async with lock:
            # Double-check cache after acquiring lock
            entry = cache.get(key)
            if entry:
                record_hit(service)
                return entry["data"]

            # True miss — fetch + store
            data = await safe_fetch(url, params)
            await store_result(key, data, ttl)

            record_miss(service)
            return data

    except Exception as e:
        record_error(service)
        return {"status": "error", "message": str(e)}

    finally:
        record_latency(time.time() - start_time)


async def safe_fetch(url, params):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, params=params, timeout=20.0)

        content_type = response.headers.get("content-type", "")

        # ✅ Valid JSON
        if "application/json" in content_type:
            try:
                return response.json()
            except Exception:
                return {
                    "status": "error",
                    "message": "Invalid JSON from upstream",
                    "status_code": response.status_code,
                    "preview": response.text[:200]
                }

        # ❌ Not JSON (e.g., login page, HTML, redirect)
        return {
            "status": "error",
            "message": "Upstream did not return JSON",
            "status_code": response.status_code,
            "content_type": content_type,
            "url": str(response.url),
            "preview": response.text[:200]
        }