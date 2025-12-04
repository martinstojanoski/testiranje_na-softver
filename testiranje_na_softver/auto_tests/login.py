from playwright.sync_api import sync_playwright

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # <-- UI mode
        page = browser.new_page()

        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "testuser")
        page.fill("input[name='password']", "testpass")
        page.click("button[type='submit']")

        browser.close()

if __name__ == "__main__":
    test_login()
