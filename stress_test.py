import asyncio
import httpx
import time

# 1. Configuration
BASE_URL = "http://127.0.0.1:9000"
TEST_TOKEN = "product123"  # Must match the token in your get_service_from_token logic
TOTAL_REQUESTS = 50
NAMES = ["john", "mary", "alex", "mike", "sarah"]

async def make_request(client, i):
    name = NAMES[i % len(NAMES)]
    # 2. Update the URL path to match your Vercel routing
    url = f"{BASE_URL}/v1/genderize?name={name}"
    
    # 3. Add the required Auth Header
    # headers = {"X-API-Token": TEST_TOKEN}

    try:
        start = time.time()
        # Increased timeout for Vercel/Cold Starts
        response = await client.get(url, timeout=20.0)
        duration = time.time() - start

        if response.status_code == 200:
            print(f"Request {i}: ✅ 200 ({duration:.4f}s)")
            return duration
        else:
            print(f"Request {i}: ❌ {response.status_code} ({duration:.4f}s)")
            return 0
    except Exception as e:
        print(f"Request {i} failed: {e}")
        return 0

async def main():
    # Using a single client for connection pooling
    async with httpx.AsyncClient() as client:
        print(f"🚀 Starting stress test against {BASE_URL}...")
        
        tasks = [make_request(client, i) for i in range(TOTAL_REQUESTS)]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    # Filter out failures for the average
    valid_results = [r for r in results if r > 0]
    
    print("\n--- SUMMARY ---")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successful: {len(valid_results)}")
    print(f"Total time: {total_time:.2f}s")
    if valid_results:
        print(f"Avg response time: {sum(valid_results)/len(valid_results):.4f}s")
    print("\nCheck your dashboard for the Live Hit Rate! 📈")

if __name__ == "__main__":
    asyncio.run(main())