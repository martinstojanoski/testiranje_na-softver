from playwright.sync_api import sync_playwright

def test_user_register():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("http://127.0.0.1:5000/register")

        page.fill("input[name='username']", "newuser123")
        page.fill("input[name='password']", "pass123")
        page.click("button[type='submit']")

        # After registering, it redirects to the login page
        assert "/login" in page.url

        browser.close()

if __name__ == "__main__":
    test_user_register()
