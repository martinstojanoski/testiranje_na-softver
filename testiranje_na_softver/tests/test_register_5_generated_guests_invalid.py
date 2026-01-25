import time
import random
import string
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _rand_letters(n=6):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def _rand_password():
    return f"Aa{random.randint(10,99)}!{_rand_letters(6)}Z9"


def go_register_page(page):
    page.goto(f"{BASE_URL}/register", wait_until="domcontentloaded")
    page.wait_for_selector("text=Create account", timeout=7000)


def fill_register_form(page, fname, lname, username, email, phone, password, confirm_password):
    page.fill("input[name='first_name']", fname)
    page.fill("input[name='last_name']", lname)
    page.fill("input[name='username']", username)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)
    page.fill("input[name='password']", password)
    page.fill("input[name='confirm_password']", confirm_password)


def click_submit(page):
    page.click("button[type='submit']")


def assert_still_on_register(page):
    # останува на register ако е неуспешно/блокирано
    page.wait_for_selector("text=Create account", timeout=3000)


def assert_flash_error(page):
    page.wait_for_selector(".flash.error", timeout=6000)


# ------------------------------------------------------------
# NEGATIVE 1: Password mismatch (client-side JS alert + no submit)
# ------------------------------------------------------------
def test_register_password_mismatch_shows_alert_and_blocks_submit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        fname = "Martin"
        lname = "Test" + _rand_letters(3)
        username = "martin" + _rand_letters(4)  # letters-only
        email = f"martin.{lname.lower()}@test.local"
        phone = f"+3897{random.randint(1000000, 9999999)}"

        pwd = _rand_password()
        confirm = pwd + "X"  # mismatch намерно

        fill_register_form(page, fname, lname, username, email, phone, pwd, confirm)

        # Очекуваме JS alert: "❌ Passwords do not match!"
        dialog_message = None

        def handle_dialog(dialog):
            nonlocal dialog_message
            dialog_message = dialog.message
            dialog.accept()

        page.once("dialog", handle_dialog)
        click_submit(page)

        # Потврди дека има alert и дека е “mismatch”
        if not dialog_message:
            page.screenshot(path="neg_mismatch_no_alert.png")
            raise Exception("Expected mismatch alert, but no dialog appeared.")

        if "Passwords do not match" not in dialog_message:
            page.screenshot(path="neg_mismatch_wrong_alert.png")
            raise Exception(f"Unexpected alert message: {dialog_message}")

        # И остануваме на register (не треба да редиректира)
        assert_still_on_register(page)
        page.screenshot(path="neg_password_mismatch_ok.png")

        context.close()
        browser.close()


# ------------------------------------------------------------
# NEGATIVE 2: Invalid username (contains digits) -> HTML pattern blocks submit
# ------------------------------------------------------------
def test_register_username_with_digits_is_blocked_by_pattern():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        fname = "Ana"
        lname = "Test" + _rand_letters(3)
        username = "ana123"  # НЕ СМЕЕ - има цифри (pattern letters-only)
        email = f"ana.{lname.lower()}@test.local"
        phone = f"+3897{random.randint(1000000, 9999999)}"

        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)

        # Клик submit — browser треба да блокира (не се праќа форма)
        click_submit(page)

        # Најсигурно: уште сме на истата страна и “Create account” постои
        assert_still_on_register(page)

        # Дополнително: username input е invalid според constraint validation API
        is_invalid = page.eval_on_selector("input[name='username']", "el => !el.checkValidity()")
        if not is_invalid:
            page.screenshot(path="neg_username_digits_expected_invalid_but_valid.png")
            raise Exception("Expected username to be invalid by pattern, but checkValidity() returned valid.")

        page.screenshot(path="neg_username_digits_blocked_ok.png")

        context.close()
        browser.close()


# ------------------------------------------------------------
# NEGATIVE 3: Duplicate username/email -> server-side should return flash.error
# (Овој тест самиот прво регистрира валиден корисник, па пробува истите креденцијали)
# ------------------------------------------------------------
def test_register_duplicate_user_shows_flash_error():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1) Register a valid user
        go_register_page(page)

        fname = "Ivan"
        lname = "Dup" + _rand_letters(3)
        username = "ivan" + _rand_letters(4)  # letters-only
        email = f"ivan.{lname.lower()}@test.local"
        phone = f"+3897{random.randint(1000000, 9999999)}"
        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # success може да е flash.success или redirect на login; не форсираме многу
        # само да не е error во првиот обид
        try:
            page.wait_for_selector(".flash.error", timeout=2500)
            page.screenshot(path="neg_duplicate_setup_failed_first_register.png")
            raise Exception("First registration unexpectedly failed (flash.error shown).")
        except TimeoutError:
            pass

        # 2) Try to register SAME username/email again
        go_register_page(page)
        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # Очекуваме flash.error од backend (пример: "Username already exists" / "Email already exists")
        try:
            assert_flash_error(page)
        except TimeoutError:
            page.screenshot(path="neg_duplicate_expected_error_not_found.png")
            raise Exception("Expected flash.error on duplicate registration, but none was found.")

        page.screenshot(path="neg_duplicate_flash_error_ok.png")

        context.close()
        browser.close()


if __name__ == "__main__":
    test_register_password_mismatch_shows_alert_and_blocks_submit()
    test_register_username_with_digits_is_blocked_by_pattern()
    test_register_duplicate_user_shows_flash_error()
