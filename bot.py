import os, random, re, sys, time
from playwright.sync_api import sync_playwright

BASE = "https://duel-og-frontend.centralmaster-hq.workers.dev/"
EMAIL = os.environ["BOT_EMAIL"]
PASSWORD = os.environ["BOT_PASSWORD"]
RUN_SECONDS = 240
VOTE_BTN = "button:has-text('Vote for this photo')"


def show_page(page, label):
    """Print the visible text of the page so we can debug from the GitHub log."""
    try:
        text = page.inner_text("body")
        print(f"--- {label} ---")
        print(text[:700].replace("\n", " | "))
    except Exception as e:
        print("could not read page:", e)


def try_login(page):
    # If there is a Log in / Sign in button on the landing page, open it first.
    for label in ["Log in", "Login", "Sign in", "Sign In"]:
        loc = page.locator(f"button:has-text('{label}'), a:has-text('{label}')")
        if loc.count():
            try:
                loc.first.click()
                page.wait_for_timeout(1500)
            except Exception as e:
                print("login button click failed:", e)
            break

    email = page.locator("input[type=email], input[name=email], input[placeholder*='mail' i]")
    if email.count():
        email.first.fill(EMAIL)
    password = page.locator("input[type=password]")
    if password.count():
        password.first.fill(PASSWORD)
        submit = page.locator(
            "button[type=submit], button:has-text('Log in'), "
            "button:has-text('Sign in'), button:has-text('Continue')"
        )
        if submit.count():
            submit.first.click()
        else:
            password.first.press("Enter")
        page.wait_for_timeout(5000)
    else:
        print("no password box found")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(BASE)
    page.wait_for_timeout(4000)

    if page.locator(VOTE_BTN).count() < 2:
        show_page(page, "page before login")
        try_login(page)
        page.goto(BASE)
        page.wait_for_timeout(4000)

    if page.locator(VOTE_BTN).count() < 2:
        show_page(page, "page after login (still no vote buttons)")
        print("Could not find the vote buttons. Stopping.")
        browser.close()
        sys.exit(1)

    end = time.time() + RUN_SECONDS
    votes = 0
    misses = 0
    while time.time() < end:
        try:
            buttons = page.locator(VOTE_BTN)
            if buttons.count() >= 2:
                misses = 0
                before = re.findall(r"@\w+", page.inner_text("body"))[:2]
                buttons.nth(random.randint(0, 1)).click(timeout=5000)
                votes += 1
                print(f"vote {votes} on pair {before}")
            else:
                misses += 1
                print("no vote buttons right now")
                if misses % 3 == 0:
                    show_page(page, "page without vote buttons")
                    page.reload()
                    page.wait_for_timeout(3000)
        except Exception as e:
            print("error:", e)
        page.wait_for_timeout(2000)

    print("done, total votes:", votes)
    browser.close()
