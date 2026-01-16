from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re

from database import init_db, get_db_connection
init_db()

from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# -------------------
# Storage
# -------------------
users = {}  # admin + normal users
guests = []  # list of guest dicts

# -------------------
# Admin
# -------------------

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

# -------------------
# REGISTER
# -------------------
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


# -------------------
# CONTACT
# -------------------
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
#contact

from datetime import datetime

# -------------------
# BOOKING
# -------------------
#booking
from datetime import datetime

@app.route("/booking", methods=["GET", "POST"])
def booking():
    if request.method == "POST":
        conn = None
        try:
            first_name = request.form["first_name"].strip()
            last_name = request.form["last_name"].strip()
            email = request.form["email"].strip()
            phone = request.form["phone"].strip()
            checkin_date = request.form["checkin_date"]
            checkout_date = request.form["checkout_date"]

            if not all([first_name, last_name, email, phone, checkin_date, checkout_date]):
                flash("❌ Сите полиња се задолжителни!", "error")
                return redirect(url_for("booking"))

            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = get_db_connection()
            conn.execute("""
                INSERT INTO bookings 
                (first_name, last_name, email, phone, checkin_date, checkout_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone,
                  checkin_date, checkout_date, created_at))
            conn.commit()

            flash("✅ Успешно направивте регистрација за сместување!", "success")
            return redirect(url_for("booking_status"))

        except Exception as e:
            print("BOOKING ERROR:", e)
            flash("❌ Грешка при зачувување во база!", "error")
            return redirect(url_for("booking"))

        finally:
            if conn:
                conn.close()

    return render_template("booking.html")
#booking


# -------------------
# BOOKING status
# -------------------
@app.route("/booking-status", methods=["GET", "POST"])
def booking_status():
    booking = None
    stay_days = None

    if request.method == "POST":
        email = request.form["email"]

        conn = get_db_connection()
        booking = conn.execute("""
            SELECT * FROM bookings
            WHERE email = ?
            ORDER BY id DESC
            LIMIT 1
        """, (email,)).fetchone()
        conn.close()

        if not booking:
            flash("❌ Нема пронајдена регистрација за овој email.", "error")

    # ✅ АКО ИМА BOOKING → ПРЕСМЕТАЈ ДЕНОВИ
    if booking:
        checkin = datetime.strptime(booking["checkin_date"], "%Y-%m-%d")
        checkout = datetime.strptime(booking["checkout_date"], "%Y-%m-%d")
        stay_days = (checkout - checkin).days

    return render_template(
        "booking_status.html",
        booking=booking,
        stay_days=stay_days
    )


# -------------------
# BOOKING status
# -------------------



# -------------------
# BOOKING EDIT
# -------------------
#booking_edit
@app.route("/admin/edit/<int:booking_id>", methods=["GET", "POST"])
def edit_booking(booking_id):
    conn = get_db_connection()

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        checkin_date = request.form["checkin_date"]
        checkout_date = request.form["checkout_date"]

        conn.execute("""
            UPDATE bookings
            SET first_name=?, last_name=?, email=?, phone=?,
                checkin_date=?, checkout_date=?
            WHERE id=?
        """, (first_name, last_name, email, phone,
              checkin_date, checkout_date, booking_id))

        conn.commit()
        conn.close()

        flash("Booking updated successfully!", "success")
        return redirect(url_for("admin_bookings"))

    booking = conn.execute(
        "SELECT * FROM bookings WHERE id=?",
        (booking_id,)
    ).fetchone()
    conn.close()

    return render_template("edit_booking.html", booking=booking)
#booking_edit


# -------------------
# ADMIN BOOKINGS
# -------------------
#admin/bookings
@app.route("/admin/bookings")
def admin_bookings():
    if "user" not in session or session["user"] != admin_user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM bookings ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    bookings = []
    for b in rows:
        checkin = datetime.strptime(b["checkin_date"], "%Y-%m-%d")
        checkout = datetime.strptime(b["checkout_date"], "%Y-%m-%d")
        stay_days = (checkout - checkin).days

        bookings.append({
            **dict(b),
            "stay_days": stay_days
        })

    return render_template("admin_bookings.html", bookings=bookings)
#admin/bookings


# -------------------
# DELETE
# -------------------
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



# -------------------
# IMAGE
# -------------------
#images
@app.route("/images")
def images():
    images = [
        {
            "url": "/static/images/img1.jpg",
            "title": "Mountain View",
            "description": "Nature & Landscape"
        },
        {
            "url": "/static/images/img2.jpg",
            "title": "City Lights",
            "description": "Urban Photography"
        }
    ]
    return render_template("images.html", images=images)
#image




if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
    
