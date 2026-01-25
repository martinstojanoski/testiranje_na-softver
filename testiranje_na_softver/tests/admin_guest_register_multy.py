import time
import random
import string
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def _rand_letters(n=6):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def generate_guest(i: int):
    first_names = ["Martin", "Ana", "Ivan", "Elena", "Stefan", "Marija"]
    last_names = ["Stojanoski", "Petrovski", "Ilievski", "Nikolova", "Trajkovski"]

    fname = random.choice(first_names)
    # правиме уникатно презиме за да нема забуна во UI/табела/статус
    lname = random.choice(last_names) + _rand_letters(3)

    # уникатен email (најдобро за проверка)
    email = f"{fname.lower()}.{lname.lower()}.{i+1}@test.local"

    # “валиден” телефон (пример формат)
    phone = f"+3897{random.randint(1000000, 9999999)}"

    checkin = "2026-12-12"
    checkout = "2026-12-15"

    return fname, lname, email, phone, checkin, checkout


def go_checkin_page(page):
    # тука стави точната рута за booking/checkin страницата кај тебе
    # пример: "/booking" или "/checkin" итн.
    page.goto(f"{BASE_URL}/booking", wait_until="domcontentloaded")

    # индикатор дека сме на вистинска страна
    page.wait_for_selector("text=Guest Check-In", timeout=7000)


def fill_checkin_form(page, fname, lname, email, phone, checkin, checkout):
    # Стабилни селектори по NAME (како во твојот template)
    page.fill("input[name='first_name']", fname)
    page.fill("input[name='last_name']", lname)
    page.fill("input[name='email']", email)
    page.fill("input[name='phone']", phone)

    page.fill("input[name='checkin_date']", checkin)
    page.fill("input[name='checkout_date']", checkout)

    page.click("button[type='submit']")


def assert_success(page, email):
    """
    Најсигурно е да провериме преку нешто што е уникатно — email.
    Ова може да е:
    - flash порака што го содржи email-от
    - или booking status страница каде се гледа email-от
    """

    # 1) Пробај ако имаш flash success што покажува "success" класа
    # (ако користиш Flask flash категории како: success/error/info)
    try:
        page.wait_for_selector(".flash.success", timeout=2500)
        return
    except TimeoutError:
        pass

    # 2) Ако нема flash, пробај да видиш дали email се појавува на страницата
    # (пример ако покажува резиме/табела)
    try:
        page.wait_for_selector(f"text={email}", timeout=2500)
        return
    except TimeoutError:
        pass

    # 3) Ако не покажува ништо, оди на Booking Status и провери таму (ако е достапно)
    # Ова е најреално за твојот проект (имаш линк "Booking Status").
    try:
        page.goto(f"{BASE_URL}/booking_status", wait_until="domcontentloaded")
        # Ако има поле за email за проверка на статус:
        if page.locator("input[name='email']").count() > 0:
            page.fill("input[name='email']", email)
            page.click("button[type='submit']")
        page.wait_for_selector(f"text={email}", timeout=7000)
        return
    except TimeoutError:
        page.screenshot(path=f"checkin_verify_fail_{email}.png")
        raise Exception(f"Check-in NOT verified for email: {email}")


def test_register_multiple_checkins():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        number_of_guests = 5

        for i in range(number_of_guests):
            fname, lname, email, phone, checkin, checkout = generate_guest(i)

            print(f"\n➡ Check-in {i+1}: {fname} {lname} | {email}")

            go_checkin_page(page)
            fill_checkin_form(page, fname, lname, email, phone, checkin, checkout)

            assert_success(page, email)

            page.screenshot(path=f"checkin_{i+1}_ok_{email.replace('@','_')}.png")
            print(f"✔ Successfully checked-in and verified: {email}")

            time.sleep(0.4)

        print(f"\n🎉 SUCCESS — {number_of_guests} check-ins submitted and verified!")
        context.close()
        browser.close()


if __name__ == "__main__":
    test_register_multiple_checkins()
