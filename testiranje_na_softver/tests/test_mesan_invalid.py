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


def assert_field_invalid(page, selector: str, screenshot_name: str):
    """
    Проверува HTML5 constraint validation (pattern/type/required) дали го прави полето invalid.
    Ако полето е валидно, значи немаш constraint на тоа поле (или е дозволено) -> тестот ќе падне (со screenshot).
    """
    is_invalid = page.eval_on_selector(selector, "el => !el.checkValidity()")
    if not is_invalid:
        page.screenshot(path=screenshot_name)
        raise Exception(f"Expected field to be INVALID, but it is valid: {selector}")


def assert_field_valid(page, selector: str, screenshot_name: str):
    """
    Проверува дали полето е валидно (корисно за sanity).
    """
    is_valid = page.eval_on_selector(selector, "el => el.checkValidity()")
    if not is_valid:
        page.screenshot(path=screenshot_name)
        raise Exception(f"Expected field to be VALID, but it is invalid: {selector}")


# ============================================================
# 1) ЗГРЕШЕНО: бројка во името (First Name)
# ============================================================
def test_register_first_name_with_digit_is_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        # намерно грешно име со бројка
        fname = "Mart1n"
        lname = "Test" + _rand_letters(3)
        username = "martin" + _rand_letters(4)  # letters-only
        email = f"martin.{lname.lower()}@test.local"
        phone = f"+3897{random.randint(1000000, 9999999)}"
        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # ако имаш HTML pattern/constraint на first_name, треба да биде invalid
        assert_field_invalid(page, "input[name='first_name']", "neg_first_name_digit_expected_invalid_but_valid.png")

        # и треба да останеме на register
        assert_still_on_register(page)
        page.screenshot(path="neg_first_name_digit_blocked_ok.png")

        context.close()
        browser.close()


# ============================================================
# 2) ЗГРЕШЕНО: интерпункциски знак во презимето (Last Name)
# ============================================================
def test_register_last_name_with_punctuation_is_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        fname = "Ana"
        # намерно со интерпункција
        lname = "Stojan,oski"
        username = "ana" + _rand_letters(5)  # letters-only
        email = f"ana.{_rand_letters(5)}@test.local"
        phone = f"+3897{random.randint(1000000, 9999999)}"
        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # ако имаш HTML constraint на last_name, треба да биде invalid
        assert_field_invalid(page, "input[name='last_name']", "neg_last_name_punct_expected_invalid_but_valid.png")

        assert_still_on_register(page)
        page.screenshot(path="neg_last_name_punct_blocked_ok.png")

        context.close()
        browser.close()


# ============================================================
# 3) ЗГРЕШЕНО: невалидна email адреса
# ============================================================
def test_register_invalid_email_is_blocked_by_email_type():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        fname = "Ivan"
        lname = "Test" + _rand_letters(3)
        username = "ivan" + _rand_letters(4)
        # намерно невалиден email
        email = "ivan..test@"
        phone = f"+3897{random.randint(1000000, 9999999)}"
        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # email type="email" треба да го направи invalid
        assert_field_invalid(page, "input[name='email']", "neg_email_invalid_expected_invalid_but_valid.png")

        assert_still_on_register(page)
        page.screenshot(path="neg_email_invalid_blocked_ok.png")

        context.close()
        browser.close()


# ============================================================
# 4) ЗГРЕШЕНО: корисничко име со бројка (username pattern letters-only)
# ============================================================
def test_register_username_with_digit_is_blocked_by_pattern():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        fname = "Elena"
        lname = "Test" + _rand_letters(3)
        # намерно username со бројка
        username = "elena1"
        email = f"elena.{_rand_letters(6)}@test.local"
        phone = f"+3897{random.randint(1000000, 9999999)}"
        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # ова треба 100% да биде invalid поради pattern="[A-Za-z]+"
        assert_field_invalid(page, "input[name='username']", "neg_username_digit_expected_invalid_but_valid.png")

        assert_still_on_register(page)
        page.screenshot(path="neg_username_digit_blocked_ok.png")

        context.close()
        browser.close()


# ============================================================
# 5) ЗГРЕШЕНО: телефонски број со буква
# ============================================================
def test_register_phone_with_letter_is_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        go_register_page(page)

        fname = "Stefan"
        lname = "Test" + _rand_letters(3)
        username = "stefan" + _rand_letters(4)
        email = f"stefan.{_rand_letters(6)}@test.local"
        # намерно телефон со буква
        phone = "+3897A234567"
        pwd = _rand_password()

        fill_register_form(page, fname, lname, username, email, phone, pwd, pwd)
        click_submit(page)

        # ако имаш HTML constraint/pattern за телефон, треба да биде invalid
        assert_field_invalid(page, "input[name='phone']", "neg_phone_letter_expected_invalid_but_valid.png")

        assert_still_on_register(page)
        page.screenshot(path="neg_phone_letter_blocked_ok.png")

        context.close()
        browser.close()


if __name__ == "__main__":
    test_register_first_name_with_digit_is_invalid()
    test_register_last_name_with_punctuation_is_invalid()
    test_register_invalid_email_is_blocked_by_email_type()
    test_register_username_with_digit_is_blocked_by_pattern()
    test_register_phone_with_letter_is_invalid()
