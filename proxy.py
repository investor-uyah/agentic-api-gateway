import httpx
import time
import asyncio
from config import TARGET_API, get_service_from_token
from cache import get_or_wait, set_in_flight, store_result, get_lock, in_flight, cache
from metrics import record_request, record_hit, record_miss, record_swr, record_error, record_latency

client = httpx.AsyncClient()

async def fetch_from_api(url, params):
    # Clean params (don't send internal token to target API)
    api_params = {k: v for k, v in params.items() if k != "token"}
    response = await client.get(url, params=api_params, timeout=10.0)
    return response.json()

async def handle_request(service, params):
    start_time = time.time()
    
    # --- SECURITY CHECK ---
    target = TARGET_API.get(service)

    if not target:
        return {"status": "error", "message": "Service not supported"}

    record_request(service)

    try:
        url = target["base_url"]
        strategy = target.get("cache_strategy", "ttl")
        ttl = target.get("ttl", 60)
        key = f"{service}:{str(sorted(params.items()))}"

        # 1. NO CACHE
        if strategy == "no_cache":
            record_miss(service)
            return await fetch_from_api(url, params)

        # 2. CACHE HIT
        entry = await get_or_wait(key)
        if entry:
            record_hit(service)
            return entry

        # 3. SWR (Background Refresh)
        if strategy == "swr":
            cached = cache.get(key)
            if cached:
                lock = get_lock(key)
                if not lock.locked() and key not in in_flight:
                    async def refresh():
                        async with lock:
                            try:
                                data = await fetch_from_api(url, params)
                                await store_result(key, data, ttl)
                            except: record_error(service)
                    asyncio.create_task(refresh())
                record_hit(service)
                record_swr(service)
                return cached["data"]

        # 4. COLD START / TTL
        lock = get_lock(key)
        async with lock:
            entry = await get_or_wait(key)
            if entry: return entry

            async def task():
                data = await fetch_from_api(url, params)
                await store_result(key, data, ttl)
                record_miss(service)
                return data
            
            task_obj = await set_in_flight(key, task())
            return await task_obj

    except Exception as e:
        record_error(service)
        return {"status": "error", "message": str(e)}
    finally:
        record_latency(time.time() - start_time)