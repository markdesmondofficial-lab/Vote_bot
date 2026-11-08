import os, random, time
from playwright.sync_api import sync_playwright

URL = "https://duel-og-frontend.centralmaster-hq.workers.dev/u/mark"
EMAIL = os.environ["BOT_EMAIL"]
PASSWORD = os.environ["BOT_PASSWORD"]
RUN_SECONDS = 240

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(3000)

    if page.locator("input[type=password]").count():
        page.fill("input[type=email], input[name=email], input[type=text]", EMAIL)
        page.fill("input[type=password]", PASSWORD)
        page.click("button[type=submit], button:has-text('Log in'), button:has-text('Sign in')")
        page.wait_for_timeout(4000)

    end = time.time() + RUN_SECONDS
    votes = 0
    while time.time() < end:
        try:
            imgs = page.locator("img:visible")
            if imgs.count() >= 2:
                imgs.nth(random.randint(0, 1)).click()
                votes += 1
                print("votes so far:", votes)
        except Exception as e:
            print("error:", e)
        page.wait_for_timeout(2000)

    browser.close()
