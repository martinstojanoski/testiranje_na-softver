import time
from playwright.sync_api import sync_playwright, TimeoutError

def test_contact():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ----------------------
        # OPEN CONTACT PAGE
        # ----------------------
        page.goto("http://127.0.0.1:5000/contact")

        # ----------------------
        # FILL CONTACT FORM
        # ----------------------
        Name = "Martin"
        Email = "martin@test.com"
        Message = "Hello, this is a test message sent via Playwright automation."

        page.fill("input[name='name']", Name)
        page.fill("input[name='email']", Email)
        page.fill("textarea[name='message']", Message)

        page.click("button[type='submit']")

        # ----------------------
        # WAIT FOR SUCCESS MESSAGE
        # ----------------------
        try:
            page.wait_for_selector(".flash.success", timeout=5000)
            page.screenshot(path="contact_ok.png")
        except TimeoutError:
            page.screenshot(path="contact_fail.png")
            raise Exception("Contact form submission failed or success message not found!")

        print(f"Contact message sent successfully by: {Name}")

        time.sleep(1)
        # browser.close()


if __name__ == "__main__":
    test_contact()
