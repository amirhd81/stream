from playwright.sync_api import sync_playwright
from undetected_playwright import stealth_sync
import sys

chromiumPath = "/usr/bin/chromium-browser"   # your system chromium path

def main():
    url = "https://discord.com/channels/1171584364723847230/1199031302725312643"
    
    with sync_playwright() as p:
        context = p.chromium.launch(
            user_data_dir="/root/strem/pro/Profile 41",
            record_video_dir="videos/",
            storageState="state.json",
            record_video_size={"width": 640, "height": 480},
            headless=True,
            executable_path=chromiumPath,   # USE SYSTEM CHROMIUM
            args=["--no-sandbox", "--disable-gpu"],
        )

    
        page = context.new_page()

        stealth_sync(page)


        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        # page.locator("input#uid_10").fill("amir.hd.davoudi1381@gmail.com")
        # page.locator("input#uid_12").fill("@Lost4815162342")
        # page.locator("button[type='submit']").click()
        # page.wait_for_timeout(2000)
        # page.wait_for_timeout(3000)
        # page.locator("button.buttonOver18").nth(1).click()
        # page.wait_for_timeout(2000)
        
        # page.locator("button.cbPrimaryCTA").click()
        # page.wait_for_timeout(4000)
        
        # page.locator("input#searchInput").fill(search)
        
        # page.keyboard.press("Enter")
        # page.wait_for_timeout(4000)

        # page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        # page.wait_for_timeout(1500)

        # page.wait_for_timeout(2000)
        # page.screenshot(path="page.png", full_page=True)
        co = page.content()

        with open("div.html", "w") as f:
            f.write(str(co))

        context.close()

if __name__ == "__main__":
    search = sys.argv[1]

    main()
