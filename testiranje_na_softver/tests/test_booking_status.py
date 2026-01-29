from datetime import datetime, timedelta
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _create_booking_via_form(page, first_name, last_name, email, phone, checkin, checkout):
    page.goto(f"{BASE_URL}/booking", wait_until="domcontentloaded")

    page.fill("input[name='first_name']", first_name)
    page.fill("input[name='last_name']", last_name)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)

    # must match booking.html input names
    page.fill("input[name='checkin_date']", checkin)
    page.fill("input[name='checkout_date']", checkout)

    page.click("button[type='submit']")

    # allow /booking-status with optional params
    page.wait_for_url(re.compile(r".*/booking-status.*"), timeout=10000)
    page.wait_for_load_state("networkidle")


def test_booking_status_email_not_found_shows_error():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

            email = "no_such_booking_12345@example.com"
            page.fill("input[name='email']", email)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")

            page.wait_for_selector(
                "text=/Нема пронајдена регистрација|нема резултат|not found|no booking|не постои/i",
                timeout=6000
            )

            page.screenshot(path="booking_status_not_found.png", full_page=True)
            print("✅ booking-status not found test passed.")
        finally:
            browser.close()


def test_booking_status_found_shows_booking_details_and_stay_days():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            first_name = "Test"
            last_name = f"User{stamp}"
            email = f"test_{stamp}@example.com"
            phone = "070123456"

            checkin = datetime.now().strftime("%Y-%m-%d")
            checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
            expected_days = 3

            # 1) create booking
            _create_booking_via_form(page, first_name, last_name, email, phone, checkin, checkout)

            # 2) search on booking-status (deterministic)
            page.wait_for_selector("input[name='email']", timeout=6000)
            page.fill("input[name='email']", email)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(250)

            # 3) success message (your real UI text)
            page.wait_for_selector(
                "text=/Резервацијата е пронајдена и е валидна|резервација.*пронајден|пронајдена.*валидна|valid/i",
                timeout=7000
            )

            # Name
            page.wait_for_selector(f"text={first_name}", timeout=7000)
            page.wait_for_selector(f"text={last_name}", timeout=7000)

            # Dates
            page.wait_for_selector(f"text={checkin}", timeout=7000)
            page.wait_for_selector(f"text={checkout}", timeout=7000)

            # Stay days label + value (✅ FIXED: use Playwright text regex string, not python Pattern)
            page.wait_for_selector("text=/Вкупно денови/i", timeout=7000)
            page.wait_for_selector(f"text=/{expected_days}\\s*дена/i", timeout=7000)

            page.screenshot(path="booking_status_found.png", full_page=True)
            print("✅ booking-status found test passed.")

        except PlaywrightTimeoutError:
            page.screenshot(path="booking_status_found_fail.png", full_page=True)
            print("URL:", page.url)
            print("Body text (first 1800 chars):\n", page.inner_text("body")[:1800])
            raise

        finally:
            browser.close()


def test_booking_status_email_required_browser_validation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"{BASE_URL}/booking-status", wait_until="domcontentloaded")

            page.click("button[type='submit']")
            page.wait_for_timeout(400)

            if "/booking-status" not in page.url:
                raise AssertionError(f"❌ Form submitted unexpectedly. URL changed to: {page.url}")

            is_invalid = page.eval_on_selector("input[name='email']", "el => !el.checkValidity()")
            if not is_invalid:
                page.screenshot(path="booking_status_email_required_fail.png", full_page=True)
                raise AssertionError("❌ Expected email input to be invalid (required), but it is valid.")

            page.screenshot(path="booking_status_email_required_ok.png", full_page=True)
            print("✅ booking-status required email validation test passed.")

        finally:
            browser.close()


if __name__ == "__main__":
    test_booking_status_email_not_found_shows_error()
    test_booking_status_found_shows_booking_details_and_stay_days()
    test_booking_status_email_required_browser_validation()
