import json
import os
import subprocess
import sys
from datetime import datetime
from rich import print
from rich.console import Console

console = Console()

CACHE_FILE = "yt_cache.json"
RESULTS_PER_PAGE = 10
SEARCH_CAP = 100


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def run_yt_dlp_json(target, playlist_start=None, playlist_end=None):
    cmd = ["yt-dlp", "-4", "--flat-playlist", "-J"]

    if playlist_start is not None:
        cmd += ["--playlist-start", str(playlist_start)]
    if playlist_end is not None:
        cmd += ["--playlist-end", str(playlist_end)]

    cmd.append(target)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        print("[red]yt-dlp error:[/red]")
        print(result.stderr.strip())
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[red]Failed to parse yt-dlp JSON output[/red]")
        return None


def extract_entries(data):
    if not data:
        return []
    if "entries" in data and data["entries"]:
        return data["entries"]
    return [data]


def time_ago(upload_date):
    if not upload_date:
        return "unknown date"
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d")
        delta = datetime.now() - dt
        days = delta.days

        if days < 0:
            return "unknown date"
        if days == 0:
            return "today"
        if days == 1:
            return "1 day ago"
        if days < 30:
            return f"{days} days ago"
        if days < 365:
            months = days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        years = days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    except Exception:
        return "unknown date"


def get_video_url(video):
    webpage_url = video.get("webpage_url")
    if webpage_url:
        return webpage_url

    url = video.get("url")
    if url and isinstance(url, str) and url.startswith("http"):
        return url

    video_id = video.get("id")
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    return None


def fetch_page(target, cache_key_base, page):
    cache = load_cache()
    cache_key = f"{cache_key_base}|page:{page}"

    if cache_key in cache:
        print(f"[yellow]Loaded page {page} from cache[/yellow]")
        return cache[cache_key]

    start = (page - 1) * RESULTS_PER_PAGE + 1
    end = page * RESULTS_PER_PAGE

    data = run_yt_dlp_json(target, playlist_start=start, playlist_end=end)
    entries = extract_entries(data)

    cache[cache_key] = entries
    save_cache(cache)

    return entries


def display_videos(videos, page, header):
    console.clear()
    print(f"[bold cyan]{header} - Page {page}[/bold cyan]\n")

    for i, vid in enumerate(videos, start=1):
        title = vid.get("title", "No title")
        channel = vid.get("channel") or vid.get("uploader") or "Unknown channel"
        age = time_ago(vid.get("upload_date"))
        print(f"[green][{i}][/green] {title} [dim]- {channel}, {age}[/dim]")

    print("\n[bold yellow]Commands:[/bold yellow] [n] next, [p] previous, [q] quit, [1-10] select")


def paginate_target(target, cache_key_base, header):
    page = 1

    while True:
        videos = fetch_page(target, cache_key_base, page)

        if not videos:
            if page == 1:
                print("[red]No results found.[/red]")
                return None
            print("[red]No more results.[/red]")
            page -= 1
            continue

        display_videos(videos, page, header)
        cmd = input("Enter command: ").strip().lower()

        if cmd == "n":
            page += 1
        elif cmd == "p":
            if page > 1:
                page -= 1
        elif cmd == "q":
            return None
        elif cmd.isdigit():
            idx = int(cmd)
            if 1 <= idx <= len(videos):
                return videos[idx - 1]
            else:
                print("[red]Invalid selection.[/red]")
        else:
            print("[red]Invalid command.[/red]")


def global_search():
    query = input("Enter search query: ").strip()
    if not query:
        print("[red]Query cannot be empty.[/red]")
        return None

    target = f"ytsearch{SEARCH_CAP}:{query}"
    return paginate_target(target, f"global_search|{query}", f"Search: {query}")


def channel_uploads():
    channel_url = input("Enter channel URL: ").strip()
    if not channel_url:
        print("[red]Channel URL cannot be empty.[/red]")
        return None

    target = f"{channel_url}/videos"
    return paginate_target(target, f"channel_uploads|{channel_url}", f"Uploads: {channel_url}")


def channel_search():
    channel_url = input("Enter channel URL: ").strip()
    if not channel_url:
        print("[red]Channel URL cannot be empty.[/red]")
        return None

    query = input("Enter search term inside the channel: ").strip()
    if not query:
        print("[red]Search term cannot be empty.[/red]")
        return None

    # This may work depending on extractor behavior
    target = f"{channel_url}/search?query={query}"
    return paginate_target(
        target,
        f"channel_search|{channel_url}|{query}",
        f"Channel Search: {query}"
    )


def download_selected_video(video):
    url = get_video_url(video)
    if not url:
        print("[red]Could not determine video URL.[/red]")
        return

    print(f"\nSelected: [bold]{video.get('title', 'No title')}[/bold]")
    print(f"URL: [blue]{url}[/blue]")

    fmt = input("Enter download format (default: best): ").strip() or "best"

    print("[cyan]Starting downloader...[/cyan]")
    subprocess.run([sys.executable, "dl.py", url, fmt])


def main():
    while True:
        print("\n[bold magenta]YouTube Browser[/bold magenta]")
        print("[1] Global search")
        print("[2] Channel uploads")
        print("[3] Search inside a channel")
        print("[q] Quit")

        choice = input("Choose an option: ").strip().lower()

        selected_video = None

        if choice == "1":
            selected_video = global_search()
        elif choice == "2":
            selected_video = channel_uploads()
        elif choice == "3":
            selected_video = channel_search()
        elif choice == "q":
            print("Goodbye.")
            break
        else:
            print("[red]Invalid option.[/red]")
            continue

        if selected_video:
            download_selected_video(selected_video)


if __name__ == "__main__":
    main()
