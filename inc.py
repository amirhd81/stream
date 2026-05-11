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
SPLIT_SIZE = "90m"
ARCHIVE_NAME = "video_archive"

def run(cmd, cwd=None):
    """Run a shell command safely."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def split_rar():
    """Split the downloaded video into RAR parts."""
    print(f"📦 Splitting into {SPLIT_SIZE} parts...")
    
    # run(f"mkdir {DOWNLOAD_DIR}")
    # run(f"mv video.mp4 {os.path.join(DOWNLOAD_DIR)}")

    

    video_path = os.path.join(DOWNLOAD_DIR, "video.mp4")
    if not os.path.exists(video_path):
        # Fallback in case the extension wasn't mp4 despite merge_output_format
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith("video.")]
        if not files:
            print("Error: Downloaded video file not found.")
            sys.exit(1)
        video_path = os.path.join(DOWNLOAD_DIR, files[0])

    # Create split archive inside the download folder
    # Note: Using {os.path.basename(video_path)} ensures we target the right file
    target_file = os.path.basename(video_path)
    run(f"rar a -v{SPLIT_SIZE} -m0 {ARCHIVE_NAME}.rar \"{target_file}\"", cwd=DOWNLOAD_DIR)

    # Collect created archive parts
    parts = sorted(
        f for f in os.listdir(DOWNLOAD_DIR)
        if f.startswith(ARCHIVE_NAME) and f.endswith(".rar") or ".r" in f
    )

    # Remove original video after archiving
    os.remove(video_path)

    return parts


# def split_rar():
#     print("📦 Splitting into 90MB parts...")

#     archive_name = "video_archive"

#     run(f"mv video.mp4 /download")
#     run(f"cd download")
#     run(f"rar a -v{SPLIT_SIZE} -m0 {archive_name}.rar video.mp4")

#     parts = [f for f in os.listdir() if f.startswith("video_archive")]
#     run(f"rm -rf video.mp4")
#     return parts

def git_push_in_batches(files, batch_size=10, delay=8):
    print("📤 Starting batch upload to GitHub...")

    # Configure git once
    run("git config pack.windowMemory 10m")
    run("git config pack.packSizeLimit 20m")
    run("git config pack.threads 1")

    # Process files in chunks
    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        print(f"--- Processing batch {i//batch_size + 1}: {len(batch)} files ---")

        # Add the batch of files
        for f in batch:
            run(f"git add \"{f}\"", cwd=DOWNLOAD_DIR)

        # Commit and Push
        run('git commit -m "upload video parts batch"')
        run('git push origin master')

        # Add artificial delay to allow memory/VPS resources to settle
        if i + batch_size < len(files):
            print(f"⏳ Waiting {delay} seconds for memory to clear...")
            time.sleep(delay)

    print("✅ All batches uploaded successfully.")

def drive(files, batch_size=10, delay=8):
    print("📤 Starting batch upload to GitHub...")

    for f in files:
        run(f"rclone --bind 0.0.0.0 copy -P \"{f}\" gdrive:/vps", cwd=DOWNLOAD_DIR)

    
    print("✅ All batches uploaded successfully.")


async def main(url, password):
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

    # cookies = {
    #     "OptanonConsent": "isGpcEnabled=0&datestamp=Fri+May+01+2026+08%3A53%3A11+GMT%2B0000+(Coordinated+Universal+Time)&version=202506.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=590b7acd-4659-4339-90cf-4f19745f6055&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fstreamable.com%2Fri37ps&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A0%2CC0004%3A0",
    #     "session": "MOMXVE2X12K",
    # }

    # with open("div.html", "r", encoding="utf-8") as f:
    #     html_text = f.read()

    # pattern = r'<source[^>]+src="([^"]+)"'

    # match = re.search(pattern, str(html_text))


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

    # parts = split_rar()
    # git_push_in_batches(parts, 10, 8)
    # drive(parts)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python streamable.py <url> <password>")
        sys.exit(1)

    target_url = sys.argv[1]
    password = sys.argv[2]

    asyncio.run(main(target_url, password))
