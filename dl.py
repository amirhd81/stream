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

def drive(files, batch_size=10, delay=8):
    print("📤 Starting batch upload to GitHub...")

    for f in files:
        run(f"rclone --bind 0.0.0.0 copy -P \"{f}\" gdrive:/vps", cwd=DOWNLOAD_DIR)

    
    print("✅ All batches uploaded successfully.")

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

    # run(f"yt-dlp -4 --downloader [m3u8]aria2c --downloader-args aria2c:-x:16:-k:1M:-4   --merge-output-format 'mp4' -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' {url}")
    run(f"yt-dlp -4 --downloader [m3u8]aria2c --downloader-args aria2c:-x:16:-k:1M:-4   --merge-output-format 'mp4' -f '{format_str}' -o '{os.path.join(DOWNLOAD_DIR, "video.%(ext)s")}' '{url}'")

    # opts = {
    #     "format": format_str,
    #     "merge_output_format": "mp4",
    #     "outtmpl": os.path.join(DOWNLOAD_DIR, "video.%(ext)s"),
        
    #     # Force IPv4
    #     "force_ipv4": True,
        
    #     # External Downloader (aria2c) with -4
    #     # "external_downloader": "aria2c",
    #     # "external_downloader_args": [
    #     #     "-x", "16", 
    #     #     "-k", "1M", 
    #     #     "-4"  # Force IPv4 for aria2c
    #     # ],
    #     "quiet": False,
    # }

    # with yt_dlp.YoutubeDL(opts) as ydl:
    #     info = ydl.extract_info(url, download=True)
    #     filename = ydl.prepare_filename(info)

    # print(f"✅ Downloaded: {filename}")
    # return filename

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
    drive(parts)
    # git_push_in_batches(parts, 10, 8)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python streamable.py <url> [resolution]")
        print("Example: python streamable.py https://youtube.com/... 720")
        sys.exit(1)

    target_url = sys.argv[1]
    
    # Default to 360 if no resolution is provided
    target_height = sys.argv[2] if len(sys.argv) > 2 else "360"
    
    main(target_url, target_height)
