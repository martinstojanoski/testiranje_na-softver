import re

def test_username_validation():
    pattern = r"[A-Za-z]+"

    assert re.fullmatch(pattern, "Martin")
    assert re.fullmatch(pattern, "UserTest")

    assert not re.fullmatch(pattern, "User123")
    assert not re.fullmatch(pattern, "Test_")

from werkzeug.security import check_password_hash, generate_password_hash

def test_user_creation():
    users = {}
    username = "TestUser"
    password = "pass123"

    users[username] = generate_password_hash(password)

    assert username in users
    assert check_password_hash(users[username], password)

def test_guest_logic():
    guests = []

    guest = {
        "first_name": "John",
        "last_name": "Doe",
        "passport": "A1234567",
        "check_in": "2025-01-01",
        "check_out": "2025-01-05"
    }

    guests.append(guest)

    assert len(guests) == 1
    assert guests[0]["first_name"] == "John"
