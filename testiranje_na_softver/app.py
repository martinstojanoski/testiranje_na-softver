from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# -------------------
# Storage
# -------------------
users = {}  # admin + normal users
guests = []  # list of guest dicts

# Admin
admin_user = "admin"
admin_password = generate_password_hash("adminpass")
users[admin_user] = admin_password

# -------------------
# ROUTES
# -------------------

@app.route("/")
def home():
    if "user" in session:
        return render_template("home.html", user=session["user"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and check_password_hash(users[username], password):
            session["user"] = username
            return redirect(url_for("home"))
        return "Invalid credentials!"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Username validation
        if not re.fullmatch(r"[A-Za-z]+", username):
            return "Invalid username! Only letters allowed."
        if username in users:
            return "User already exists!"

        users[username] = generate_password_hash(password)
        return redirect(url_for("login"))

    return render_template("register.html")

# -------------------
# Admin panel
# -------------------
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "user" not in session or session["user"] != admin_user:
        return redirect(url_for("login"))

    message = ""
    if request.method == "POST":
        # Gather guest info
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        passport = request.form["passport"]
        check_in = request.form["check_in"]
        check_out = request.form["check_out"]

        # Simple validation
        if not first_name.isalpha() or not last_name.isalpha():
            message = "First name and last name must contain only letters."
        else:
            # Store guest
            guests.append({
                "first_name": first_name,
                "last_name": last_name,
                "passport": passport,
                "check_in": check_in,
                "check_out": check_out
            })
            message = f"Guest {first_name} {last_name} registered successfully."

    # Filter current guests (check-in <= today <= check-out)
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_guests = [g for g in guests if g["check_in"] <= today_str <= g["check_out"]]

    return render_template("admin.html", message=message, guests=guests, current_guests=current_guests)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/booking")
def booking():
   
    return render_template("booking.html")
    return redirect(url_for("booking"))

if __name__ == "__main__":
    app.run(debug=True)

