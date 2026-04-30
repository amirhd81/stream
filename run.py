from playwright.sync_api import sync_playwright

chromiumPath = "/usr/bin/chromium-browser"   # your system chromium path

url = "https://streamable.com/ri37ps"
password = "gvc277"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        executable_path=chromiumPath,   # USE SYSTEM CHROMIUM
        args=["--no-sandbox", "--disable-gpu"]
    )

    context = browser.new_context()
    page = context.new_page()

    # Navigate to video page
    page.goto(url, wait_until="domcontentloaded")

    # Fill password
    page.fill('form[name="video-password"] input[name="password"]', password)
    page.click('button[type="submit"]')

    # Wait for video to unlock
    page.wait_for_selector("video source[src]")

    # Extract video URL
    video_url = page.locator("video source").first.get_attribute("src")
    print("Video URL:", video_url)

    # Download using authenticated Playwright session
    response = context.request.get(video_url)
    content = response.body()

    # Save
    with open("video.mp4", "wb") as f:
        f.write(content)

    print("Saved video.mp4")
