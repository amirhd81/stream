import json
import os
from yt_dlp import YoutubeDL
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
        json.dump(cache, f, indent=2)


def extract_videos(url_or_query):
    """Generic extractor using yt-dlp"""
    ydl_opts = {"quiet": True, "extract_flat": True}
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url_or_query, download=False)
    return result.get("entries", [])


def search_youtube(query):
    """Search globally"""
    cache = load_cache()
    if query in cache:
        print("[yellow]Loaded from cache[/yellow]")
        return cache[query]

    videos = extract_videos(f"ytsearch100:{query}")
    cache[query] = videos
    save_cache(cache)
    return videos


def search_in_channel(channel_url, keyword):
    """Search within a channel"""
    cache_key = f"{channel_url}|{keyword}"
    cache = load_cache()
    if cache_key in cache:
        print("[yellow]Loaded channel search from cache[/yellow]")
        return cache[cache_key]

    videos = extract_videos(f"{channel_url}/search?query={keyword}")
    cache[cache_key] = videos
    save_cache(cache)
    return videos


def list_channel_uploads(channel_url):
    """List all recent uploads from a channel"""
    cache_key = f"{channel_url}|uploads"
    cache = load_cache()
    if cache_key in cache:
        print("[yellow]Loaded channel uploads from cache[/yellow]")
        return cache[cache_key]

    videos = extract_videos(f"{channel_url}/videos")
    cache[cache_key] = videos
    save_cache(cache)
    return videos


def paginate_results(videos):
    """Show paginated results and return selected video URL"""
    total = len(videos)
    page = 0

    while True:
        start = page * RESULTS_PER_PAGE
        end = start + RESULTS_PER_PAGE
        console.clear()
        print(f"[bold cyan]Results (Page {page + 1})[/bold cyan]\n")

        for i, vid in enumerate(videos[start:end], start=start):
            print(f"[{i}] {vid.get('title')}")

        print("\n[n] next | [p] prev | [q] quit | number = select")
        cmd = input("Command: ").strip()
        if cmd == "n" and end < total:
            page += 1
        elif cmd == "p" and page > 0:
            page -= 1
        elif cmd.isdigit():
            idx = int(cmd)
            if 0 <= idx < total:
                return videos[idx]["url"]
        elif cmd == "q":
            return None


def main():
    print("[bold magenta]YouTube Browser[/bold magenta]\n")
    print("Modes:\n[1] Global search\n[2] Search inside a channel\n[3] List channel uploads\n")
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
        print("Invalid option.")
        return

    if not videos:
        print("No results found.")
        return

    selected = paginate_results(videos)
    if selected:
        print(f"[green]Selected video URL:[/green] {selected}")
        fmt = input("Enter format (default=best): ").strip() or "best"
        os.system(f"python dl.py \"{selected}\" \"{fmt}\"")
    else:
        print("No selection made.")


if __name__ == "__main__":
    main()
