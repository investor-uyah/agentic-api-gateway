import asyncio
import time

cache = {}
in_flight = {}
locks = {}


def get_lock(key):
    if key not in locks:
        locks[key] = asyncio.Lock()
    return locks[key]


async def get_or_wait(key):
    entry = cache.get(key)

    if entry:
        # check expiry dynamically
        if entry["expires_at"] > time.time():
            return entry["data"]
        else:
            # expired → remove
            del cache[key]

    # if request already in progress → wait for it
    if key in in_flight:
        return await in_flight[key]

    return None


async def set_in_flight(key, coro):
    task = asyncio.create_task(coro)
    in_flight[key] = task
    return task


async def store_result(key, result, ttl):
    cache[key] = {
        "data": result,
        "expires_at": time.time() + ttl
    }
    in_flight.pop(key, None)