from fastapi import FastAPI, Request
import subprocess
import requests
import os
import traceback

app = FastAPI()

PYTHON_BIN = "/root/miniconda3/envs/stream/bin/python"
BASE_DIR = "/root/strem"

def run(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        text=True,
        capture_output=True
    )

    print("RETURN CODE:", result.returncode)
    print("STDOUT:")
    print(result.stdout)

    print("STDERR:")
    print(result.stderr)

    result.check_returncode()

def drive(files, batch_size=10, delay=8):
    print("📤 Starting batch upload to GitHub...")

    for f in files:
        run(f"rclone --bind 0.0.0.0 copy -P \"{f}\" gdrive:/vps", cwd=DOWNLOAD_DIR)

    
    print("✅ All batches uploaded successfully.")
    
def download_video(url, height):
    print(f"📥 Starting download at {height}p...")
    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    output_path = os.path.join('download', "video.%(ext)s")

    print("output:", output_path, flush=True)

    os.makedirs("download", exist_ok=True)

    subprocess.run([
        "/root/miniconda3/envs/stream/bin/yt-dlp",
        "-4",
        "--downloader",
        "[m3u8]/usr/bin/aria2c",
        "--downloader-args",
        "aria2c:-x:16:-k:1M:-4",
        "--merge-output-format",
        "mp4",
        "-f",
        format_str,
        "-o",
        output_path,
        url
    ])

def send_message1(chat_id, text):
    print("ENTERED SEND_MESSAGE", flush=True)

    try:
        r = requests.post(
            "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "reply_markup": {
                    "keyboard": [
                        [
                            {
                                "text": "Youtube",
                            }
                        ]
                    ]
                }
            },
            timeout=30
        )

        print("STATUS:", r.status_code, flush=True)
        print("BODY:", r.text, flush=True)

    except Exception:
        print("SEND MESSAGE FAILED", flush=True)
        traceback.print_exc()


def send_message(chat_id, text):
    try:
        requests.post(
            "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            }
        )

    except Exception as e:
        print(str(e))
        return {
            "ok": False,
            "error": str(e)
        }
        

def download(text, chat_id):
    try:
        parts = text.split()

        command = parts[0]

        if command == "/start":
            print(chat_id)
            send_message1(chat_id, "Use Buttons")
            print(chat_id)

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
