from datetime import datetime
import random
import string
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _letters_only(n=10):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def _dump_errors(page):
    # печати можни error/flash/validation текстови од UI (ако постојат)
    candidates = [
        ".flash", ".alert", "[role='alert']",
        "text=/веќе постои|exists|error|invalid|грешк|невалид|password|username|email|phone|confirm/i"
    ]
    texts = []
    for sel in candidates:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                t = loc.first.inner_text().strip()
                if t and t not in texts:
                    texts.append(t)
        except Exception:
            pass
    return texts


def test_user_register_success():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"{BASE_URL}/register", wait_until="domcontentloaded")

            stamp = datetime.now().strftime("%H%M%S")

            first_name = "Martin"
            last_name = "Stojanoski"

            # ✅ letters-only username (as your UI says)
            username = "user" + _letters_only(8)

            # ✅ email: use standard valid domain
            email = f"{username}{stamp}@example.com"

            # ✅ phone: local digits format (most validators accept this)
            phone = "07" + str(random.randint(1000000, 9999999))

            # ✅ password: strong and matching
            password = "Pass123!aa"
            confirm_password = password

            # Fill all required fields
            page.fill("input[name='first_name']", first_name)
            page.fill("input[name='last_name']", last_name)
            page.fill("input[name='username']", username)
            page.fill("input[name='email']", email)
            page.fill("input[name='phone']", phone)
            page.fill("input[name='password']", password)
            page.fill("input[name='confirm_password']", confirm_password)

            # Before submit: check HTML5 invalid fields (if any)
            invalid_any = page.eval_on_selector("form", "f => !!f.querySelector(':invalid')")
            if invalid_any:
                page.screenshot(path="register_blocked_html5_invalid.png", full_page=True)
                # пробај да најдеш кој field е invalid
                invalid_name = page.eval_on_selector(
                    "form", "f => (f.querySelector(':invalid') && f.querySelector(':invalid').name) || ''"
                )
                raise AssertionError(f"❌ Blocked by HTML5 validation (:invalid). First invalid field: {invalid_name}")

            # Submit
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(400)

            # ✅ Success option A: redirected to /login
            if "/login" in page.url:
                page.screenshot(path="register_ok_redirect_login.png", full_page=True)
                print(f"✅ Registration successful (redirected to /login): {username}")
                return

            # ✅ Success option B: show success text
            success_locator = page.locator(
                "text=/успешн|registered|success|account created|креиран|регистриран|now you can login/i"
            )
            try:
                success_locator.first.wait_for(state="visible", timeout=4000)
                page.screenshot(path="register_ok_success_message.png", full_page=True)
                print(f"✅ Registration successful (success message shown): {username}")
                return
            except TimeoutError:
                pass

            # ❌ If still on /register, check for error text and print it
            errors = _dump_errors(page)
            page.screenshot(path="register_fail.png", full_page=True)
            print("URL after submit:", page.url)
            if errors:
                print("Detected UI errors/alerts:")
                for e in errors:
                    print(" -", e)

            raise AssertionError("❌ Registration did not succeed. See register_fail.png and printed errors.")

        finally:
            browser.close()


if __name__ == "__main__":
    test_user_register_success()
