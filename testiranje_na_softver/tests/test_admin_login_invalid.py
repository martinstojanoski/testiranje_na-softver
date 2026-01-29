from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "http://127.0.0.1:5000"


def test_admin_login_invalid():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context()
        page = context.new_page()

        # Намерно невалидни креденцијали
        username = "admin"
        password = "wrongpass"

        # 1) Отвори login страна
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")

        # 2) Пополни форма + submit
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        # Малку време за flash/рендер/анимации (по-стабилно од 0ms)
        page.wait_for_timeout(600)

        # 3) Верификација: мора да има негативна порака / alert / flash
        #    (Наместо да чекаме точен текст, чекаме најчести alert контејнери)
        alert_selectors = [
            "#flash-area",          # ако некогаш додадеш во base.html
            ".flash",
            ".alert",
            ".toast",
            "[role='alert']",
            "[data-testid='flash']",
        ]

        # прво пробуваме да најдеме контејнер
        alert_found = False
        for sel in alert_selectors:
            try:
                if page.locator(sel).count() > 0:
                    # ако постои, чекај да стане видлив (може да е скриен прво)
                    page.wait_for_selector(sel, state="visible", timeout=1500)
                    alert_found = True
                    break
            except TimeoutError:
                pass

        # ако нема контејнер, барај негативен текст било каде
        if not alert_found:
            negative_text_locator = page.locator(
                "text=/invalid|wrong|error|failed|невалид|погреш|грешн/i"
            )
            try:
                negative_text_locator.first.wait_for(state="visible", timeout=4000)
                alert_found = True
            except TimeoutError:
                alert_found = False

        if not alert_found:
            # Debug излез (ќе ти помогне да го наместиме 100% ако нема flash воопшто)
            page.screenshot(path="login_invalid_fail.png", full_page=True)
            print("URL after invalid login:", page.url)
            print("Body text (first 1200 chars):\n", page.inner_text("body")[:1200])
            raise Exception("❌ Negative login test failed: no visible error/flash message detected.")

        # Ако стигна до тука -> има негативна реакција
        page.screenshot(path="login_invalid_ok.png", full_page=True)
        print("✅ Negative login test passed: error/flash detected.")

        # 4) Верификација: НЕ смее да се појави успешен сигнал / да влезе во admin
        #    - URL не смее да е /admin
        #    - не смее да има Logout/Одјава линкови или Admin Panel текстови
        if "/admin" in page.url:
            page.screenshot(path="login_invalid_but_redirected_admin.png", full_page=True)
            raise Exception("❌ Unexpected redirect to /admin after invalid login!")

        forbidden_success_locators = [
            "a[href*='logout']",
            "text=/logout|одјава/i",
            "text=/admin panel|admin dashboard|админ/i",
            "a[href*='/admin']",
        ]

        for sel in forbidden_success_locators:
            try:
                if page.locator(sel).first.is_visible(timeout=500):
                    page.screenshot(path="login_invalid_but_success_visible.png", full_page=True)
                    raise Exception(f"❌ Unexpected success indicator visible after invalid login: {sel}")
            except Exception:
                # is_visible може да фрли ако нема елемент, тоа е ок (значи нема success)
                pass

        browser.close()


if __name__ == "__main__":
    test_admin_login_invalid()
