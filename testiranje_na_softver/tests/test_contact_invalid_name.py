import time
from playwright.sync_api import sync_playwright, TimeoutError

def test_contact_invalid_name():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ----------------------
        # OPEN CONTACT PAGE
        # ----------------------
        page.goto("http://127.0.0.1:5000/contact")

        # ----------------------
        # FILL CONTACT FORM (INVALID NAME)
        # ----------------------
        Name = ""              # ❌ празно име (најчест негативен случај)
        # Name = "123456"      # алтернатива: само бројки
        Email = "martin@test.com"
        Message = "This message should NOT be sent because the name field is invalid."

        page.fill("input[name='name']", Name)
        page.fill("input[name='email']", Email)
        page.fill("textarea[name='message']", Message)

        page.click("button[type='submit']")

        # ----------------------
        # CHECK THAT SUCCESS MESSAGE DOES NOT APPEAR
        # ----------------------
        try:
            page.wait_for_selector(".flash.success", timeout=3000)
            page.screenshot(path="contact_invalid_name_but_success.png", full_page=True)
            raise Exception("❌ Invalid name accepted – success message should NOT appear.")
        except TimeoutError:
            # добро – success не се појавил
            pass

        # ----------------------
        # CHECK FOR ERROR MESSAGE (OPTIONAL BUT RECOMMENDED)
        # ----------------------
        try:
            page.wait_for_selector(".flash.error", timeout=3000)
            page.screenshot(path="contact_invalid_name_ok.png", full_page=True)
            print("✅ Negative contact test passed: invalid name correctly rejected.")
        except TimeoutError:
            page.screenshot(path="contact_invalid_name_no_message.png", full_page=True)
            print("⚠️ Invalid name rejected (no success), but no explicit error message found.")

        time.sleep(1)
        # browser.close()


if __name__ == "__main__":
    test_contact_invalid_name()
