import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError


def generate_guest():
    first_names = ["Martin", "Ana", "Ivan", "Elena", "Stefan", "Marija"]
    last_names = ["Stojanoski", "Petrovski", "Ilievski", "Nikolova", "Trajkovski"]

    fname = random.choice(first_names)
    lname = random.choice(last_names)

    passport = f"M0{random.randint(100000, 999999)}"

    check_in = "2025-12-12"
    check_out = "2025-12-15"

    return fname, lname, passport, check_in, check_out


def test_register_multiple_guests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ----------------------
        # LOGIN AS ADMIN
        # ----------------------
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "adminpass")
        page.click("button[type='submit']")

        try:
            page.wait_for_selector("text=Welcome, admin!", timeout=5000)
            print("Admin login OK")
        except TimeoutError:
            page.screenshot(path="admin_login_fail.png")
            raise Exception("Admin login FAILED!")

        page.goto("http://127.0.0.1:5000/admin")

        # ----------------------
        # INSERT MULTIPLE GUESTS
        # ----------------------
        number_of_guests = 5  # колку гости да внесе

        for i in range(number_of_guests):
            fname, lname, passport, check_in, check_out = generate_guest()

            print(f"\n➡ Registering guest {i+1}: {fname} {lname}")

            page.fill("input[name='first_name']", fname)
            page.fill("input[name='last_name']", lname)
            page.fill("input[name='passport']", passport)
            page.fill("input[name='check_in']", check_in)
            page.fill("input[name='check_out']", check_out)

            page.click("button[type='submit']")

            # Check success message
            success_msg = f"Guest {fname} {lname} registered successfully."

            try:
                page.wait_for_selector(f"text={success_msg}", timeout=5000)
                print(f"✔ Successfully registered: {fname} {lname}")
                page.screenshot(path=f"guest_{i+1}_ok.png")
            except TimeoutError:
                page.screenshot(path=f"guest_{i+1}_fail.png")
                raise Exception(f"❌ FAILED registering: {fname} {lname}")

            # tiny pause
            time.sleep(0.5)

        print(f"\n🎉 SUCCESS — {number_of_guests} guests registered!")
        browser.close()


if __name__ == "__main__":
    test_register_multiple_guests()
