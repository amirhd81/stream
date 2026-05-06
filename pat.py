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
    main("https://host.patreaction.com/stream.m3u8?token=OXNYcEorT0tOa1JwcE8za1BMNFZ6QT09OlRkZ1hGYStyWG5UeVJLNFZXdmFhUUp1dVRvd0FQRDZuVjM3ejd6QkRJN2FxcXFQeGFaNGEzbTZCaWZnd3U4bGJBU001ZnRWTC9kZjhtNSs2TU9KdXBBNWc3b3BaRjlaMEFLSmQrNWdrQllVc2M2UWMzaWt6YitxWUR3Q21KNlZ1ZHB6YVE5aFRBZ3FxK1o4dnZFMzVESGRISnVsRUtRUlBLdnZNclo2M0c2V1dpcUxYUDBvcmNUZnd2YVM3bjRpWnNGNUh4WlBhYzdzamJYZjlQeFBmc1J3NVhxNC9Hakk3OG9DUzkwMHZvOEhwZ2lpRXIvTnBGMGg5bzRtbFZkd3BHUERXUXVzMFhXdUtRMmtJVWNNR2hLYmNkaHVIL0JVV1FLc05HajFQR01UYVNhd1d2KzRFS1I1RUdXeFdHb0NCOHBjMXVWbEczaGFQWTJjUlJvdnd2Zkx3UGpMVTZJVndCdXNSczNsQUZjZU01Qi90bkdoQzlOZ0ZhSmJkdUZtdnJ4VjZQWkJFKytyV3YyWkJhdG52MmV6WEt1YjRrYzBKbjdyVGQ0QmJoRGxVL2JGOWJrcC9uU1BsN1orQUdheEJhVG5HOUFyVDlCNnNuZHg5TFlrTm1ZdmFzZlZ6cFh0enZWTXo3NjdJMVZHNEpDYVhwazdQOU9sUzYxUlNSRFJVMldEV2Rhc0NubnhvWjB3cnJITDg3MWdCYkxjOWw4NEJlU0lkZzFWT05iYkcrZ2RBZkQyVCt4czQ1T2R2akVLSlZ5THMwMmFaL1kxNmx4TzB5UlBDYTlOK0VTRkRGSXM4Q2Z1SmNEWTVBNHRmNVZhYzBwZzZuZ2hpVWgrZlZkZXZmUUcxc1JjZk1Yd0dWNUpuQjJmMjhQcXpFMjBpdSs1Zk82bHhJSUk4VDJLd01mbmtYZDkrcXhSYlplb21rd0syN2lnaWNlc01HRVJjSkpvQm1IcE1rT0ExckNuaUk0cE83aTVsS212ck1aeTRTZHh4MFNOK3ZIWXJJWS9DMDR2WXI5OU9ZWEdiZ1haNGhZWXZwM2YvRytodFF4bk5UdHJKbXZXZDFGSExuMU02eDBVeVJueFB4S3lsdXZ1VzM1eHR3ZHg0YlJsR1JMRlpNb1BjSVQraGtiWW1HTmQwZlVGYmRwQXJvMzJ5RWFyYk5OSkhCY2pXWURSVWVqOGdJTjZsUUdwYktNMFZOemgrM1FTMUZrS2hoSVIrY282cVk4MnI1RE1XTCtBT1JiVy9nY1VtazcwR0hMTVZSNUZZaFhIZ0N3UU1neTZJdWZqM2VZeW9hOWlneGI4S3hqRWsxZTl4L1NYWGg3UVV3c0R0M09PVUVuL2w2TWtpZC8zbkxFeHY&quality=medium", "480")
