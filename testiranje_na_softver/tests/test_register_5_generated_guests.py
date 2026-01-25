import time
import random
import string
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _rand_letters(n=6):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def _rand_username(base: str, i: int):
    # username мора да е letters-only (pattern="[A-Za-z]+")
    # затоа користиме само букви
    return f"{base}{_rand_letters(4)}{chr(65+i)}".lower()  # пример: martinabczdE


def _rand_password():
    # силна лозинка (ќе ја прифати твојот UI без проблем)
    # mix: Upper + lower + digits + symbol, length >= 12
    return f"Aa{random.randint(10,99)}!{_rand_letters(6)}Z9"


def generate_register_user(i: int):
    first_names = ["Martin", "Ana", "Ivan", "Elena", "Stefan", "Marija"]
    last_names = ["Stojanoski", "Petrovski", "Ilievski", "Nikolova", "Trajkovski"]

    fname = random.choice(first_names)
    lname = random.choice(last_names) + _rand_letters(3)

    username = _rand_username(fname, i)

    # уникатен email за секој корисник
    email = f"{fname.lower()}.{lname.lower()}.{i+1}@test.local"

    phone = f"+3897{random.randint(1000000, 9999999)}"

    password = _rand_password()
    confirm_password = password

    return fname, lname, username, email, phone, password, confirm_password


def go_register_page(page):
    # рута за register кај тебе (најчесто /register)
    page.goto(f"{BASE_URL}/register", wait_until="domcontentloaded")

    # индикатор дека сме на register страната (од твојот template)
    page.wait_for_selector("text=Create account", timeout=7000)


def fill_register_form(page, fname, lname, username, email, phone, password, confirm_password):
    # Стабилни селектори по name атрибут (како во твојот HTML)
    page.fill("input[name='first_name']", fname)
    page.fill("input[name='last_name']", lname)
    page.fill("input[name='username']", username)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)
    page.fill("input[name='password']", password)
    page.fill("input[name='confirm_password']", confirm_password)

    # submit
    page.click("button[type='submit']")


def assert_register_success(page, username, email):
    """
    Најсигурно е да провериме нешто уникатно (email или username).
    Твојот template има flash категории: success/error/info.
    """

    # 1) Ако има flash success порака
    try:
        page.wait_for_selector(".flash.success", timeout=4000)
        return
    except TimeoutError:
        pass

    # 2) Ако нема flash, пробај да видиш дали те префрлил на login
    # (честа пракса: "You can sign in right after registration." -> redirect /login)
    try:
        page.wait_for_selector("text=Login", timeout=2500)
        return
    except TimeoutError:
        pass

    # 3) Провери дали email/username се појавуваат некаде на страницата (ретко, ама корисно)
    try:
        page.wait_for_selector(f"text={email}", timeout=2500)
        return
    except TimeoutError:
        pass

    try:
        page.wait_for_selector(f"text={username}", timeout=2500)
        return
    except TimeoutError:
        pass

    # Ако ништо не успее, слика и фејл
    safe_email = email.replace("@", "_at_").replace(".", "_")
    page.screenshot(path=f"register_verify_fail_{safe_email}.png")
    raise Exception(f"Registration NOT verified for user: {username} | {email}")


def test_register_5_generated_guests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        number_of_users = 5

        for i in range(number_of_users):
            fname, lname, username, email, phone, password, confirm_password = generate_register_user(i)

            print(f"\n➡ Register {i+1}: {fname} {lname} | {username} | {email}")

            go_register_page(page)
            fill_register_form(page, fname, lname, username, email, phone, password, confirm_password)

            assert_register_success(page, username, email)

            safe_email = email.replace("@", "_at_").replace(".", "_")
            page.screenshot(path=f"register_{i+1}_ok_{safe_email}.png")
            print(f"✔ Successfully registered and verified: {username} | {email}")

            time.sleep(0.4)

        print(f"\n🎉 SUCCESS — {number_of_users} registrations submitted and verified!")
        context.close()
        browser.close()


if __name__ == "__main__":
    test_register_5_generated_guests()
