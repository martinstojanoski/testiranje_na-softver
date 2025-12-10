def test_register_success(client):
    response = client.post("/register", data={
        "username": "TestUserA",
        "password": "pass123"
    })

    # Expect redirect to login
    assert response.status_code == 302
    assert "/login" in response.location


def test_register_invalid_username(client):
    response = client.post("/register", data={
        "username": "User123",
        "password": "pass123"
    })

    assert b"Invalid username" in response.data
def test_register_existing_user(client):
    client.post("/register", data={"username": "John", "password": "pass"})  # create
    response = client.post("/register", data={"username": "John", "password": "pass"})

    assert b"User already exists" in response.data


def test_login_success(client):
    client.post("/register", data={"username": "Ana", "password": "pass123"})

    response = client.post("/login", data={
        "username": "Ana",
        "password": "pass123"
    })

    # Expect redirect to home
    assert response.status_code == 302
    assert "/" in response.location

def test_login_invalid(client):
    response = client.post("/login", data={
        "username": "no_user",
        "password": "wrong"
    })

    assert b"Invalid credentials" in response.data

def test_admin_not_logged_in(client):
    response = client.get("/admin")

    # Expect redirect to login
    assert response.status_code == 302
    assert "/login" in response.location
def test_add_guest(client):

    # First login as admin
    client.post("/login", data={
        "username": "admin",
        "password": "adminpass"
    })

    # Add guest
    response = client.post("/admin", data={
        "first_name": "Ivan",
        "last_name": "Petrov",
        "passport": "12345",
        "check_in": "2025-02-01",
        "check_out": "2025-02-05"
    }, follow_redirects=True)

    assert b"registered successfully" in response.data

