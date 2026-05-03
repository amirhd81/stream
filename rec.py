from playwright.sync_api import sync_playwright
import sys

chromiumPath = "/usr/bin/chromium-browser"

def main():
    url = "https://discord.com/channels/1171584364723847230/1199031302725312643"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromiumPath,
            args=["--no-sandbox", "--disable-gpu"],
        )

        context = browser.new_context(
            storage_state="discord.json",
            record_video_dir="videos/",
            record_video_size={"width": 640, "height": 480},
        )
    
        page = context.new_page()
        context.storageState({ path: 'discord1.json' })

        page.goto(url, wait_until="domcontentloaded")

        page.wait_for_timeout(30000 * 1)

        html = page.content()

        with open("div.html", "w") as f:
            f.write(html)

        context.close()
        browser.close()

if __name__ == "__main__":
    search = sys.argv[1]
    main()
