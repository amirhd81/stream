from fastapi import FastAPI, Request
import subprocess
import json
import shlex

app = FastAPI()

PYTHON_BIN = "/root/miniconda3/envs/stream/bin/python"
BASE_DIR = "/root/strem"

def download(text):
    try:
        parts = shlex.split(text)

        command = parts[0]

        # -----------------------------
        # /yt URL QUALITY
        # -----------------------------
        if command == "/yt":

            if len(parts) != 3:
                return {
                    "ok": False,
                    "usage": "/yt <url> <360|480|720>"
                }

            url = parts[1]
            quality = parts[2]

            subprocess.Popen([
                PYTHON_BIN,
                f"{BASE_DIR}/dl.py",
                url,
                quality
            ])

            return {
                "ok": True,
                "action": "youtube",
                "url": url,
                "quality": quality
            }

        # -----------------------------
        # /stream URL PASSWORD
        # -----------------------------
        elif command == "/stream":

            if len(parts) != 3:
                return {
                    "ok": False,
                    "usage": "/stream <url> <password>"
                }

            url = parts[1]
            password = parts[2]

            subprocess.Popen([
                PYTHON_BIN,
                f"{BASE_DIR}/get.py",
                url,
                password
            ])

            return {
                "ok": True,
                "action": "streamable",
                "url": url
            }

        # -----------------------------
        # /inc URL
        # -----------------------------
        elif command == "/inc":

            if len(parts) != 2:
                return {
                    "ok": False,
                    "usage": "/inc <url>"
                }

            url = parts[1]

            subprocess.Popen([
                PYTHON_BIN,
                f"{BASE_DIR}/inc.py",
                url
            ])

            return {
                "ok": True,
                "action": "inc",
                "url": url
            }

        else:
            return {
                "ok": False,
                "error": "Unknown command"
            }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

@app.post("/webhook/streamable")
async def telegram_webhook(request: Request):
    update = await request.json()

    # print(json.dumps(update, indent=2, ensure_ascii=False))

    message = update.get("message", {})
    text = message.get("text", "").strip()

    if not text:
        return {
            "ok": False,
            "error": "No text found"
        }

    download(text)
