import time
from collections import defaultdict

metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "swr_served": 0,
    "errors": 0,
}

# Standardized service structure
service_metrics = defaultdict(lambda: {
    "requests": 0,
    "hits": 0,
    "misses": 0,
    "swr": 0,
    "errors": 0
})

latencies = []

def ensure_service(service):
    if service not in service_metrics:
        _ = service_metrics[service]

def record_request(service):
    metrics["total_requests"] += 1
    ensure_service(service)
    service_metrics[service]["requests"] += 1

def record_hit(service):
    metrics["cache_hits"] += 1
    service_metrics[service]["hits"] += 1

def record_miss(service):
    metrics["cache_misses"] += 1
    service_metrics[service]["misses"] += 1

def record_swr(service):
    metrics["swr_served"] += 1
    service_metrics[service]["swr"] += 1

def record_error(service=None):
    metrics["errors"] += 1
    if service:
        service_metrics[service]["errors"] += 1

def record_latency(duration):
    latencies.append(duration)

def get_metrics():
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    return {
        "summary": {
            "Inbound API Requests": metrics["total_requests"],
            "Cache Hits": metrics["cache_hits"],
            "Cache Misses": metrics["cache_misses"],
            "SWR Served": metrics["swr_served"],
            "Errors": metrics["errors"],
        },
        "services": dict(service_metrics),
        "avg_latency": round(avg_latency, 4),
        "total_samples": len(latencies)
    }