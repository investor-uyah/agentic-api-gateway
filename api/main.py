from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
from proxy import handle_request
from metrics import get_metrics, ensure_service
from config import get_service_from_token, TARGET_API
from fastapi.responses import FileResponse

app = FastAPI()

for service in TARGET_API.keys():
    ensure_service(service)

@app.get("/")
async def get_dashboard():
    return FileResponse("dashboard.html")

@app.get("/v1/{service:path}")
async def gateway(service: str, request: Request):
    params = dict(request.query_params)
    return await handle_request(service, params)

@app.get("/metrics")
async def metrics_endpoint(x_api_token: str = Header(None)):
    service = get_service_from_token(x_api_token)

    if not service:
        raise HTTPException(status_code=401, detail="Invalid token")

    data = get_metrics()

    service_data = data["services"].get(service, {})

    summary = {
        "Inbound API Requests": service_data.get("requests", 0),
        "Cache Hits": service_data.get("hits", 0),
        "Cache Misses": service_data.get("misses", 0),
        "SWR Served": service_data.get("swr", 0),
        "Errors": service_data.get("errors", 0),
    }

    return {
        "service": service,
        "data": service_data,
        "summary": summary,          # ✅ now scoped
        "avg_latency": data["avg_latency"]  # (optional: still global)
    }

# @app.get("/dashboard", response_class=HTMLResponse)
# async def dashboard():
#     with open("dashboard.html") as f:
#         return f.read()