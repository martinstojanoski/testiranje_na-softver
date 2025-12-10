import time
from playwright.sync_api import sync_playwright, TimeoutError

def test_login_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        

        username = f"user" 
        password = "mypassword"

        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Wait for home page with welcome message
        try:
            page.wait_for_selector(f"text=Invalid credentials!", timeout=5000)
            page.screenshot(path="login_ok.png")
        except TimeoutError:
            page.screenshot(path="login_fail.png")
            raise Exception("Login failed!")

        print(f"Test Invalid credentials! Login successful.")


if __name__ == "__main__":
    test_login_invalid()