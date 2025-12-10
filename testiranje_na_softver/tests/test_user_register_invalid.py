import time
from playwright.sync_api import sync_playwright

def test_user_register_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("http://127.0.0.1:5000/register")

        page.fill("input[name='username']", "newuser123")
        page.fill("input[name='password']", "pass123")
        page.click("button[type='submit']")

        time.sleep(3)


        try:
            page.wait_for_selector("input[title='Only letters allowed']")
            page.screenshot(path="test_user_registration_invalid.png")
        except TimeoutError:
            page.screenshot(path="register_fail.png")
            raise Exception("Registration failed or login page not loaded!")

        print(f"Invalid test Registration successful:")


        browser.close()

if __name__ == "__main__":
    test_user_register_invalid()
