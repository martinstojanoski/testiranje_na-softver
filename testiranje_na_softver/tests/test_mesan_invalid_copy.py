import random
import string
import re
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
    page.wait_for_selector("form", timeout=10000)
    page.wait_for_selector("input[name='first_name']", timeout=10000)
    page.wait_for_selector("button[type='submit']", timeout=10000)


def fill_register_form_no_submit(page, fname, lname, username, email, phone, password, confirm_password):
    page.fill("input[name='first_name']", fname)
    page.fill("input[name='last_name']", lname)
    page.fill("input[name='username']", username)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)
    page.fill("input[name='password']", password)
    page.fill("input[name='confirm_password']", confirm_password)


def submit_register(page):
    # no_wait_after=True за да не "очекува" навигација
    page.click("button[type='submit']", no_wait_after=True)
    page.wait_for_timeout(500)


def assert_still_on_register(page):
    assert "/register" in page.url, f"Expected to stay on /register, but URL is: {page.url}"
    page.wait_for_selector("input[name='first_name']", timeout=7000)


# -----------------------------
# Validation helpers
# -----------------------------
def _safe_name(selector: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", selector)[:90]


def assert_no_novalidate(page):
    """
    Ако form има novalidate -> browser нема да блокира submit со HTML constraints.
    """
    has_novalidate = page.eval_on_selector("form", "f => f.hasAttribute('novalidate')")
    if has_novalidate:
        page.screenshot(path="FAIL_form_has_novalidate.png")
        raise Exception("❌ <form> има 'novalidate'. Избриши го за да работи HTML constraint validation.")


def assert_field_invalid(page, selector: str, screenshot_if_valid: str, hint: str = ""):
    """
    Проверува HTML constraint validation: el.checkValidity()
    Ако испадне VALID, снимаме screenshot и даваме јасен Exception.
    """
    count = page.locator(selector).count()
    if count == 0:
        page.screenshot(path=f"FAIL_missing_selector_{_safe_name(selector)}.png")
        raise Exception(f"❌ Selector not found: {selector}")

    is_invalid = page.eval_on_selector(selector, "el => !el.checkValidity()")
    if not is_invalid:
        page.screenshot(path=screenshot_if_valid)
        extra = f"\nHint: {hint}" if hint else ""
        raise Exception(
            f"❌ Expected INVALID field, but it is VALID -> {selector}.{extra}\n"
            f"Most likely: missing pattern/required/type OR form has novalidate."
        )


def assert_field_valid(page, selector: str, screenshot_if_invalid: str, hint: str = ""):
    """
    Корисно за случаи како password mismatch (кога HTML нема constraint за тоа)
    """
    count = page.locator(selector).count()
    if count == 0:
        page.screenshot(path=f"FAIL_missing_selector_{_safe_name(selector)}.png")
        raise Exception(f"❌ Selector not found: {selector}")

    is_valid = page.eval_on_selector(selector, "el => el.checkValidity()")
    if not is_valid:
        page.screenshot(path=screenshot_if_invalid)
        extra = f"\nHint: {hint}" if hint else ""
        raise Exception(f"❌ Expected VALID field, but it is INVALID -> {selector}.{extra}")


# ============================================================
# NEGATIVE CASES (FULL)
# ============================================================

def run_case(case_name: str, mutate_fn, invalid_selector: str, invalid_hint: str, ok_shot: str, fail_shot: str):
    """
    Generic runner:
    - Open /register
    - Ensure no novalidate
    - Fill form with mutated invalid value
    - Assert invalid field BEFORE submit
    - Submit
    - Assert still on /register
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # base valid data
        data = list(generate_register_user(0))
        # apply mutation to create invalid input
        mutate_fn(data)

        fname, lname, username, email, phone, password, confirm_password = data

        print(f"\n❌ {case_name}")

        go_register_page(page)
        assert_no_novalidate(page)

        fill_register_form_no_submit(page, fname, lname, username, email, phone, password, confirm_password)

        # check invalid BEFORE submit
        assert_field_invalid(
            page,
            invalid_selector,
            fail_shot,
            hint=invalid_hint
        )

        # submit and still on /register
        submit_register(page)
        assert_still_on_register(page)

        page.screenshot(path=ok_shot)

        context.close()
        browser.close()


def test_neg_1_first_name_has_digit():
    def mutate(data):
        data[0] = data[0] + "1"
    run_case(
        case_name="NEG 1: First name has digit (Martin1)",
        mutate_fn=mutate,
        invalid_selector="input[name='first_name']",
        invalid_hint="Add required + pattern='^[A-Za-zА-Яа-я]+$' на first_name.",
        ok_shot="OK_neg1_first_name_digit_blocked.png",
        fail_shot="FAIL_neg1_first_name_digit_expected_invalid_but_valid.png"
    )


def test_neg_2_last_name_has_punctuation():
    def mutate(data):
        data[1] = data[1] + ","
    run_case(
        case_name="NEG 2: Last name has punctuation (Trajkovski,)",
        mutate_fn=mutate,
        invalid_selector="input[name='last_name']",
        invalid_hint="Add required + pattern='^[A-Za-zА-Яа-я]+$' (или дозволи '-') на last_name.",
        ok_shot="OK_neg2_last_name_punct_blocked.png",
        fail_shot="FAIL_neg2_last_name_punct_expected_invalid_but_valid.png"
    )


def test_neg_3_email_invalid():
    def mutate(data):
        data[3] = "invalid-email@"
    run_case(
        case_name="NEG 3: Email invalid (invalid-email@)",
        mutate_fn=mutate,
        invalid_selector="input[name='email']",
        invalid_hint="Ensure email input has type='email' + required.",
        ok_shot="OK_neg3_email_blocked.png",
        fail_shot="FAIL_neg3_email_expected_invalid_but_valid.png"
    )


def test_neg_4_username_has_digit():
    def mutate(data):
        data[2] = data[2] + "7"
    run_case(
        case_name="NEG 4: Username has digit (letters-only violated)",
        mutate_fn=mutate,
        invalid_selector="input[name='username']",
        invalid_hint="Ensure username has required + pattern='^[A-Za-z]+$' (letters-only).",
        ok_shot="OK_neg4_username_digit_blocked.png",
        fail_shot="FAIL_neg4_username_digit_expected_invalid_but_valid.png"
    )


def test_neg_5_phone_has_letter():
    def mutate(data):
        data[4] = "+3897A" + str(random.randint(100000, 999999))
    run_case(
        case_name="NEG 5: Phone has letter (+3897Axxxxxx)",
        mutate_fn=mutate,
        invalid_selector="input[name='phone']",
        invalid_hint="Ensure phone has required + pattern='^\\+?[0-9]+$' (digits only).",
        ok_shot="OK_neg5_phone_letter_blocked.png",
        fail_shot="FAIL_neg5_phone_letter_expected_invalid_but_valid.png"
    )


# -----------------------------
# BONUS NEG 6: Password mismatch
# (ова најчесто НЕ е HTML constraint, туку backend check)
# -----------------------------
def test_neg_6_password_mismatch_backend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        fname, lname, username, email, phone, password, confirm_password = generate_register_user(6)
        confirm_password = password + "X"  # mismatch

        print("\n❌ NEG 6 (BONUS): Password mismatch -> expect to stay on /register (backend validation)")

        go_register_page(page)
        assert_no_novalidate(page)

        fill_register_form_no_submit(page, fname, lname, username, email, phone, password, confirm_password)

        # овде очекуваме полињата да се HTML-valid (обично нема constraint за mismatch)
        assert_field_valid(
            page,
            "input[name='password']",
            "FAIL_neg6_password_field_invalid.png",
            hint="Password field is unexpectedly invalid; check required/minlength/pattern."
        )
        assert_field_valid(
            page,
            "input[name='confirm_password']",
            "FAIL_neg6_confirm_password_field_invalid.png",
            hint="Confirm password field unexpectedly invalid; check required/minlength/pattern."
        )

        # submit => backend треба да врати назад на register со flash message
        submit_register(page)
        assert_still_on_register(page)

        # optional: ако имаш flash errors
        # page.wait_for_selector(".flash, .alert, .toast", timeout=3000)
        page.screenshot(path="OK_neg6_password_mismatch_blocked_backend.png")

        context.close()
        browser.close()


# -----------------------------
# Run all
# -----------------------------
if __name__ == "__main__":
    test_neg_1_first_name_has_digit()
    test_neg_2_last_name_has_punctuation()
    test_neg_3_email_invalid()
    test_neg_4_username_has_digit()
    test_neg_5_phone_has_letter()
    test_neg_6_password_mismatch_backend()

    print("\n✅ ALL negative register tests executed.")
