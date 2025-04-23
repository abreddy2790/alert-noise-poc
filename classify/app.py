from fastapi import FastAPI, Request
import os, httpx

app = FastAPI()
GPT_URL = os.getenv("GPT_URL")
GPT_KEY = os.getenv("GPT_KEY")
CORRELATE_URL = os.getenv("CORRELATE_URL")
HEADERS = {"Authorization": f"Bearer {GPT_KEY}"}

@app.post("/classify")
async def classify_alert(request: Request):
    data = await request.json()
    prompt = f"Classify this alert as NOISE or ACTIONABLE: {data}"
    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.post(GPT_URL, json={"prompt": prompt}, headers=HEADERS)
        result = res.json()
    decision = result.get("decision")
    confidence = result.get("confidence", 0)
    if decision == "ACTIONABLE" and confidence >= 0.6:
        await client.post(CORRELATE_URL, json={**data, "confidence": confidence})
        return {"status": "forwarded", "confidence": confidence}
    return {"status": "suppressed", "confidence": confidence}
