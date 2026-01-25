import random
import string
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"


# -----------------------------
# Helpers (random test data)
# -----------------------------
def _rand_letters(n=6):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def _rand_username(base: str, i: int):
    # username мора да е letters-only (pattern="[A-Za-z]+")
    return f"{base}{_rand_letters(4)}{chr(65+i)}".lower()


def _rand_password():
    return f"Aa{random.randint(10,99)}!{_rand_letters(6)}Z9"


def generate_register_user(i: int):
    first_names = ["Martin", "Ana", "Ivan", "Elena", "Stefan", "Marija"]
    last_names = ["Stojanoski", "Petrovski", "Ilievski", "Nikolova", "Trajkovski"]

    fname = random.choice(first_names)
    lname = random.choice(last_names) + _rand_letters(3)

    username = _rand_username(fname, i)
    email = f"{fname.lower()}.{lname.lower()}.{i+1}@test.local"
    phone = f"+3897{random.randint(1000000, 9999999)}"

    password = _rand_password()
    confirm_password = password

    return fname, lname, username, email, phone, password, confirm_password


# -----------------------------
# Navigation & stable selectors
# -----------------------------
def go_register_page(page):
    page.goto(f"{BASE_URL}/register", wait_until="domcontentloaded")
    # НЕ бараме "Create account" текст. Бараме сигурен input.
    page.wait_for_selector("input[name='first_name']", timeout=10000)
    page.wait_for_selector("button[type='submit']", timeout=10000)


def fill_register_form(page, fname, lname, username, email, phone, password, confirm_password):
    page.fill("input[name='first_name']", fname)
    page.fill("input[name='last_name']", lname)
    page.fill("input[name='username']", username)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)
    page.fill("input[name='password']", password)
    page.fill("input[name='confirm_password']", confirm_password)

    # Submit (не претпоставуваме navigation, затоа само click + кратко чекање)
    page.click("button[type='submit']")
    page.wait_for_timeout(600)  # доволно за DOM update / flash / останување


def assert_still_on_register(page):
    # Во негативен тест очекуваме да остане на register
    assert "/register" in page.url, f"Expected to stay on /register, but URL is: {page.url}"
    page.wait_for_selector("input[name='first_name']", timeout=7000)


def _field_exists(page, selector: str) -> bool:
    return page.locator(selector).count() > 0


def assert_field_invalid(page, selector: str, screenshot_if_valid: str, hint: str = ""):
    """
    Проверува HTML constraint validation: el.checkValidity()
    Ако испадне VALID, снимаме screenshot и даваме јасен Exception.
    """
    if not _field_exists(page, selector):
        page.screenshot(path=f"missing_selector_{selector.replace('[','_').replace(']','_').replace('=','_')}.png")
        raise Exception(f"Selector not found: {selector}")

    is_invalid = page.eval_on_selector(selector, "el => !el.checkValidity()")

    if not is_invalid:
        page.screenshot(path=screenshot_if_valid)
        extra = f"\nHint: {hint}" if hint else ""
        raise Exception(
            f"Expected INVALID field, but it is VALID -> {selector}.{extra}\n"
            f"Most likely: your HTML input is missing pattern/required/type constraints."
        )


# ============================================================
# NEGATIVE CASES (5)
# ============================================================

def test_register_negative_1_first_name_has_digit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        fname, lname, username, email, phone, password, confirm_password = generate_register_user(0)
        fname = fname + "1"  # invalid

        print(f"\n❌ NEG 1: First name with digit -> {fname}")

        go_register_page(page)
        fill_register_form(page, fname, lname, username, email, phone, password, confirm_password)

        assert_still_on_register(page)
        assert_field_invalid(
            page,
            "input[name='first_name']",
            "neg1_first_name_digit_expected_invalid_but_valid.png",
            hint="Add pattern='^[A-Za-zА-Яа-я]+$' (или letters-only) + required на first_name input."
        )
        page.screenshot(path="neg1_first_name_digit_blocked_ok.png")

        context.close()
        browser.close()


def test_register_negative_2_last_name_has_punctuation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        fname, lname, username, email, phone, password, confirm_password = generate_register_user(1)
        lname = lname + ","  # invalid

        print(f"\n❌ NEG 2: Last name with punctuation -> {lname}")

        go_register_page(page)
        fill_register_form(page, fname, lname, username, email, phone, password, confirm_password)

        assert_still_on_register(page)
        assert_field_invalid(
            page,
            "input[name='last_name']",
            "neg2_last_name_punct_expected_invalid_but_valid.png",
            hint="Add pattern='^[A-Za-zА-Яа-я]+$' (или дозволи '-') и required на last_name input."
        )
        page.screenshot(path="neg2_last_name_punct_blocked_ok.png")

        context.close()
        browser.close()


def test_register_negative_3_email_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        fname, lname, username, email, phone, password, confirm_password = generate_register_user(2)
        email = "invalid-email@"  # invalid by type="email"

        print(f"\n❌ NEG 3: Invalid email -> {email}")

        go_register_page(page)
        fill_register_form(page, fname, lname, username, email, phone, password, confirm_password)

        assert_still_on_register(page)
        assert_field_invalid(
            page,
            "input[name='email']",
            "neg3_email_expected_invalid_but_valid.png",
            hint="Ensure your email input is type='email' and required."
        )
        page.screenshot(path="neg3_email_blocked_ok.png")

        context.close()
        browser.close()


def test_register_negative_4_username_has_digit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        fname, lname, username, email, phone, password, confirm_password = generate_register_user(3)
        username = username + "7"  # invalid (letters-only)

        print(f"\n❌ NEG 4: Username with digit -> {username}")

        go_register_page(page)
        fill_register_form(page, fname, lname, username, email, phone, password, confirm_password)

        assert_still_on_register(page)
        assert_field_invalid(
            page,
            "input[name='username']",
            "neg4_username_expected_invalid_but_valid.png",
            hint="Ensure username has pattern='^[A-Za-z]+$' (letters-only) and required."
        )
        page.screenshot(path="neg4_username_digit_blocked_ok.png")

        context.close()
        browser.close()


def test_register_negative_5_phone_has_letter():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        fname, lname, username, email, phone, password, confirm_password = generate_register_user(4)
        phone = "+3897A" + str(random.randint(100000, 999999))  # invalid

        print(f"\n❌ NEG 5: Phone with letter -> {phone}")

        go_register_page(page)
        fill_register_form(page, fname, lname, username, email, phone, password, confirm_password)

        assert_still_on_register(page)
        assert_field_invalid(
            page,
            "input[name='phone']",
            "neg5_phone_letter_expected_invalid_but_valid.png",
            hint="Ensure phone has pattern='^\\+?[0-9]+$' (digits only) and required."
        )
        page.screenshot(path="neg5_phone_letter_blocked_ok.png")

        context.close()
        browser.close()


# -----------------------------
# Run all
# -----------------------------
if __name__ == "__main__":
    test_register_negative_1_first_name_has_digit()
    test_register_negative_2_last_name_has_punctuation()
    test_register_negative_3_email_invalid()
    test_register_negative_4_username_has_digit()
    test_register_negative_5_phone_has_letter()

    print("\n✅ All negative registration checks executed.")
