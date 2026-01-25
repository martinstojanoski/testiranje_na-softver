from flask import Flask, render_template, request, redirect, session, url_for, flash

from werkzeug.security import generate_password_hash, check_password_hash

import re

from database import init_db, get_db_connection

init_db()

from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

def ensure_admin():
    conn = get_db_connection()

    admin = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute("""
           INSERT INTO users (username, password_hash, role, created_at, password_changed_at, password_changed_by)
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    "admin",
    generate_password_hash("adminpass"),
    "admin",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "system"
        ))
        conn.commit()

    conn.close()
ensure_admin()



# -------------------
# Storage
# -------------------

guests = []  # list of guest dicts

# -------------------
# Admin
# -------------------



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
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        # ❌ Погрешно корисничко име или лозинка
        if not user or not check_password_hash(user["password_hash"], password):
            flash("❌ Invalid username or password.", "error")
            return redirect(url_for("login"))

        # ✅ Успешна најава
        session["user"] = user["username"]
        session["role"] = user["role"]
        flash(f"✅ Welcome back, {user['username']}!", "success")
        return redirect(url_for("home"))

    return render_template("login.html")

# -------------------
# ROUTES forgot-password
# -------------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not username or not new_password or not confirm_password:
            flash("❌ Please fill all fields.", "error")
            return render_template("forgot_password.html")

        if new_password != confirm_password:
            flash("❌ Passwords do not match.", "error")
            return render_template("forgot_password.html")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT id, username FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            conn.close()
            flash("❌ User not found.", "error")
            return render_template("forgot_password.html")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE users
            SET password_hash = ?, password_changed_at = ?, password_changed_by = ?
            WHERE id = ?
        """, (generate_password_hash(new_password), now, "user", user["id"]))

        conn.commit()
        conn.close()

        flash("✅ Password updated. You can login now.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")
# -------------------
# ROUTES forgot-password
# -------------------












# -------------------
# REGISTER
# -------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # ✅ validations
        if not username or not password or not confirm_password:
            flash("❌ Сите полиња се задолжителни.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("❌ Лозинките не се совпаѓаат.", "error")
            return redirect(url_for("register"))

        if not re.fullmatch(r"[A-Za-z]+", username):
            flash("❌ Invalid username! Only letters allowed.", "error")
            return redirect(url_for("register"))

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing:
            conn.close()
            flash("❌ User already exists!", "error")
            return redirect(url_for("register"))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute("""
            INSERT INTO users (username, password_hash, role, created_at, password_changed_at, password_changed_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username,
            generate_password_hash(password),
            "user",
            now,
            now,
            "self (registration)"
        ))

        conn.commit()
        conn.close()

        # ✅ SUCCESS flash + redirect to login
        flash(f"✅ Корисникот '{username}' е успешно регистриран. Најави се.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# -------------------
# Admin panel
# -------------------
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        phone      = request.form.get("phone", "").strip()
        check_in   = request.form.get("check_in", "").strip()   # from admin.html
        check_out  = request.form.get("check_out", "").strip()  # from admin.html

        # validations
        if not all([first_name, last_name, email, phone, check_in, check_out]):
            flash("❌ Please fill all fields.", "error")
            return redirect(url_for("admin_panel"))

        if not first_name.isalpha() or not last_name.isalpha():
            flash("❌ First name and last name must contain only letters.", "error")
            return redirect(url_for("admin_panel"))

        try:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = get_db_connection()
            conn.execute("""
                INSERT INTO bookings
                (first_name, last_name, email, phone, checkin_date, checkout_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone, check_in, check_out, created_at))
            conn.commit()
            conn.close()

            flash(f"✅ Guest {first_name} {last_name} registered successfully.", "success")

            # ✅ ОДИ ДИРЕКТ НА /admin/bookings
            return redirect(url_for("admin_bookings"))

        except Exception as e:
            try:
                conn.close()
            except:
                pass
            print("ADMIN INSERT ERROR:", e)
            flash("❌ Error saving booking to database.", "error")
            return redirect(url_for("admin_panel"))

    # GET: прикажи dashboard статистики преку база (не RAM листа)
    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    guests_rows = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
    current_rows = conn.execute("""
        SELECT * FROM bookings
        WHERE checkin_date <= ? AND checkout_date >= ?
        ORDER BY created_at DESC
    """, (today, today)).fetchall()
    conn.close()

    # admin.html очекува keys: first_name, last_name, email, phone, check_in, check_out
    guests = []
    for r in guests_rows:
        guests.append({
            "first_name": r["first_name"],
            "last_name": r["last_name"],
            "email": r["email"],
            "phone": r["phone"],
            "check_in": r["checkin_date"],
            "check_out": r["checkout_date"],
        })

    current_guests = []
    for r in current_rows:
        current_guests.append({
            "first_name": r["first_name"],
            "last_name": r["last_name"],
            "email": r["email"],
            "phone": r["phone"],
            "check_in": r["checkin_date"],
            "check_out": r["checkout_date"],
        })

    return render_template("admin.html", message="", guests=guests, current_guests=current_guests)


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
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
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
    conn.close()

    bookings = []
    for b in rows:
        checkin = datetime.strptime(b["checkin_date"], "%Y-%m-%d")
        checkout = datetime.strptime(b["checkout_date"], "%Y-%m-%d")
        stay_days = (checkout - checkin).days

        bookings.append({**dict(b), "stay_days": stay_days})

    return render_template("admin_bookings.html", bookings=bookings)
#admin/bookings


# -------------------
# DELETE
# -------------------
#delete
@app.route("/admin/bookings/delete/<int:booking_id>", methods=["POST"])
def delete_booking(booking_id):
    if "user" not in session or session.get("role") != "admin":
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


# -------------------
# admin/users
# -------------------
#admin/users
@app.route("/admin/users")
def admin_users():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    q = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()

    sql = "SELECT id, username, role, created_at, password_changed_at, password_changed_by FROM users WHERE 1=1"
    params = []

    if q:
        sql += " AND username LIKE ?"
        params.append(f"%{q}%")

    if role_filter in ("admin", "user"):
        sql += " AND role = ?"
        params.append(role_filter)

    sql += " ORDER BY id DESC"

    conn = get_db_connection()
    users = conn.execute(sql, params).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    admins = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    normal_users = conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    conn.close()

    return render_template(
        "admin_users.html",
        users=users,
        total=total,
        admins=admins,
        normal_users=normal_users,
        q=q,
        role_filter=role_filter
    )

#admin/users







# -------------------
# ADMIN USERS: EDIT
# -------------------
#ADMIN USERS: EDIT
@app.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username, role, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if not user:
        conn.close()
        flash("❌ User not found.", "error")
        return redirect(url_for("admin_users"))

    # Забрани измена на admin username (по желба)
    if user["username"] == "admin" and request.method == "POST":
        flash("❌ Admin user cannot be edited here.", "error")
        conn.close()
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        username = request.form["username"].strip()
        role = request.form["role"].strip()

        if not re.fullmatch(r"[A-Za-z]+", username):
            flash("❌ Invalid username! Only letters allowed.", "error")
            conn.close()
            return render_template("edit_user.html", u=user)

        if role not in ("admin", "user"):
            flash("❌ Invalid role.", "error")
            conn.close()
            return render_template("edit_user.html", u=user)

        # Check if username is taken by another user
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (username, user_id)
        ).fetchone()

        if existing:
            flash("❌ Username already exists.", "error")
            conn.close()
            return render_template("edit_user.html", u=user)

        conn.execute(
            "UPDATE users SET username = ?, role = ? WHERE id = ?",
            (username, role, user_id)
        )
        conn.commit()
        conn.close()

        flash("✅ User updated successfully.", "success")
        return redirect(url_for("admin_users"))

    conn.close()
    return render_template("edit_user.html", u=user)
    #ADMIN USERS: EDIT  


# -------------------
# (admin менува лозинка на било кој user)
# -------------------
@app.route("/admin/users/change-password/<int:user_id>", methods=["GET", "POST"])
def admin_change_user_password(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if not user:
        conn.close()
        flash("❌ User not found.", "error")
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        new_password = request.form["password"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changed_by = f"admin:{session.get('user')}"

        conn.execute("""
            UPDATE users
            SET password_hash = ?,
                password_changed_at = ?,
                password_changed_by = ?
            WHERE id = ?
        """, (
            generate_password_hash(new_password),
            now,
            changed_by,
            user_id
        ))

        conn.commit()
        conn.close()

        flash("✅ Password changed successfully.", "success")
        return redirect(url_for("admin_users"))

    conn.close()
    return render_template("admin_change_password.html", u=user)


# -------------------
# (admin менува лозинка на било кој user)
# -------------------










# -------------------
# ADMIN USERS: DELETE
# -------------------
@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if not user:
        conn.close()
        flash("❌ User not found.", "error")
        return redirect(url_for("admin_users"))

    if user["username"] == "admin":
        conn.close()
        flash("❌ Admin user cannot be deleted.", "error")
        return redirect(url_for("admin_users"))

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("✅ User deleted successfully.", "success")
    return redirect(url_for("admin_users"))




if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
    
