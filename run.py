from playwright.sync_api import sync_playwright
import sys

chromiumPath = "/usr/bin/chromium-browser"   # your system chromium path

def main(search):
    url = "https://www.pornhub.com"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromiumPath,   # USE SYSTEM CHROMIUM
            args=["--no-sandbox", "--disable-gpu"]
        )

        context = browser.new_context()
        page = context.new_page()


        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        page.locator("button.buttonOver18").nth(1).click()
        page.wait_for_timeout(2000)
        
        page.locator("button.cbPrimaryCTA").click()
        page.wait_for_timeout(4000)
        
        page.locator("input#searchInput").fill(search)
        
        page.keyboard.press("Enter")
        page.wait_for_timeout(4000)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        page.wait_for_timeout(2000)
        page.screenshot(path="page.png", full_page=True)
        co = page.content()

        with open("div.html", "w") as f:
            f.write(str(co))

        browser.close()

if __name__ == "__main__":
    search = sys.argv[1]

    main(search)

