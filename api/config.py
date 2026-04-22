# manually update json with user target info details

TARGET_API = {
    "genderize": {
        "base_url": "https://api.genderize.io",
        "method": "GET",
        "cache_strategy": "swr",
        "ttl": 60,
        "token": "product129"
    },
    "agify": {
        "base_url": "https://api.agify.io",
        "method": "GET",
        "cache_strategy": "ttl",
        "ttl": 10,
        "token": "product124"
    },
    "crypto-prices": {
        "base_url": "https://api.crypto.com",
        "method": "GET",
        "cache_strategy": "no_cache",
        "token": "product125"
    },
    "price-store": {
        "base_url": "https://price-store.xyz/api/price-estimate/",
        "method": "GET",
        "cache_strategy": "swr",
        "ttl": 60,
        "token": "auth"

    }
}

# v2 API structure

# "mfon": {
#         "password": "product123",
#         "services": {
#             "products": {
#                 "base_url": "https://.../products",
#                 "cache_strategy": "ttl",
#                 "ttl": 60
#             },
#             "prices": {
#                 "base_url": "https://.../prices",
#                 "cache_strategy": "swr",
#                 "ttl": 30
#             }
#         }
#     }

def get_service_from_token(token):
    for service, config in TARGET_API.items():
        if config.get("token") == token:
            return service
    return None