from playwright.sync_api import sync_playwright

def test_click_button_counter():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # open visible browser
        page = browser.new_page()

        # Open login page
        page.goto("http://127.0.0.1:5000/login")

        # Locate button and counter
        button_selector = "#clickBtn"
        counter_selector = "#count"

        # Initial counter value
        initial_count = int(page.inner_text(counter_selector))
        print(f"Initial counter: {initial_count}")

        # Number of clicks to test
        clicks = 50
        for _ in range(clicks):
            page.wait_for_timeout(1000)  # 0.5 sec
            page.click(button_selector)

        # Wait a little for counter to update via JS/fetch
        page.wait_for_timeout(3500)  # 0.5 sec

        # Get final counter value
        final_count = int(page.inner_text(counter_selector))
        print(f"Final counter after {clicks} clicks: {final_count}")

        # Verify counter incremented correctly
        assert final_count == initial_count + clicks, "Counter did not increment correctly!"

        browser.close()


if __name__ == "__main__":
    test_click_button_counter()
