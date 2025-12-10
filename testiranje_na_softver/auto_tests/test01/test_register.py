from playwright.sync_api import Page
import random
import string

def test_register_success(page: Page):

    # username: само букви + уникатност
    random_suffix = "".join(random.choice(string.ascii_letters) for _ in range(5))
    username = "User" + random_suffix
    password = "TestPass123"

    page.goto("http://127.0.0.1:5000/register")

    page.fill("#username", username)
    page.fill("#password", password)

    page.click("button[type='submit']")

    # backend redirect → /login
    page.wait_for_url("http://127.0.0.1:5000/login")

    assert "Login" in page.content()
