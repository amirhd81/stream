import json
import os
import subprocess
from datetime import datetime
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
    cmd = ["yt-dlp", "-4", "-J", target]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print("[red]yt‑dlp error:[/red]")
        print(result.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[red]Failed to parse yt‑dlp JSON[/red]")
        return None


def extract_entries(target):
    data = run_yt_dlp_json(target)
    if not data:
        return []
    if "entries" in data and data["entries"]:
        return data["entries"]
    return [data]


def search_youtube(query):
    cache = load_cache()
    key = f"search|{query}"
    if key in cache:
        print("[yellow]Loaded from cache[/yellow]")
        return cache[key]
    vids = extract_entries(f"ytsearch100:{query}")
    cache[key] = vids
    save_cache(cache)
    return vids


def search_in_channel(channel_url, keyword):
    cache = load_cache()
    key = f"channel_search|{channel_url}|{keyword}"
    if key in cache:
        print("[yellow]Loaded from cache[/yellow]")
        return cache[key]
    target = f"{channel_url}/search?query={keyword}"
    vids = extract_entries(target)
    cache[key] = vids
    save_cache(cache)
    return vids


def list_channel_uploads(channel_url):
    cache = load_cache()
    key = f"channel_uploads|{channel_url}"
    if key in cache:
        print("[yellow]Loaded from cache[/yellow]")
        return cache[key]
    target = f"{channel_url}/videos"
    vids = extract_entries(target)
    cache[key] = vids
    save_cache(cache)
    return vids


def time_ago(upload_date):
    if not upload_date:
        return "Unknown date"
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d")
        delta = datetime.now() - dt
        days = delta.days
        if days < 1:
            return "today"
        elif days == 1:
            return "1 day ago"
        elif days < 30:
            return f"{days} days ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except Exception:
        return "Unknown date"


def get_video_url(video):
    for key in ("webpage_url", "url", "id"):
        val = video.get(key)
        if val:
            if val.startswith("http"):
                return val
            return f"https://www.youtube.com/watch?v={val}"
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
            channel = vid.get("channel") or vid.get("uploader") or "Unknown"
            age = time_ago(vid.get("upload_date"))
            print(f"[{i}] {title} [dim]- {channel}, {age}[/dim]")

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
    print("Modes:\n[1] Global search\n[2] Search in channel\n[3] Channel uploads\n")
    mode = input("Choose [1/2/3]: ").strip()
    videos = []
    if mode == "1":
        query = input("Search: ").strip()
        videos = search_youtube(query)
    elif mode == "2":
        channel = input("Channel URL: ").strip()
        keyword = input("Keyword: ").strip()
        videos = search_in_channel(channel, keyword)
    elif mode == "3":
        channel = input("Channel URL: ").strip()
        videos = list_channel_uploads(channel)
    else:
        print("[red]Invalid choice[/red]")
        return

    if not videos:
        print("[red]No results found[/red]")
        return

    sel = paginate_results(videos)
    if not sel:
        print("No selection made.")
        return

    url = get_video_url(sel)
    if not url:
        print("[red]Invalid URL[/red]")
        return

    fmt = input("Format (default=best): ").strip() or "best"
    subprocess.run(["python", "dl.py", url, fmt])


if __name__ == "__main__":
    main()
