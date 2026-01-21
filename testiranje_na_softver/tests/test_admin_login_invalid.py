from playwright.sync_api import sync_playwright, TimeoutError

def test_admin_login_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # намерно невалидни креденцијали
        username = "admin"
        password = "wrongpass"

        page.goto("http://127.0.0.1:5000/login", wait_until="domcontentloaded")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Проверка 1: мора да се појави 'Invalid credentials!'
        try:
            page.wait_for_selector("text=Invalid credentials!", timeout=5000)
            page.screenshot(path="login_invalid_ok.png", full_page=True)
            print("✅ Negative login test passed: 'Invalid credentials!' displayed.")
        except TimeoutError:
            page.screenshot(path="login_invalid_fail.png", full_page=True)
            print("URL after invalid login:", page.url)
            raise Exception("❌ Negative login test failed: expected 'Invalid credentials!' not found.")

        # Проверка 2: да НЕ се појават успешни сигнали (опционално, но добро за семинарска)
        forbidden_success_locators = [
            "a[href*='logout']",
            "text=Logout",
            "text=Одјава",
            "text=Admin",
        ]

        for sel in forbidden_success_locators:
            if page.locator(sel).count() > 0:
                page.screenshot(path="login_invalid_but_success_visible.png", full_page=True)
                raise Exception(f"❌ Unexpected success indicator visible after invalid login: {sel}")

        # browser.close()

if __name__ == "__main__":
    test_admin_login_invalid()
