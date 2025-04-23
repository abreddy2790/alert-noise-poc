from fastapi import FastAPI, Request
import hashlib, os, json, httpx
import aioredis

app = FastAPI()
redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
CLASSIFY_URL = os.getenv("CLASSIFY_URL")

@app.post("/alerts")
async def receive_alert(request: Request):
    data = await request.json()
    # Normalize fields
    payload = {
        "service": data.get("service"),
        "host": data.get("host"),
        "code": data.get("code"),
        "timestamp": data.get("timestamp"),
        "message": data.get("message")
    }
    # Deduplicate on a 1-min window
    key = f"{payload['service']}:{payload['code']}:{payload['host']}:{int(payload['timestamp'])//60}"
    h = hashlib.sha256(key.encode()).hexdigest()
    if await redis.exists(h):
        return {"status": "deduplicated"}
    await redis.set(h, 1, ex=120)
    # Forward to classification
    async with httpx.AsyncClient() as client:
        await client.post(CLASSIFY_URL, json=payload)
    return {"status": "forwarded"}
