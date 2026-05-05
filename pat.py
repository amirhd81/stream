import time
import yt_dlp
import sys
import subprocess
import os

# Configuration
DOWNLOAD_DIR = "download"
SPLIT_SIZE = "90m"
ARCHIVE_NAME = "video_archive"

def run(cmd, cwd=None):
    """Run a shell command safely."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def setup_env():
    """Ensure download directory exists."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(url, height):
    """Download the video using yt-dlp with IPv4 forced and specific resolution."""
    print(f"📥 Starting download at {height}p...")

    # if (height == "360p" or height == "480" or height == "720") {
    #     format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
    # } else {
    #     # Construct the format string dynamically
    #     # It tries to find the best video at that height, and merges with best audio
    #     format_str = height
    # }

    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    # run(f"yt-dlp -4 --add-header 'Referer: https://www.patreon.com/' --downloader [m3u8]aria2c --downloader-args aria2c:-x:16:-k:1M:-4  -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' {url}")
    run(f"yt-dlp -4 --add-header 'Referer: https://www.patreon.com/' --merge-output-format 'mp4' -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' {url}")


def split_rar():
    """Split the downloaded video into RAR parts."""
    print(f"📦 Splitting into {SPLIT_SIZE} parts...")

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

def git_push(files):
    """Commit the split archive parts to git."""
    print(f"📤 Adding {len(files)} parts to Git...")

    # Git memory optimizations for small VPS
    run("git config pack.windowMemory 10m")
    run("git config pack.packSizeLimit 20m")
    run("git config pack.threads 1")

    # Add only the created archive parts
    for f in files:
        run(f"git add \"{os.path.join(DOWNLOAD_DIR, f)}\"")

    run('git commit -m "upload video parts"')
    print("✅ Files committed. You can now run `git push` manually or add it to the script.")

def main(url, height):
    setup_env()
    download_video(url, height)
    # parts = split_rar()
    # git_push_in_batches(parts, 10, 8)

if __name__ == "__main__": 
    main("https://host.patreaction.com/stream.m3u8?token=NTN6ZVdYc3dDdmY5d0FYRFBpNWs0Zz09Oi9GMEVZOWpnaUlGdzV2UVJObjhkb0Y2anBENmVyM3E4dWV1VDRhczE5T3pReVZjdUM4K0VYNG1iWFJpNGM1MFNBUi83elBqNnpKZUFnT1M0cUhVVkJEM0lwdmlibWJSOWxMWGZoTmREd3BlOWxLTWoxeEw5YmUrRzlGbTRWVTV6UUJyZ2Q3WTZaZ3FvWnJyVUZpV29yT2FyZUJzMjFJRms5UmVuTHd4eFhKNUxiQU5jUGh2dyttanY5TkhueXdOR2FWK2R5LzZiQ21WbW5DWGJwRnNkY2VYbEUvRW4xQ2JMUkRxYXAxOEJxTkF6c3pDNzBKalJSMmJsWkI0azF2OU1PMTFraDFJQU5aOWMybTh3dWxqaWxFSkdDVUxXOGFOalRvTENzdHNkRTJkd0NRbmZXd0txcU95VkMreVQ2U1UyYjQ1a0JPYWZFMEhmS2VPQkJ0cnpuWE1LNHRpMXArUkMrUTFpMnV0N1hKalhPMUxTNGhvcFNiVlZLbS9FVlhyRlAzQ2wzMU8wMDRYQk9IU2krRVVYbGZkZ0cyN1EzajVuTW15dzBSb2JBcnVhbm1ZaytzZzd6OWI4KytiNzlGaHMyeGFobGNWenlqM3NyY0pRQ1pBbEhObkN4dHcvR28xL2VPRnh0SXdtU3d5b2Y5d2ZRV1JSVkcxQzBxQUs2NkNIU0hHU2w3NmtISDFaaWx5UzBIajRoTmtkZ1lhVENobEhpaXlWb3FmbHdaZ3BCU3JZZ2w1eEFIK2ZRTk1mcldmVm4zMXQ4TTZac3FmdXpEci92K0dQbmszVWtFVTRFU21KMDR3YTJhS09TbHlLZkN4SENMbnp5TlZjM2pRdndLUjBwbUx5NWxlTkFHTnZLYUx2Z3dBTU1vQXpSc2plUit2MHZhOXp2czZSUVVIYTkyQmR1Nm5VbDFYbU5YR05MRVVMOGVGdnl2cXNzZ3l4R1lPWFBsQ1hmS2dSbG1WR1VkNVI0bzdxMjNOSUVlOHNVNUNXd1pNaFFzNHJiRWJURlRmbFdmTUI2LzNYb2tRcFl0MzZINnRjQUxDcm5RR3B6UTJpTC96ZndMKzV2akFSMzZVQTVnRHRCSWZUZUhDempTOHpRc2pkOFE0WFczMiszeWJKTDlESW51cmdZdStzVjN5TmxFbXNKOHRKSGJRRE43SEg4U28zQjlMY3pUV0pRb3c3OXgveUh6S255ZWlscEQvTXlBeXU5NjBEdEpOd2d1RmFqUElnMEMvV2NWaWp5SDhTS0NpMi9zRElyN2Y3eG5KTnN3aWNUbDR2YWxQUlJHc1A2OExsMjdpWkVzUFVvYUhTNzM2STFYWEEzRHRiTi9xbGprenQxOXFDb2piY3V6U0s&quality=medium", "480")
