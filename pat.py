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
    main("https://host.patreaction.com/stream.m3u8?token=REVxVjJlekVWVGtQdmhvOTVveHQ4QT09OjZBcWhjZFA0VTdlM05GL3ZhVVFmLzJic0FSbks2WERPeUZodHZXY2ZXVWVjejd5c2F0V0l3V0NIZGNzRnJBUit3NzJNclcrU2h3Z3FVY0E4K3owaDdDaTUreHMrNDBJMGRvS2dvZTJNSWh2ZldjTS9GVWJvcjBNVExhV0FwSjM4TzZteFRkL2FVbXBsRVZwekh6ZUdZTHpZcW9MdU9heXNmTVV6dG5IeTN6a2t1NGtJK2JCZG0yTk9WMVd5MmdpWlR4cmtjU3NtNVM1Y0Yyb0lJeGRXMUVjUHUyRVl6VVZoeG02TEY3enJKK0pwWXNOY3E0VlMvM1lsRUpDTmt3eCtPb1g5YUhsa0ptWU9jczNkQjQyNDlIbm5rYnBLcjhEZ2ZGVzFnWkZwN0ZaWTI2K3pMR1dVNElycTZTM05xNVdlQmVhbjV6TWltNlJxN0o5RmpYa0dEV2VtNGJ4eWx3b2tIRVJmVnVjSWtzc3pKeno4eGF1Ym5Fd0NXWk93eTNDdE9zT0QwTnc0b2pNeFowUTVDKzBCekNDdTBoaVkzV2pWSEowaTVlenRnU0x3bStqbFo0WUVUUno0ME05aklkazBKc1pUSE85U1grUkRXM3Q4RGdpQ1ZPZXVLZGVyNVJtNjlISFp1NVdodk9ta1p5a0lnNldQN1hNU2dRSWFST3QxcktySWlBNFRVK0pEY2VzK1dWSUY0WS9CQXhzZlRUaEw5VkUyMTJxcWtUODExSVp3S2hvUzZYeGJiNTkwRXVPa1B2QVlaZUt1KzVTcGdtOWF1STM2Z0p5cWhSM3pZSFY3K0ZFaDl1SloxbzNCbUdGRjdyVU5sQ2pPV1RFOGxNUVQ4RTdmMVJQellOMzYza1dFSkFaQTEyZ1U1VzV0eEZnZmlpaWd5SVUvOXdnbjM5OFk5MG4xZTIvQXZ4c3l3aFBKVFBoWDg0RlV1Vi85ZklhMjE1cnN1UlI0SEV4TmRkaERYci9hQWQ0Sys0cVBNK2ZLZVc5M2tucmlJU2pYN21lSzl0djVFdEVLMksrYlY4ekJlcmNGQ3dLTTN0ZjZ6U3lrY1BqSlloVXZyTU8xU3NtYVpGV0lIdU1TL0JzbU4vL3dCOXZlZVpjejd0WVM2aGlJSHRDbjZmL090NWdRemR1YU03M3lzZ05FWU5YMkhmYVY0dWNoMk53N21uTTNqYjY3bUFoV1NWMmczRThtMG5oN0RhbzhHMGZueWhjNVdMR1U4S2k3MnhHWDh4bGszdDI4UjBKUllVSk5WZkx5aXhzQmxOMjI3TVNCQ0ZkTSthRnNOUXEzaFZnYjZyUmdrYWZ6SW9qNEVzdTlROUN1N04rZTgzTWhGdkREanNVOUZaSCs&quality=medium", "480")
