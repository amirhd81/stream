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

DOWNLOAD_DIR = "download"
CHROMIUM_PATH = "/usr/bin/chromium-browser"

def run(cmd, cwd=None):
    """Run a shell command safely."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)


async def main(chat_id, url):
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

        # Attach listeners
        page.on("request", lambda req: asyncio.create_task(log_request(req)))
        page.on("response", lambda res: asyncio.create_task(log_response(res)))

        await page.wait_for_timeout(5000)

        await page.screenshot(path="page.png", full_page=True)

        if len(matched_urls) > 0:
            print(matched_urls[0])
    
        co = await page.content()
        
        with open("div.html", "w") as f:
            f.write(str(co))

        await browser.close()

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/147.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://ln5.sync.com/"
    }


    if len(matched_urls) > 0:
        download_url = matched_urls[0]


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



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python streamable.py <url> <password>")
        sys.exit(1)

    chat_id = sys.argv[1]
    url = sys.argv[2]

    asyncio.run(main(chat_id, url))
