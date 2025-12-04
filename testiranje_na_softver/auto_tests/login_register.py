import time
from playwright.sync_api import sync_playwright, TimeoutError

def test_register_and_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ----------------------
        # REGISTER
        # ----------------------
        username = f"user{int(time.time())}"  # unique username
        password = "mypassword"

        page.goto("http://127.0.0.1:5000/register")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Wait for redirect to login
        try:
            page.wait_for_selector("input[name='username']", timeout=5000)
        except TimeoutError:
            page.screenshot(path="register_fail.png")
            raise Exception("Registration failed or login page not loaded!")

        assert "/login" in page.url
        print(f"Registration successful: {username}")

        time.sleep(1)

        # ----------------------
        # LOGIN
        # ----------------------
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Wait for home page with welcome message
        try:
            page.wait_for_selector(f"text=Welcome, {username}!", timeout=5000)
            page.screenshot(path="login_ok.png")
        except TimeoutError:
            page.screenshot(path="login_fail.png")
            raise Exception("Login failed or welcome message not found!")

        print(f"Login successful: {username}")

        # Optional: logout
        page.click("a[href='/logout']")
        page.wait_for_selector("input[name='username']", timeout=5000)
        assert "/login" in page.url
        page.screenshot(path="login_ok_logout.png")
        print(f"Logout successful: {username}")

        browser.close()


if __name__ == "__main__":
    test_register_and_login()
