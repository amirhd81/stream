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

    run(f"curl -H 'Referer: https://ln5.sync.com/' '{url}'")
    

    # run(f"yt-dlp -4 --add-header 'Referer: https://www.patreon.com/' --downloader [m3u8]aria2c --downloader-args aria2c:-x:16:-k:1M:-4  -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' {url}")
    # run(f"yt-dlp -4 --add-header 'Referer: https://ln5.sync.com/' -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' '{url}'")


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
    main("https://m218.syncusercontent1.com/mfs-60:6686d36ad98209359e991b67fc6fc8d4=============================/p/Wake%20Up%20Dead%20Man%20A%20Knives%20Out%20Mystery%20(2025)%20UNCUT.mp4?allowdd=0&datakey=YBSRFI0PdgKwHaNrLplPdO4XQbLPlEe0Uiimsd9t1+xW8JAPcueVeFA+dR7LynLRrm1ZqvmUpTGlNYs/SBTRIHhY9IeUusC0rgGkqGbBj+cW8hAvET4yOYk1TdlTF1HIskl7INI/0bPPc2GJulzPZuIL5U/puWZQ4589A8zaSIFB5Hbq/pdJwT7umrPvPlA9TrvhSUa/hBnwi7YRxLLgrh6jVYHiPaMeEWeM6geq0vwbuEi1hjHBvamcA5GekL0AquPPmbbcNP2XxKFv6I4fRMMEnZjZsW0v5T1kh1rurAkbXDXi3I0/BYILN/VXZXr/VO4CNAoRastuZHUQEKgHhw&engine=ln-3.1.38&errurl=lH7at6uQT3lJbz1xquf2ACG1xTQ4w5zurWBzzzy2UV9xMwQvxIsk7x9Wj5+05w8eA903dakh3RJcYVizU1eeu9LA2+c1eAdNjGqUKS2jc1xzBmglCCujkLHliHmJY5PxJhZQZ6k0gpT9cg5CADmfbNvkahWRn63kcndiHZ+oDLJ79cFYUDFkJ+1BorjUxeayBUg6TN3DedpiLf00aWvniK56rgEIx05gOQbBU+p7pI/uFbMQ7cv36weca/JymyTj8SWgyQmCvYhacJYi/VkPQaOuIuvO5ga3lsXXqp4ih9fE0BLZwF3nMxDH9aebaBc4SccyJ5dp2SAGlddey6rzOw==&header1=Q29udGVudC1UeXBlOiB2aWRlby9tcDQ&header2=Q29udGVudC1EaXNwb3NpdGlvbjogYXR0YWNobWVudDsgZmlsZW5hbWU9Ildha2UlMjBVcCUyMERlYWQlMjBNYW4lMjBBJTIwS25pdmVzJTIwT3V0JTIwTXlzdGVyeSUyMCgyMDI1KSUyMFVOQ1VULm1wNCI7ZmlsZW5hbWUqPVVURi04JydXYWtlJTIwVXAlMjBEZWFkJTIwTWFuJTIwQSUyMEtuaXZlcyUyME91dCUyME15c3RlcnklMjAoMjAyNSklMjBVTkNVVC5tcDQ7&ipaddress=2380504788&linkcachekey=dba92a010&linkoid=1558830005&mode=101&sharelink_id=32694952190005&timestamp=1778503073088&uagent=95e7d5ee30042362fb746b7f9ddea2007633c4e1&signature=67f8633ea41214ae9e68ac583f1905aad3f5dd2d&cachekey=60:6686d36ad98209359e991b67fc6fc8d4=============================", "480")
