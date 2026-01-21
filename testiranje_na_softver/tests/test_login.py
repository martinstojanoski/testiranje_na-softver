import time
from playwright.sync_api import sync_playwright, TimeoutError

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 👉 ТУКА стави креденцијали што сигурно постојат во твојот систем
        username = "admin"
        password = "adminpass"

        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Проверка 1: да НЕ се појави 'Invalid credentials!'
        try:
            page.wait_for_selector("text=Invalid credentials!", timeout=5000)
            page.screenshot(path="login_valid_but_invalid.png", full_page=True)
            raise Exception("❌ Login failed: Invalid credentials message appeared.")
        except TimeoutError:
            pass   # добро – не се појавила грешка

        # Проверка 2: чекај некаков сигнал за успешен login
        success_locators = [
            "a[href*='logout']",
            "text=Logout",
            "text=Одјава",
            "text=Admin",
            f"text={username}",
        ]

        for sel in success_locators:
            try:
                page.wait_for_selector(sel, timeout=5000)
                page.screenshot(path="login_valid_ok.png", full_page=True)
                print(f"✅ Valid login successful. Found: {sel}")
                break
            except TimeoutError:
                continue
        else:
            page.screenshot(path="login_valid_fail.png", full_page=True)
            print("URL after login:", page.url)
            raise Exception("❌ Login failed: no success indicator found.")

        print(f"Test valid login successful: {username}")
        time.sleep(1)

        # browser.close()

if __name__ == "__main__":
    test_login()
