import re
import sys
import requests
from urllib.parse import urlparse

def extract_video_id(url: str) -> str:
    """
    Extract Streamable video ID from URL.
    Example:
    https://streamable.com/abcd12 -> abcd12
    """
    match = re.search(r"streamable\.com/([a-zA-Z0-9]+)", url)
    if not match:
        raise ValueError("Invalid Streamable URL")
    return match.group(1)


def proto_relative_url(url: str) -> str:
    """Fix URLs that start with //"""
    if url.startswith("//"):
        return "https:" + url
    return url


def get_video_info(url: str) -> dict:
    video_id = extract_video_id(url)

    api_url = f"https://ajax.streamable.com/videos/{video_id}"
    response = requests.get(api_url)
    response.raise_for_status()

    video = response.json()

    # Check status
    # 0 uploading
    # 1 processing
    # 2 ready
    # 3 error
    status = video.get("status")
    if status != 2:
        raise Exception(
            "Video unavailable. It may still be uploading or processing."
        )

    title = video.get("reddit_title") or video.get("title")

    formats = []
    files = video.get("files", {})

    for key, info in files.items():
        url = info.get("url")
        if not url:
            continue

        formats.append({
            "format_id": key,
            "url": proto_relative_url(url),
            "width": info.get("width"),
            "height": info.get("height"),
            "filesize": info.get("size"),
            "fps": info.get("framerate"),
            "bitrate": info.get("bitrate"),
            "video_codec": (
                info.get("input_metadata", {})
                .get("video_codec_name")
            ),
            "audio_codec": (
                info.get("input_metadata", {})
                .get("audio_codec_name")
            ),
        })

    return {
        "id": video_id,
        "title": title,
        "description": video.get("description"),
        "thumbnail": proto_relative_url(video.get("thumbnail_url", "")),
        "uploader": video.get("owner", {}).get("user_name"),
        "timestamp": video.get("date_added"),
        "duration": video.get("duration"),
        "view_count": video.get("plays"),
        "formats": formats,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python streamable_extractor.py <streamable_url>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        info = get_video_info(url)

        print("\n=== Video Info ===")
        print(f"ID: {info['id']}")
        print(f"Title: {info['title']}")
        print(f"Uploader: {info['uploader']}")
        print(f"Duration: {info['duration']} seconds")
        print(f"Views: {info['view_count']}")
        print(f"Thumbnail: {info['thumbnail']}")

        print("\n=== Available Formats ===")
        for fmt in info["formats"]:
            print(
                f"{fmt['format_id']} | "
                f"{fmt['width']}x{fmt['height']} | "
                f"{fmt['bitrate']} kbps | "
                f"{fmt['url']}"
            )

    except Exception as e:
        print("Error:", str(e))
