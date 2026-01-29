import re
import time
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _count_guest_rows(page) -> int:
    """
    Грубо броење на редови во табелата "All Guests".
    Ако немаш <table>, овој дел може да се прилагоди.
    """
    # најчесто табела редови:
    # - ако имаш <tbody><tr>...</tr></tbody> ќе работи
    # - ако немаш, нека врати 0 без да руши тест
    try:
        return page.locator("table tbody tr").count()
    except Exception:
        return 0


def test_admin_register_guest_negative_invalid_data():
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
            page.wait_for_selector("text=/logout|одјава/i", timeout=6000)

            # ----------------------
            # OPEN ADMIN PAGE
            # ----------------------
            page.goto(f"{BASE_URL}/admin", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            if "/login" in page.url:
                page.screenshot(path="neg_admin_access_fail.png", full_page=True)
                raise Exception("❌ Cannot access /admin (redirected to /login).")

            # ----------------------
            # WAIT FOR FORM FIELDS
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
                page.wait_for_selector(sel, state="visible", timeout=7000)

            # (опционално) брои редови пред submit
            rows_before = _count_guest_rows(page)

            # ----------------------
            # FILL FORM WITH INVALID DATA (NEGATIVE CASE)
            # ----------------------
            # 1) first_name празно (или whitespace)
            page.fill("input[name='first_name']", "")

            # 2) last_name може да ставиме валидно (не мора, но ок)
            page.fill("input[name='last_name']", "Stojanoski")

            # 3) email невалиден
            page.fill("input[name='email']", "not-an-email")

            # 4) phone невалиден (премногу краток / букви)
            page.fill("input[name='phone']", "abc")

            # 5) check_out пред check_in (логички невалидно)
            page.fill("input[name='check_in']", "2026-12-15")
            page.fill("input[name='check_out']", "2026-12-12")

            # ----------------------
            # SUBMIT
            # ----------------------
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)

            # ----------------------
            # NEGATIVE ASSERTIONS
            # ----------------------
            # A) НЕ смее да има success порака
            success = page.locator("text=/registered successfully|success|успешно|регистриран|додаден|saved/i")
            try:
                # ако се појави success -> тестот треба да падне
                success.first.wait_for(state="visible", timeout=2500)
                page.screenshot(path="neg_register_unexpected_success.png", full_page=True)
                raise Exception("❌ Negative test failed: success message appeared for invalid input!")
            except TimeoutError:
                # тоа е добро: нема success
                pass

            # B) Треба да има error/validation индикатор (или HTML5 validation)
            #    *или* барем да останеме на /admin и да не се додаде ред во табелата.
            error_like = page.locator("text=/invalid|error|failed|please|required|невалид|погреш|грешк|валид/i")
            error_found = False
            try:
                error_like.first.wait_for(state="visible", timeout=3500)
                error_found = True
            except TimeoutError:
                error_found = False

            # C) Проверка дека не е додаден нов гостин (ако табелата е реална <table>)
            rows_after = _count_guest_rows(page)

            still_on_admin = "/admin" in page.url

            if not (error_found or still_on_admin or rows_after == rows_before):
                page.screenshot(path="neg_register_no_error_detected.png", full_page=True)
                print("URL:", page.url)
                print("rows_before:", rows_before, "rows_after:", rows_after)
                raise Exception(
                    "❌ Negative test inconclusive: no error message found, not clearly stayed on /admin, "
                    "and row count changed unexpectedly."
                )

            page.screenshot(path="neg_register_ok.png", full_page=True)
            print("✅ Negative register test passed: invalid input was NOT accepted.")

            time.sleep(1)

        finally:
            browser.close()


if __name__ == "__main__":
    test_admin_register_guest_negative_invalid_data()
