from playwright.sync_api import sync_playwright, TimeoutError

def test_admin_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # стави тука точни креденцијали што постојат во твојот систем
        username = "admin"
        password = "adminpass"

        page.goto("http://127.0.0.1:5000/login", wait_until="domcontentloaded")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)

        page.click("button[type='submit']")

        # Проверка 1: да нема 'Invalid credentials!'
        try:
            page.wait_for_selector("text=Invalid credentials!", timeout=5000)
            page.screenshot(path="login_valid_but_invalid_msg.png", full_page=True)
            raise Exception("❌ Login failed: 'Invalid credentials!' displayed.")
        except TimeoutError:
            pass  # добро - не се појавило

        # Проверка 2: барем еден „успешен сигнал“
        success_locators = [
            "a[href*='logout']",
            "text=Logout",
            "text=Одјава",
            "text=Admin",
            f"text={username}",
        ]

        for sel in success_locators:
            try:
                page.wait_for_selector(sel, timeout=3000)
                page.screenshot(path="login_valid_ok.png", full_page=True)
                print(f"✅ Positive login test passed. Found: {sel}")
                break
            except TimeoutError:
                continue
        else:
            page.screenshot(path="login_valid_uncertain.png", full_page=True)
            print("URL after login:", page.url)
            raise Exception("❌ Login may have failed: no success indicator found.")

        # browser.close()

if __name__ == "__main__":
    test_admin_login()
    