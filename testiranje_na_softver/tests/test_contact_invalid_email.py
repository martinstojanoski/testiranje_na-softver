import time
from playwright.sync_api import sync_playwright, TimeoutError

def test_contact_invalid_email():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ----------------------
        # OPEN CONTACT PAGE
        # ----------------------
        page.goto("http://127.0.0.1:5000/contact")

        # ----------------------
        # FILL CONTACT FORM (INVALID EMAIL)
        # ----------------------
        Name = "Martin"
        Email = "invalid-email"   # ❌ невалиден формат
        Message = "This message should NOT be sent because the email is invalid."

        page.fill("input[name='name']", Name)
        page.fill("input[name='email']", Email)
        page.fill("textarea[name='message']", Message)

        page.click("button[type='submit']")

        # ----------------------
        # CHECK THAT SUCCESS MESSAGE DOES NOT APPEAR
        # ----------------------
        try:
            # ако се појави success → тестот треба да падне
            page.wait_for_selector(".flash.success", timeout=3000)
            page.screenshot(path="contact_invalid_but_success.png", full_page=True)
            raise Exception("❌ Invalid email accepted – success message should NOT appear.")
        except TimeoutError:
            # добро – не се појавил success
            pass

        # ----------------------
        # CHECK FOR ERROR MESSAGE (OPTIONAL BUT RECOMMENDED)
        # ----------------------
        try:
            page.wait_for_selector(".flash.error", timeout=3000)
            page.screenshot(path="contact_invalid_ok.png", full_page=True)
            print("✅ Negative contact test passed: invalid email correctly rejected.")
        except TimeoutError:
            # ако немаш error flash, сепак барем знаеме дека success не се појавил
            page.screenshot(path="contact_invalid_no_message.png", full_page=True)
            print("⚠️ Invalid email rejected (no success), but no explicit error message found.")

        time.sleep(1)
        # browser.close()


if __name__ == "__main__":
    test_contact_invalid_email()
