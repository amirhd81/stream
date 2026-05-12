from fastapi import FastAPI, Request
import subprocess
import requests

app = FastAPI()

PYTHON_BIN = "/root/miniconda3/envs/stream/bin/python"
BASE_DIR = "/root/strem"

def run(cmd, cwd=None):
    """Run a shell command safely."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def download_video(url, height):
    print(f"📥 Starting download at {height}p...")
    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    run(f"yt-dlp -4 --downloader [m3u8]aria2c --downloader-args aria2c:-x:16:-k:1M:-4   --merge-output-format 'mp4' -f '{format_str}' -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' '{url}'")


def send_message(chat_id, text):
    requests.post(
        "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        }
    )

def download(text, chat_id):
    try:
        parts = text.split()

        command = parts[0]

        # ----------------------------------------
        # /search
        # ----------------------------------------

        if command == "/search":

            if len(parts) < 3:
                send_message(chat_id, "Invalid search command")
                return {"ok": False}

            search_type = parts[1]

            # ------------------------------------
            # global search
            # ------------------------------------

            if search_type == "global":

                query = " ".join(parts[2:])

                result = subprocess.run(
                    [
                        PYTHON_BIN,
                        "ytSearch.py",
                        "global",
                        query
                    ],
                    capture_output=True,
                    text=True
                )

                send_message(chat_id, result.stdout[:4000])

            # ------------------------------------
            # uploads
            # ------------------------------------

            elif search_type == "uploads":

                if len(parts) < 3:
                    send_message(chat_id, "Usage: /search uploads <channel_url>")
                    return {"ok": False}
                

                channel_url = f"https://www.youtube.com/@{parts[2]}"

                result = subprocess.run(
                    [
                        PYTHON_BIN,
                        "ytSearch.py",
                        "uploads",
                        channel_url
                    ],
                    capture_output=True,
                    text=True
                )

                send_message(chat_id, result.stdout[:4000])

            # ------------------------------------
            # channel search
            # ------------------------------------

            elif search_type == "channel":

                if len(parts) < 4:
                    send_message(chat_id, "Usage: /search channel <channel_url> <query>")
                    return {"ok": False}

                channel_url = f"https://www.youtube.com/@{parts[2]}"
                query = " ".join(parts[3:])

                result = subprocess.run(
                    [
                        PYTHON_BIN,
                        "ytSearch.py",
                        "channel",
                        channel_url,
                        query
                    ],
                    capture_output=True,
                    text=True
                )

                send_message(chat_id, result.stdout[:4000])

            else:
                send_message(chat_id, "Unknown search type")

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

            download_video(url, quality)

            # subprocess.run([PYTHON_BIN, f"{BASE_DIR}/dl.py", url, quality])

            sendMessage(chat_id, f"url: {url}")

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

            subprocess.Popen(
                [
                    PYTHON_BIN,
                    f"{BASE_DIR}/get.py",
                    url,
                    password
                ], 
                capture_output=True,
                text=True
            )

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

            subprocess.Popen(
                [
                    PYTHON_BIN,
                    f"{BASE_DIR}/inc.py",
                    url
                ], 
                capture_output=True,
                text=True
            )
            
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
        send_message(str(e), chat_id)
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
    chat_id = message.get("chat", {}).get("id")

    if not text:
        return {
            "ok": False,
            "error": "No text found"
        }

    download(text, chat_id)
