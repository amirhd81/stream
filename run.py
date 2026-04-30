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

    page.wait_for_timeout(2000)



    # Extract video URL
    video_url = "https://cdn-cf-east.streamable.com/video/mp4/ri37ps.mp4?Expires=1777842035795&amp;Key-Pair-Id=APKAIEYUVEN4EVB2OKEQ&amp;Signature=d0X~owv~Q-N1Ww~rTMZgB-l2GplY23~EwEhhIVvU3jnVzq6ywuFjdfx58wcatMibfg0lrfneIzOprZ~5ZeBB8uRQP1dF~09Mlelo7P--Yuimv9TAyIjhC8pax1AWfgQ9UQDbR2vOOOsA7Axl8ZRpteDZHDF70PbaUAHjTtL-O5WeBoQfMKXzgs42I6G-Ndur2vrPTRMYEdGNrB5Nh5rrvwMq0qYfVtoPcp-bOXhEaN2TA5hNiA8NDHTmwZpkFUxOeR3S3VQ2x10ZnzrKOqutrGDiZbq1hxoDEAAfylw3bLtEozPs-q~j0TIHBjz~bsZ4fr1QpcQsqcAE4WSGVe8sNA__"
    print("Video URL:", video_url)

    # Download using authenticated Playwright session
    response = context.request.get(video_url)
    content = response.body()

    # Save
    with open("video.mp4", "wb") as f:
        f.write(content)

    print("Saved video.mp4")
