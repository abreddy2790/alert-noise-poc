from fastapi import FastAPI, Request
import os, json
import aioredis
import httpx

app = FastAPI()
redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
CORRELATION_THRESHOLD = int(os.getenv("CORRELATION_THRESHOLD", 3))

@app.post("/correlate")
async def correlate(request: Request):
    data = await request.json()
    key = f"{data['service']}:{data['code']}"
    # Buffer alerts in Redis
    await redis.rpush(key, json.dumps(data))
    await redis.expire(key, 120)
    count = await redis.llen(key)
    if count >= CORRELATION_THRESHOLD:
        items = await redis.lrange(key, 0, -1)
        await redis.delete(key)
        hosts = list({json.loads(item)["host"] for item in items})
        summary = f"{count}× {data['service']} {data['code']} on {len(hosts)} hosts"
        card = {"body": {"contentType": "html", "content": summary}}
        async with httpx.AsyncClient() as client:
            await client.post(TEAMS_WEBHOOK_URL, json=card)
        return {"status": "notified", "count": count}
    return {"status": "buffered", "count": count}
