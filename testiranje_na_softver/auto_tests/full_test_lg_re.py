import time
from playwright.sync_api import sync_playwright, TimeoutError

def register_and_login_multiple_users(number_of_users=5):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for i in range(number_of_users):
            username = f"user{i}_{int(time.time())}"  # unique username
            password = "mypassword"

            print(f"\n=== Processing user {i+1}/{number_of_users}: {username} ===")

            # ----------------------
            # REGISTER
            # ----------------------
            page.goto("http://127.0.0.1:5000/register")
            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")

            try:
                page.wait_for_selector("input[name='username']", timeout=5000)
            except TimeoutError:
                page.screenshot(path=f"register_fail_user{i}.png")
                print(f"Registration failed for {username}")
                continue

            assert "/login" in page.url
            print(f"Registration successful: {username}")

            time.sleep(1)  # optional delay

            # ----------------------
            # LOGIN
            # ----------------------
            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")

            try:
                page.wait_for_selector(f"text=Welcome, {username}!", timeout=5000)
                
            except TimeoutError:
                page.screenshot(path=f"login_fail_user{i}.png")
                print(f"Login failed for {username}")
                continue

            print(f"Login successful: {username}")

            time.sleep(1)  # optional delay

            # ----------------------
            # LOGOUT
            # ----------------------
            page.click("a[href='/logout']")
            try:
                page.wait_for_selector("input[name='username']", timeout=5000)
            except TimeoutError:
                page.screenshot(path=f"logout_fail_user{i}.png")
                print(f"Logout failed for {username}")
                continue

            assert "/login" in page.url
            print(f"Logout successful: {username}")

            # Short delay before next user
            time.sleep(1)

        browser.close()
        print("\n=== All users processed ===")


if __name__ == "__main__":
    register_and_login_multiple_users(number_of_users=5)
