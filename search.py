import json
import os
import subprocess
from rich import print
from rich.console import Console

console = Console()

CACHE_FILE = "yt_search_cache.json"
RESULTS_PER_PAGE = 10


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def run_yt_dlp_json(target):
    """
    Run yt-dlp via CLI with IPv4 forced and return parsed JSON.
    """
    cmd = ["yt-dlp", "-4", "-J", target]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        print("[red]yt-dlp error:[/red]")
        print(result.stderr)
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[red]Failed to parse yt-dlp JSON output[/red]")
        return None


def extract_entries(target):
    data = run_yt_dlp_json(target)
    if not data:
        return []

    if "entries" in data and data["entries"]:
        return data["entries"]

    # Sometimes a single video may come back without entries
    return [data]


def search_youtube(query):
    cache = load_cache()
    cache_key = f"search|{query}"

    if cache_key in cache:
        print("[yellow]Loaded global search from cache[/yellow]")
        return cache[cache_key]

    videos = extract_entries(f"ytsearch100:{query}")
    cache[cache_key] = videos
    save_cache(cache)
    return videos


def search_in_channel(channel_url, keyword):
    cache = load_cache()
    cache_key = f"channel_search|{channel_url}|{keyword}"

    if cache_key in cache:
        print("[yellow]Loaded channel search from cache[/yellow]")
        return cache[cache_key]

    target = f"{channel_url}/search?query={keyword}"
    videos = extract_entries(target)
    cache[cache_key] = videos
    save_cache(cache)
    return videos


def list_channel_uploads(channel_url):
    cache = load_cache()
    cache_key = f"channel_uploads|{channel_url}"

    if cache_key in cache:
        print("[yellow]Loaded channel uploads from cache[/yellow]")
        return cache[cache_key]

    target = f"{channel_url}/videos"
    videos = extract_entries(target)
    cache[cache_key] = videos
    save_cache(cache)
    return videos


def get_video_url(video):
    """
    Try to normalize URL from yt-dlp JSON entry.
    """
    webpage_url = video.get("webpage_url")
    if webpage_url:
        return webpage_url

    url = video.get("url")
    if url:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        # for flat entries, url may be a video id
        return f"https://www.youtube.com/watch?v={url}"

    video_id = video.get("id")
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    return None


def paginate_results(videos):
    total = len(videos)
    page = 0

    while True:
        start = page * RESULTS_PER_PAGE
        end = min(start + RESULTS_PER_PAGE, total)

        console.clear()
        print(f"[bold cyan]Results (Page {page + 1})[/bold cyan]\n")

        for i in range(start, end):
            vid = videos[i]
            title = vid.get("title", "No title")
            channel = vid.get("channel") or vid.get("uploader") or "Unknown channel"
            print(f"[{i}] {title} [dim]- {channel}[/dim]")

        print("\n[n] next | [p] prev | [q] quit | number = select")
        cmd = input("Command: ").strip().lower()

        if cmd == "n":
            if end < total:
                page += 1
        elif cmd == "p":
            if page > 0:
                page -= 1
        elif cmd == "q":
            return None
        elif cmd.isdigit():
            idx = int(cmd)
            if 0 <= idx < total:
                return videos[idx]


def main():
    print("[bold magenta]YouTube Browser[/bold magenta]\n")
    print("Modes:")
    print("[1] Global search")
    print("[2] Search inside a channel")
    print("[3] List channel uploads")
    print()

    mode = input("Choose [1/2/3]: ").strip()

    videos = []
    if mode == "1":
        query = input("Search YouTube: ").strip()
        videos = search_youtube(query)

    elif mode == "2":
        channel_url = input("Channel URL: ").strip()
        keyword = input("Keyword to search inside channel: ").strip()
        videos = search_in_channel(channel_url, keyword)

    elif mode == "3":
        channel_url = input("Channel URL: ").strip()
        videos = list_channel_uploads(channel_url)

    else:
        print("[red]Invalid option[/red]")
        return

    if not videos:
        print("[red]No results found[/red]")
        return

    selected_video = paginate_results(videos)
    if not selected_video:
        print("No selection made.")
        return

    selected_url = get_video_url(selected_video)
    if not selected_url:
        print("[red]Could not determine video URL[/red]")
        return

    print(f"[green]Selected video URL:[/green] {selected_url}")
    fmt = input("Enter format (default=best): ").strip() or "best"

    subprocess.run(["python", "dl.py", selected_url, fmt])


if __name__ == "__main__":
    main()
