from fastapi import FastAPI, Request
import json

app = FastAPI()


@app.post("/webhook/streamable")
async def telegram_webhook(request: Request):
    update = await request.json()

    pretty = json.dumps(update, indent=2, ensure_ascii=False)

    print(pretty)

    return {
        "ok": True,
        "pretty_update": pretty,
        "raw_update": update
    }
