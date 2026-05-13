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

    # run(f"curl -L -H 'Referer: https://ln5.sync.com/' -O '{url}'")
    

    run(f"yt-dlp -4 --add-header 'Referer: https://www.patreon.com/' --downloader [m3u8]aria2c --downloader-args aria2c:-x:16:-k:1M:-4  -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' {url}")
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
    parts = split_rar()
    # git_push_in_batches(parts, 10, 8)

if __name__ == "__main__": 
    main("https://host.patreaction.com/stream.m3u8?token=MWhMWitpNzk0czJSMm44OThaRGR5dz09Ono0aWFKbDRudWY5a3IwY3pqdnJKUS9QdmVTZENscy9kb25rdkNYc0R2ajlmazM4QzNxWEJxQ3o0ZE1xaTk0NVhDRlBOM3FaeUJYNzRwbW5ST1ByZGgvV0FjSXJDUTlnVXFpR1RzQ0JmT05HcWhEdnhUQXV0dUUvMXduc20xaTgvRnRCRkpwanJzQXBodkgxS3ZvbWVzZWRXYnAvc3BBRU9BLzBwbVU0R3VJZWord1FXUnpkTVhBeGJUaTY1MVgvV1V5bTUwNSsvdEVCVitvL0FxN0pLRmNPVDhEdDNPb0pTYkI2T2JQNFJOaTlyTFpRbkZwM1BJT2JQSk5Pdy9iNGlDQVlHZVRjckdxcEs0U3ZaRSt5aVVVSHBhTHYzc1o1QitSNGxkdzI5K3RRaGp6U1E4ZUx1MTFpWDgzNlFmbVhIckwxekQ3WE1jU3d6eUh6RW5OaXVZbE1VZkRGdU10OUVlbVBybjQxSnIyTU93cUxXcXhMSFlNYlRWNmRsOGMxMmR5YTVnVGE0MXZPT3E2K3FOY243L0dvWVAwVDMycTVGWVlkQnN0Y2p4cEV4aG5id095QzZIcXVRMDM4dHoyRHROUFpieDlnc3lRTlBvNk5IaGExWitXRWl3SU0wbkY5andlVDZNbzBYZU1XUlp2RnJqU3RuU0xJZW9OZVZkT3luYlpqU0RMcFViYm5wcWJGeXN4cmJhOHE4bFZzQjBONkZDb0FiTllPanNhOFVUMmhQZFNxQnZJVEdEbVJ5L1ZZdUVSaGhoVDhNVzhzT254c05tY3pYK2JFYW5sTzc2Tm8xamdpN29waU5MYy9hTUFyK2JySldHVVZaQ2RmOU9DMzZoUkFaZjdRKzFidzdobDFLSk9yYW1qdXZNUDF1MC9FK21UcHRZQ2Zkb2FPbE9ETVE4aWNULzdPL2lPUDhkNnpJZ0dsRlVodDFIU1lqTmJlV0NZZ1llL0c3QlF0Ny9LajNlRG5kRGVFNFFUcDlSWS80Ulh5K1d1WVpNV0p2VDA1eXRGeUl2cFdlUzlnazY5d2FneFNHMnkzTGZZS3JpY2o2NjVMbS90dDQ2S2NzQ3RnNGFGdURsdXBkOUhsNWRHNGw0VWtUK1pzMG5nMitIVEVvSU5YQmlKRnRWcm5JWTliR0VtV1NUR1RKdEw3bVhMR0lKRzNrdERHcDRBRm5DUGNsWENFZTFrMkI2Mk1OeW1MaG0vdWdLdEZoS0hsNWYrNXc2VVMwTEJPb3d0Y0FkVm10WUM5ZlZ1RklDT0sxanNBR1FleGg1NFdsb0N1d2Naenp0OFYzeHloQmhvcmcxWEhUVWVNNDhOcVZpVVNSSkZvbTIwNXB0SW1GSjFOMmRVLzk&quality=medium", "480")
