from fastapi import FastAPI, Request
import subprocess
import requests
import os
import traceback
import sys
import asyncio
from playwright.async_api import async_playwright
import httpx
import re
import html
import datetime
from tqdm import tqdm
import time
import signal
import threading

processes = {}

app = FastAPI()

LOCK_FILE = "/tmp/bot_download.lock"
CHROMIUM_PATH = "/usr/bin/chromium-browser"
PYTHON_BIN = "/root/miniconda3/envs/stream/bin/python"
BASE_DIR = "/root/strem"
DOWNLOAD_DIR = "download"
SPLIT_SIZE = "90m"
ARCHIVE_NAME = "video_archive"

def send_message1(chat_id, text):
    try:
        r = requests.post(
            "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=30
        )

    except Exception:
        traceback.print_exc()

def run(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        cwd=cwd,
    )

    print("RETURN CODE:", result.returncode)
    print("STDOUT:")
    print(result.stdout)

    print("STDERR:")
    print(result.stderr)

    result.check_returncode()

def cleanup(chat_id):
    run([
            "rclone",
            "--bind",
            "0.0.0.0",
            "delete",
            "gdrive:/vps"
        ])
    
    send_message1(chat_id, "All files deleted successfully.")

def cleanup_trash(chat_id):
    run([
            "rclone",
            "--bind",
            "0.0.0.0",
            "cleanup",
            "gdrive:"
        ])
    
    send_message1(chat_id, "All files deleted successfully in trash.")
    

def drive(files, chat_id):
    send_message1(chat_id, "Starting upload to drive")

    for f in files:
        run([
            "rclone",
            "--bind",
            "0.0.0.0",
            "copy",
            "-P",
            f,
            "gdrive:/vps"
        ], cwd=DOWNLOAD_DIR)

    send_message1(chat_id, "All files uploaded successfully.")
    
    run([
        "rm",
        "-rf",
        DOWNLOAD_DIR
    ])
    
    send_message1(chat_id, "Removed parts")



def split_rar(chat_id):
    send_message1(chat_id, f"Splitting into {SPLIT_SIZE} parts...")


    video_path = os.path.join(DOWNLOAD_DIR, "video.mp4")
    
    if not os.path.exists(video_path):

        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith("video.")]
        if not files:
            send_message1(chat_id, "Error: Downloaded video file not found.")
            sys.exit(1)
        video_path = os.path.join(DOWNLOAD_DIR, files[0])

    target_file = os.path.basename(video_path)

    size = f"-v{SPLIT_SIZE}"

    rar_name = f"{ARCHIVE_NAME}.rar"

    run([
        "rar",
        "a",
        size,
        "-m0",
        rar_name,
        target_file
    ], cwd=DOWNLOAD_DIR)

    parts = sorted(
        f for f in os.listdir(DOWNLOAD_DIR)
        if f.startswith(ARCHIVE_NAME) and f.endswith(".rar") or ".r" in f
    )

    os.remove(video_path)

    return parts


def download_patreon(chat_id, url):
    send_message1(chat_id, "Starting download")

    output_path = os.path.join(DOWNLOAD_DIR, "video.%(ext)s")

    with open(LOCK_FILE, "w") as f:
        f.write("running")

    process = subprocess.Popen([
        "/root/miniconda3/envs/stream/bin/yt-dlp",
        "-4",
        "--add-header",
        "Referer: https://www.patreon.com/",
        "--downloader",
        "[m3u8]/usr/bin/aria2c",
        "--downloader-args",
        "aria2c:-x:16:-k:1M:-4",
        "-o",
        output_path,
        url
    ])

    processes[chat_id] = process

    def monitor1():
        process.wait()

        if chat_id in processes:
            del processes[chat_id]

        send_message1("Download finished")

        parts = split_rar(chat_id)

        drive(parts, chat_id)
        
        send_message1(chat_id, "Operation success")

        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    threading.Thread(target=monitor1, daemon=True).start()


def download_inc(chat_id, url):
    send_message1(chat_id, "Starting download")

    with open(LOCK_FILE, "w") as f:
        f.write("running")

    process = subprocess.Popen([
        PYTHON_BIN,
        "/root/strem/inc_download.py",
        str(chat_id),
        url
    ])

    processes[chat_id] = process

    def monitor4():
        process.wait()

        if chat_id in processes:
            del processes[chat_id]

        send_message1("Download finished")

        parts = split_rar(chat_id)

        drive(parts, chat_id)
        
        send_message1(chat_id, "Operation success")

        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    threading.Thread(target=monitor4, daemon=True).start()
    

def download_streamable(chat_id, url, password):
    send_message1(chat_id, "Starting download")

    with open(LOCK_FILE, "w") as f:
        f.write("running")
        

    process = subprocess.Popen([
        PYTHON_BIN,
        "/root/strem/stream_download.py",
        str(chat_id),
        url,
        password
    ])

    processes[chat_id] = process

    def monitor3():
        process.wait()

        if chat_id in processes:
            del processes[chat_id]

        send_message1("Download finished")

        parts = split_rar(chat_id)

        drive(parts, chat_id)
        
        send_message1(chat_id, "Operation success")

        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    threading.Thread(target=monitor3, daemon=True).start()

    
def download_yt(chat_id, url, height):
    send_message1(chat_id, f"Starting download at {height}p...")

    with open(LOCK_FILE, "w") as f:
        f.write("running")
    
    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    output_path = os.path.join(DOWNLOAD_DIR, "video.%(ext)s")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    process = subprocess.Popen([
        "/root/miniconda3/envs/stream/bin/yt-dlp",
        "-4",
        "--downloader",
        "[m3u8]/usr/bin/aria2c",
        "--downloader-args",
        "aria2c:-x:16:-k:1M:-4",
        "--merge-output-format",
        "mp4",
        "-f",
        format_str,
        "-o",
        output_path,
        url
    ])

    processes[chat_id] = process

    def monitor():
        process.wait()

        if chat_id in processes:
            del processes[chat_id]

        send_message1("Download finished")

        parts = split_rar(chat_id)

        drive(parts, chat_id)
        
        send_message1(chat_id, "Operation success")

        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    threading.Thread(target=monitor, daemon=True).start()

    
def download_twitch(chat_id, url, height, start, end):
    send_message1(chat_id, f"Starting download at {height}p...")

    with open(LOCK_FILE, "w") as f:
        f.write("running")
    
    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    output_path = os.path.join(DOWNLOAD_DIR, "video.%(ext)s")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    regex = f"*{start}-{end}"
        
    process = subprocess.Popen([
        "/root/miniconda3/envs/stream/bin/yt-dlp",
        "-4",
        "--downloader",
        "[m3u8]/usr/bin/aria2c",
        "--downloader-args",
        "aria2c:-x:16:-k:1M:-4",
        "--download-sections",
        regex,
        "-f",
        format_str,
        "-o",
        output_path,
        url
    ])

    processes[chat_id] = process

    def monitor2():
        process.wait()

        if chat_id in processes:
            del processes[chat_id]

        send_message1("Download finished")

        parts = split_rar(chat_id)

        drive(parts, chat_id)
        
        send_message1(chat_id, "Operation success")

        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    threading.Thread(target=monitor2, daemon=True).start()
        

def download(text, chat_id):
    try:
        parts = text.split()

        command = parts[0]

        if os.path.exists(LOCK_FILE) and command != "/clean":
            send_message1(chat_id, "Another download is already running.")

            return {"ok": True}

        if command == "/start":
            print(chat_id)
            send_message1(chat_id, "Use Buttons")
            print(chat_id)

        if command == "/yt":

            if len(parts) != 3:
                send_message1(chat_id, "/yt <url> <360|480|720>")
                return {
                    "ok": False,
                    "usage": "/yt <url> <360|480|720>"
                }
            
            url = parts[1]
            quality = parts[2]

            download_yt(chat_id, url, quality)

            return {
                "ok": True,
                "action": "youtube",
                "url": url,
                "quality": quality
            }

        if command == "/twitch":

            if len(parts) < 3:
                send_message1(chat_id, "/twitch <url> 360|480|720 start(00:00:00) end(06:00:00)")
                return {
                    "ok": False,
                    "usage": "/twitch <url> start(00:00:00) end(06:00:00)"
                }
            
            url = parts[1]
            quality = parts[2]
            start = parts[3]
            end = parts[4]

            download_twitch(chat_id, url, quality, start, end)

            return {
                "ok": True,
                "action": "youtube",
                "url": url,
                "quality": quality
            }


        elif command == "/stream":

            if len(parts) != 3:
                send_message1(chat_id, "/stream <url> <password")
                return {
                    "ok": False,
                    "usage": "/stream <url> <password>"
                }
            
            url = parts[1]
            password = parts[2]

            download_streamable(chat_id, url, password)

            return {
                "ok": True,
                "action": "streamable",
                "url": url
            }
    
        elif command == "/inc":

            if len(parts) != 2:
                send_message1(chat_id, "/inc <url>")
                return {
                    "ok": False,
                    "usage": "/inc <url>"
                }
            
            url = parts[1]

            download_inc(chat_id, url)
            
            return {
                "ok": True,
                "action": "inc",
                "url": url
            }

        elif command == "/patreon":
            if len(parts) != 2:
                send_message1(chat_id, "/patreon <url>")
                return {
                    "ok": False,
                    "usage": "/patreon <url>"
                }
            
            url = parts[1]

            download_patreon(chat_id, url)
            
            return {
                "ok": True,
                "action": "inc",
                "url": url
            }
            
        elif command == "/clean":
            cleanup(chat_id)

            cleanup_trash(chat_id)

            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
            
            return {
                "ok": True,
                "action": "clean",
            }

        elif command == "/cancel":
            
            p = processes.get(chat_id)

            if p:
                p.terminate()
                del processes[chat_id]

            send_message1(chat_id, "Job cancelled")
        
        else:
            return {
                "ok": False,
                "error": "Unknown command"
            }

    except Exception as e:
        send_message1(chat_id, str(e))
        return {
            "ok": False,
            "error": str(e)
        }

@app.post("/webhook/streamable")
async def telegram_webhook(request: Request):
    update = await request.json()

    message = update.get("message", {})
    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")

    if not text:
        return {
            "ok": False,
            "error": "No text found"
        }

    download(text, chat_id)
