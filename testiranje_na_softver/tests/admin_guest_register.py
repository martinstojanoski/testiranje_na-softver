import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def test_admin_register_guest():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context()
        page = context.new_page()

        try:
            # ----------------------
            # LOGIN AS ADMIN
            # ----------------------
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            page.fill("input[name='username']", "admin")
            page.fill("input[name='password']", "adminpass")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")

            # robust login check
            try:
                page.wait_for_selector("text=/logout|одјава/i", timeout=6000)
                page.screenshot(path="login_ok.png", full_page=True)
                print("✅ Login successful (logout detected): admin")
            except TimeoutError:
                page.screenshot(path="login_fail.png", full_page=True)
                raise Exception("❌ Login failed: logout/одјава not detected.")

            # ----------------------
            # OPEN ADMIN PAGE
            # ----------------------
            page.goto(f"{BASE_URL}/admin", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            if "/login" in page.url:
                page.screenshot(path="admin_access_fail.png", full_page=True)
                raise Exception("❌ Cannot access /admin (redirected to /login).")

            # ----------------------
            # WAIT FOR FORM FIELDS (REAL ON YOUR PAGE)
            # ----------------------
            required_fields = [
                "input[name='first_name']",
                "input[name='last_name']",
                "input[name='email']",
                "input[name='phone']",
                "input[name='check_in']",
                "input[name='check_out']",
            ]

            for sel in required_fields:
                try:
                    page.wait_for_selector(sel, state="visible", timeout=7000)
                except TimeoutError:
                    page.screenshot(path="admin_form_missing_fields.png", full_page=True)
                    print("Missing selector:", sel)
                    print("Admin URL:", page.url)
                    print("Body text (first 1200 chars):\n", page.inner_text("body")[:1200])
                    raise Exception(f"❌ Admin form field not visible: {sel}")

            # ----------------------
            # FILL FORM
            # ----------------------
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            first_name = "Martin"
            last_name = "Stojanoski"
            email = f"martin.stojanoski.{ts}@test.local"
            phone = "+38970123456"

            check_in = "2026-12-12"
            check_out = "2026-12-15"

            page.fill("input[name='first_name']", first_name)
            page.fill("input[name='last_name']", last_name)
            page.fill("input[name='email']", email)
            page.fill("input[name='phone']", phone)
            page.fill("input[name='check_in']", check_in)
            page.fill("input[name='check_out']", check_out)

            # ----------------------
            # SUBMIT
            # ----------------------
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")

            # ----------------------
            # SUCCESS CHECK (ROBUST)
            # ----------------------
            success = page.locator("text=/registered successfully|success|успешно|регистриран|додаден|saved/i")
            try:
                success.first.wait_for(state="visible", timeout=7000)
                page.screenshot(path="register_ok.png", full_page=True)
                print(f"✅ Guest registered: {first_name} {last_name} | {email}")
            except TimeoutError:
                page.screenshot(path="register_fail.png", full_page=True)
                print("URL after submit:", page.url)
                print("Body text (first 1500 chars):\n", page.inner_text("body")[:1500])
                raise Exception("❌ Registration failed: success message not detected.")

            time.sleep(1)

        finally:
            browser.close()


if __name__ == "__main__":
    test_admin_register_guest()
