from fastapi import FastAPI, Request
import subprocess
import requests
import os
import traceback

app = FastAPI()

PYTHON_BIN = "/root/miniconda3/envs/stream/bin/python"
BASE_DIR = "/root/strem"
DOWNLOAD_DIR = "download"
SPLIT_SIZE = "90m"
ARCHIVE_NAME = "video_archive"

def send_message1(chat_id, text):
    try:
        r = requests.post(
            "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
                # "reply_markup": {
                #     "keyboard": [
                #         [
                #             {
                #                 "text": "Youtube",
                #             }
                #         ]
                #     ]
                # }
            },
            timeout=30
        )

    except Exception:
        traceback.print_exc()

def run(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        cwd=cwd,
    )

    print("RETURN CODE:", result.returncode)
    print("STDOUT:")
    print(result.stdout)

    print("STDERR:")
    print(result.stderr)

    result.check_returncode()

def drive(files, chat_id):
    send_message1(chat_id, "Starting upload to drive")

    for f in files:
        run([
            "rclone",
            "--bind 0.0.0.0",
            "copy -P",
            f,
            "gdrive:/vps"
        ], cwd=DOWNLOAD_DIR)

    send_message1(chat_id, "All files uploaded successfully.")


def split_rar(chat_id):
    send_message1(chat_id, f"Splitting into {SPLIT_SIZE} parts...")

    video_path = os.path.join(DOWNLOAD_DIR, "video.mp4")
    
    if not os.path.exists(video_path):

        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith("video.")]
        if not files:
            send_message1(chat_id, "Error: Downloaded video file not found.")
            sys.exit(1)
        video_path = os.path.join(DOWNLOAD_DIR, files[0])

    target_file = os.path.basename(video_path)

    size = f"-v{SPLIT_SIZE}"

    rar_name = f"{ARCHIVE_NAME}.rar"

    run([
        "rar",
        "a",
        size,
        "-m0",
        rar_name,
        target_file
    ], cwd=DOWNLOAD_DIR)

    parts = sorted(
        f for f in os.listdir(DOWNLOAD_DIR)
        if f.startswith(ARCHIVE_NAME) and f.endswith(".rar") or ".r" in f
    )

    os.remove(video_path)

    return parts


async def download_streamable(chat_id, url, password):
    logfile = open("network_log.txt", "w", encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True
        )
        page = await browser.new_page()

        await page.goto(url, wait_until="domcontentloaded")

        async def log_request(request):
            timestamp = datetime.datetime.now().isoformat()
            line = f"[{timestamp}] REQUEST: {request.method} {request.url}\n"
            logfile.write(line)

        async def log_response(response):
            timestamp = datetime.datetime.now().isoformat()
            line = f"[{timestamp}] RESPONSE: {response.status} {response.url}\n"
            logfile.write(line)

        page.on("request", lambda req: asyncio.create_task(log_request(req)))
        page.on("response", lambda res: asyncio.create_task(log_response(res)))

        await page.fill('form[name="video-password"] input[name="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)
        html_text = await page.inner_html("div.svp-desktop-player")
        await page.screenshot(path="page.png", full_page=True)
        await browser.close()

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/147.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://streamable.com"
    }

    cookies = {
        "OptanonConsent": "isGpcEnabled=0&datestamp=Fri+May+01+2026+08%3A53%3A11+GMT%2B0000+(Coordinated+Universal+Time)&version=202506.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=590b7acd-4659-4339-90cf-4f19745f6055&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fstreamable.com%2Fri37ps&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A0%2CC0004%3A0",
        "session": "MOMXVE2X12K",
    }

    pattern = r'<source[^>]+src="([^"]+)"'

    match = re.search(pattern, str(html_text))

    download_url = html.unescape(match.group(1))

    send_message1(chat_id, "Starting download")

    with httpx.stream("GET", download_url, headers=headers, cookies=cookies) as r:
        r.raise_for_status()

        total = int(r.headers.get("content-length", 0))
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        video_path = os.path.join(DOWNLOAD_DIR, "video.mp4")

        with open(video_path, "wb") as f, tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading",
        ) as progress:

            for chunk in r.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                f.write(chunk)
                progress.update(len(chunk))


async def download_inc(chat_id, url):
    matched_urls = []
    logfile = open("network_log.txt", "w", encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROMIUM_PATH,
            headless=True
        )
        page = await browser.new_page()

        await page.goto(url, wait_until="domcontentloaded")

        async def log_request(request):
            if request.url.startswith("https://m218.syncusercontent1.com/mfs-60"):
                timestamp = datetime.datetime.now().isoformat()
                line = f"[{timestamp}] REQUEST: {request.method} {request.url}\n"
                logfile.write(line)
                matched_urls.append(request.url)
            timestamp = datetime.datetime.now().isoformat()
            line = f"[{timestamp}] REQUEST: {request.method} {request.url}\n"
            logfile.write(line)

        async def log_response(response):
            timestamp = datetime.datetime.now().isoformat()
            line = f"[{timestamp}] RESPONSE: {response.status} {response.url}\n"
            logfile.write(line)

        page.on("request", lambda req: asyncio.create_task(log_request(req)))
        page.on("response", lambda res: asyncio.create_task(log_response(res)))

        await page.wait_for_timeout(5000)

        await page.screenshot(path="page.png", full_page=True)

        if len(matched_urls) > 0:
            print(matched_urls[0])

        await browser.close()

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/147.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://ln5.sync.com/"
    }


    if len(matched_urls) > 0:
        download_url = matched_urls[0]

    send_message1(chat_id, "Starting download")

    with httpx.stream("GET", download_url, headers=headers) as r:
        r.raise_for_status()

        total = int(r.headers.get("content-length", 0))
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        video_path = os.path.join(DOWNLOAD_DIR, "video.mp4")

        with open(video_path, "wb") as f, tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading",
        ) as progress:

            for chunk in r.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                f.write(chunk)
                progress.update(len(chunk))


    
def download_yt(chat_id, url, height):
    send_message1(chat_id, f"Starting download at {height}p...")
    
    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    output_path = os.path.join(DOWNLOAD_DIR, "video.%(ext)s")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

            download_yt(chat_id, url, quality)

            parts = split_rar(chat_id)

            drive(parts, chat_id)
        
            sendMessage(chat_id, "Download success")

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

            download_streamable(chat_id, url, password)

            parts = split_rar(chat_id)

            drive(parts, chat_id)
        
            sendMessage(chat_id, "Download success")

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

            download_inc(chat_id, url)

            parts = split_rar(chat_id)

            drive(parts, chat_id)
        
            sendMessage(chat_id, "Download success")
            
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
