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
    parts = split_rar()
    git_push_in_batches(parts, 10, 8)

if __name__ == "__main__": 
    main("https://host.patreaction.com/stream.m3u8?token=OTZ1OHNBT1FrNExsTTdjaXNWTHQvZz09OlczbGFmSnhZTEVGaytzSnlCTnJFQy90SXljLzRZNWhMQ1RxRGdleGRzVk1CQW1VY3NJbUhlMnp2TTVHbjNBOUxzalNSYXhkdm95cFVwU05rcDI1c3hORFJTMFZKTFM2REliZFVoMFdnVk5ILzJLckgvWUVDNThtdGo2T2F6L294VnBBV2JRVFhaSnFpaGVJYU9xeXo0VTNGN3ZyY3FLM0ErZFArNGpiVlNITENQL3BidTFLdFNYeG10SEVHY24rNyt1Wmx2YTVaOEdPTytoWk03Q3pubVc4dnBkRTlzS0hFS1NHYVpKdDFmemNqQ3FUMHljRVRsa2cydTU5ZlZpY3BWenRTRFlrcXl4LzJmZWEvWC8vcUUveWc0bEpSb2NrcnZRZk9MSmNxdGt2dUNvM3NaWHJjc1pkWi9HZXpSZlhhMlNYZ001eFRaTkpDRml2R2s5REhsUnZWdzlNa25wd2pKcThXWFlVQ3dYdnI5VXpsd2hVbEhuV1pJWFRVeXhzdWpmL2tNRG1QUTZPS2tXOVVIY3ljZ2hIYmNnK0tkS1lBRWVlQkkvOHRxdlFzYVdMRGNvWHVGWmYxZUJMalh2RG1QV1RXRjI4YkZYZG05M3dtWGZwbk1LMUloSGhZeHNwTll0eWwvVG03RG5ta0lWZnZwb3ZhMGs1ZXZZdHJmc1c3OGplYm5JT1lweGNKQzh2U2VxYjRFYmxQK1FKV3hFOGVkWmJvajZvRW1XTEtrUHByc1hSNWZjTHAvZjY4c1o4VlNhWnBBVzhkNzZhSXpJWE1tMXZ3RWJIVjR5cmNsaFJWS0hzTHZRck92R2lMOHpsdEtMTWFJNTZWMFdyWFlRWW5EVWtZRnQ3RVpJZFJydXRybHN6VVhyNXcwUzJnZ3J0N2wwN3dsZGpqVm9UNW1QREcxQzZlNG9PODFsRFNXYVJGcnQ4aGRaUUVRMDlVZnRhRmtpQ1dJNGtXREUwUllqZmhUbVIxMWF3emN6blVZcVBjSlAzazRZU1dUM1laN1hPRllqNGx4Zk1lVkUrSngzZUFzVmREOHVibE5Tb0t1aCtpdXd3UldlRSswVVk1QzZXYzJ4UVlZcTVLOWZBTUtXK2JRUVJqMmRRc1lIMkw3NjVJVG1yd3BVYUdHdHJheFlYZHpSY3A5cnFGc0pXSVhhcTdlMlNXWURWYWM5RmJaWVM1UUJsbGJ0ZGt1SHhzSVhSVVNhQTAwSUZOR21URHdxUjB2ODRFUUNZMUNNc0M2Ly9YUG9zcGt1MXg4eVFsWjU4UGpNaGtQQ0djbGM3VmRzanJweTMzUVArWUk5SWtOdGFNYWo1T2tMd0wvZm9FT2hzRmJqWDltN1ZzdlpaTFVTOW8&quality=medium", "480")
