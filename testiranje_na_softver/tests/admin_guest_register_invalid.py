import time
from playwright.sync_api import sync_playwright, TimeoutError

from datetime import datetime

def admin_guest_register_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        username = f"admin"
        password = "adminpass"
        # ----------------------
        # LOGIN
        # ----------------------
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Wait for home page with welcome message
        try:
            page.wait_for_selector(f"text=Welcome, {username}!", timeout=5000)
            page.screenshot(path="login_ok.png")
        except TimeoutError:
            page.screenshot(path="admin_guest_register_invalid.png")
            raise Exception("Login failed or welcome message not found!")

        print(f"Login successful: {username}")

        page.goto("http://127.0.0.1:5000/admin")

        # ----------------------
        # REGISTER
        # ----------------------
        Ime="Martin1"
        Prezime="Stojanoskii"
        Broj_Pasos="M0123456"
        
        Check_in_raw = "12/12/2025"
        Check_in = datetime.strptime(Check_in_raw, "%d/%m/%Y").strftime("%Y-%m-%d")


        Check_out_raw = "15/12/2025"
        Check_out = datetime.strptime(Check_out_raw, "%d/%m/%Y").strftime("%Y-%m-%d")

        

        page.fill("input[name='first_name']", Ime)
        page.fill("input[name='last_name']", Prezime)
        page.fill("input[name='passport']", Broj_Pasos)
        
        page.fill("input[name='check_in']", Check_in)
        page.fill("input[name='check_out']", Check_out)

        page.click("button[type='submit']")

        # Wait for redirect to login
        try:
            page.wait_for_selector(f"text=First name and last name must contain only letters", timeout=5000)
        except TimeoutError:
            page.screenshot(path="admin_guest_register_invalid_fail.png")
            raise Exception("Registration failed or login page not loaded!")
            
        print(f"Registration successful: {Ime}")

        time.sleep(10)

        # browser.close()

if __name__ == "__main__":
    admin_guest_register_invalid()