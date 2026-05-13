import sys
import asyncio
import subprocess
import os
from playwright.async_api import async_playwright
import httpx
import re
import html
import datetime
from tqdm import tqdm
import time
import traceback

CHROMIUM_PATH = "/usr/bin/chromium-browser"

def send_message1(chat_id, text):
    try:
        r = requests.post(
            "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=30
        )

    except Exception:
        traceback.print_exc()

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


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python streamable.py <url> <password>")
        sys.exit(1)

    chat_id = sys.argv[1]
    target_url = sys.argv[2]
    password = sys.argv[3]

    print(sys.argv)

    asyncio.run(download_streamable(chat_id, target_url, password))
