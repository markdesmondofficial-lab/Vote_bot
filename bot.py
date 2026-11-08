import os, random, re, sys, time
from playwright.sync_api import sync_playwright

BASE = "https://duel-og-frontend.centralmaster-hq.workers.dev/"
EMAIL = os.environ["BOT_EMAIL"]
PASSWORD = os.environ["BOT_PASSWORD"]
RUN_SECONDS = 240
VOTE_BTN = "button:has-text('Vote for this photo')"
WALL_TEXT = "Sign up free to cast your vote"


def show_page(page, label):
    """Print the visible text of the page so we can debug from the GitHub log."""
    try:
        text = page.inner_text("body")
        print(f"--- {label} ---")
        print(text[:700].replace("\n", " | "))
    except Exception as e:
        print("could not read page:", e)


def is_logged_out(page):
    try:
        return WALL_TEXT in page.inner_text("body")
    except Exception:
        return False


def log_in(page):
    """Open the Login form, fill email + password, submit."""
    # 1. Click the Login button / tab
    login_re = re.compile(r"^\s*log ?in\s*$", re.I)
    clicked = False
    for finder in (
        lambda: page.get_by_role("button", name=login_re),
        lambda: page.get_by_role("tab", name=login_re),
        lambda: page.get_by_role("link", name=login_re),
        lambda: page.get_by_text(login_re),
    ):
        try:
            loc = finder()
            if loc.count():
                loc.first.click(timeout=4000)
                clicked = True
                break
        except Exception as e:
            print("login click failed:", e)
    print("clicked Login:", clicked)
    page.wait_for_timeout(1500)

    # 2. Fill email
    email_box = page.locator(
        "input[type=email]:visible, input[placeholder*='mail' i]:visible, "
        "input[name=email]:visible"
    )
    if email_box.count():
        email_box.first.fill(EMAIL)
    else:
        other = page.locator("input:visible:not([type=password])")
        if other.count():
            other.first.fill(EMAIL)
        else:
            print("no email box found")

    # 3. Fill password and submit
    pw = page.locator("input[type=password]:visible")
    if not pw.count():
        print("no password box found")
        return False
    pw.first.fill(PASSWORD)
    submit = page.locator("button[type=submit]:visible")
    if submit.count():
        submit.first.click()
    else:
        pw.first.press("Enter")
    page.wait_for_timeout(5000)
    return True


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(BASE)
    page.wait_for_timeout(4000)

    # Always log in first
    log_in(page)
    page.goto(BASE)
    page.wait_for_timeout(4000)
    show_page(page, "page after login attempt")

    if page.locator(VOTE_BTN).count() < 2 or is_logged_out(page):
        # One more try: the wall may only show after a first vote attempt
        print("still looks logged out, trying login once more")
        log_in(page)
        page.goto(BASE)
        page.wait_for_timeout(4000)
        show_page(page, "page after second login attempt")

    if page.locator(VOTE_BTN).count() < 2:
        print("Could not find the vote buttons. Stopping.")
        browser.close()
        sys.exit(1)

    end = time.time() + RUN_SECONDS
    votes = 0
    misses = 0
    relogins = 0
    while time.time() < end:
        try:
            if is_logged_out(page) and relogins < 3:
                relogins += 1
                print("sign-up wall showed up, logging in again")
                log_in(page)
                page.goto(BASE)
                page.wait_for_timeout(3000)

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
                    page.goto(BASE)
                    page.wait_for_timeout(3000)
        except Exception as e:
            print("error:", e)
        page.wait_for_timeout(2000)

    print("done, total votes:", votes)
    browser.close()
