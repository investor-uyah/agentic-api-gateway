import asyncio
import httpx
import time
#from fastapi import Header

names = ["john", "mary", "alex", "mike", "sarah"]
TOTAL_REQUESTS = 50


async def make_request(client, i):
    name = names[i % len(names)]
    url = f"http://127.0.0.1:9000/agent-gateway/v1/genderize?name={name}"

    start = time.time()
    response = await client.get(url)
    duration = time.time() - start

    print(f"Request {i}: {response.status_code} ({duration:.4f}s)")
    return duration


async def main():
    async with httpx.AsyncClient() as client:
        tasks = [make_request(client, i) for i in range(TOTAL_REQUESTS)]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    print("\n--- SUMMARY ---")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Avg response time: {sum(results)/len(results):.4f}s")


if __name__ == "__main__":
    asyncio.run(main())