from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re

from database import init_db, get_db_connection
init_db()

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



#contact
from flask import Flask, render_template, request, flash
# Складирање на контакт пораки
messages = []

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        message = request.form["message"].strip()

        # Basic validation
        if not name or not email or not message:
            flash("All fields are required!", "error")
            return render_template("contact.html")

        if "@" not in email:
            flash("Please enter a valid email address!", "error")
            return render_template("contact.html")

        # Store message
        messages.append({
            "name": name,
            "email": email,
            "message": message
        })

        flash("Your message has been sent successfully!", "success")
        return render_template("contact.html")

    return render_template("contact.html")
# ontact

from datetime import datetime

#booking
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        checkin_date = request.form["checkin_date"]
        checkout_date = request.form["checkout_date"]

        if not all([first_name, last_name, email, phone, checkin_date, checkout_date]):
            flash("All fields are required!", "error")
            return render_template("booking.html")

        if not first_name.isalpha() or not last_name.isalpha():
            flash("First and last name must contain only letters.", "error")
            return render_template("booking.html")

        if "@" not in email:
            flash("Invalid email address.", "error")
            return render_template("booking.html")

        if checkout_date <= checkin_date:
            flash("Check-out must be after check-in.", "error")
            return render_template("booking.html")

        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO bookings
                (first_name, last_name, email, phone, checkin_date, checkout_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                first_name,
                last_name,
                email,
                phone,
                checkin_date,
                checkout_date,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            conn.commit()
            conn.close()

            flash("Guest checked in successfully!", "success")

        except Exception as e:
            print("DB ERROR:", e)
            flash(str(e), "error")

        return render_template("booking.html")

    return render_template("booking.html")
#booking


#admin/bookings
@app.route("/admin/bookings")
def admin_bookings():
    if "user" not in session or session["user"] != admin_user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    bookings = conn.execute(
        "SELECT * FROM bookings ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return render_template("admin_bookings.html", bookings=bookings)
#admin/bookings

#delete
@app.route("/admin/bookings/delete/<int:booking_id>", methods=["POST"])
def delete_booking(booking_id):
    if "user" not in session or session["user"] != admin_user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

    flash("Booking deleted successfully.", "success")
    return redirect(url_for("admin_bookings"))
#delete

if __name__ == "__main__":
    app.run(debug=True)

