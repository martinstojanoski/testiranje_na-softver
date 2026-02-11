# app_factory.py
import os
import re
from datetime import datetime, date
import sqlite3

from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, get_db_connection


TOTAL_ROOMS = 30


def ensure_admin():
    conn = get_db_connection()
    admin = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO users (username, password_hash, role, created_at, password_changed_at, password_changed_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            generate_password_hash("adminpass"),
            "admin",
            now,
            now,
            "system"
        ))
        conn.commit()

    conn.close()


def _pick_date_columns(conn, table_name="bookings"):
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    names = [c["name"] for c in cols]

    candidates = [
        ("check_in", "check_out"),
        ("checkin", "checkout"),
        ("check_in_date", "check_out_date"),
        ("checkin_date", "checkout_date"),
        ("date_from", "date_to"),
        ("start_date", "end_date"),
    ]
    for a, b in candidates:
        if a in names and b in names:
            return a, b

    raise sqlite3.OperationalError(
        f"Could not find date columns in table '{table_name}'. Found columns: {names}"
    )


def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = "your_secret_key_here"

    # ✅ Важно: init_db само еднаш во runtime, не на import
    init_db()

    # ✅ тест конфиг
    if test_config:
        app.config.update(test_config)

    # ✅ ensure_admin само кога НЕ е тестирање
    if not app.config.get("TESTING", False):
        ensure_admin()

    # ---------------- ROUTES ----------------

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

            if not user or not check_password_hash(user["password_hash"], password):
                flash("❌ Invalid username or password.", "error")
                return redirect(url_for("login"))

            session["user"] = user["username"]
            session["role"] = user["role"]
            flash(f"✅ Welcome back, {user['username']}!", "success")
            return redirect(url_for("home"))

        return render_template("login.html")

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

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

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

            flash(f"✅ Корисникот '{username}' е успешно регистриран. Најави се.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        session.pop("role", None)
        return redirect(url_for("login"))

    # ---------------- BOOKING ----------------
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
                """, (first_name, last_name, email, phone, checkin_date, checkout_date, created_at))
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

        if booking:
            checkin = datetime.strptime(booking["checkin_date"], "%Y-%m-%d")
            checkout = datetime.strptime(booking["checkout_date"], "%Y-%m-%d")
            stay_days = (checkout - checkin).days

        return render_template("booking_status.html", booking=booking, stay_days=stay_days)

    # ---------------- AVAILABILITY ----------------
    @app.route("/availability", methods=["GET"])
    def availability():
        check_in = (request.args.get("check_in") or "").strip()
        check_out = (request.args.get("check_out") or "").strip()

        availability_data = None
        availability_error = None
        admin_insights = None

        try:
            ci = datetime.strptime(check_in, "%Y-%m-%d").date()
            co = datetime.strptime(check_out, "%Y-%m-%d").date()
            if co <= ci:
                raise ValueError("Check-out must be after check-in.")
        except Exception:
            availability_error = "Invalid dates. Please select a valid check-in and check-out."
            return render_template(
                "home.html",
                user=session.get("username"),
                availability=availability_data,
                availability_error=availability_error,
                admin_insights=admin_insights
            )

        try:
            conn = get_db_connection()
            table = "bookings"
            col_in, col_out = _pick_date_columns(conn, table)

            q = f"""
                SELECT COUNT(*) AS occupied
                FROM {table}
                WHERE date({col_in}) < date(?)
                  AND date({col_out}) > date(?)
            """
            row = conn.execute(q, (check_out, check_in)).fetchone()
            occupied = int(row["occupied"]) if row and row["occupied"] is not None else 0

            available = max(0, TOTAL_ROOMS - occupied)
            occupancy = round((occupied / TOTAL_ROOMS) * 100, 1) if TOTAL_ROOMS > 0 else 0.0

            availability_data = {"available": available, "occupied": occupied, "occupancy": occupancy}

            if session.get("role") == "admin":
                today = date.today().strftime("%Y-%m-%d")
                checkins = conn.execute(
                    f"SELECT COUNT(*) c FROM {table} WHERE date({col_in})=date(?)",
                    (today,)
                ).fetchone()["c"]

                checkouts = conn.execute(
                    f"SELECT COUNT(*) c FROM {table} WHERE date({col_out})=date(?)",
                    (today,)
                ).fetchone()["c"]

                active = conn.execute(
                    f"""
                    SELECT COUNT(*) c
                    FROM {table}
                    WHERE date({col_in}) <= date(?)
                      AND date({col_out}) > date(?)
                    """,
                    (today, today)
                ).fetchone()["c"]

                admin_insights = {
                    "checkins": int(checkins),
                    "checkouts": int(checkouts),
                    "active": int(active),
                    "conflicts": 0
                }

            conn.close()

        except sqlite3.OperationalError as e:
            availability_error = f"Database error: {e}"
        except Exception as e:
            availability_error = f"Unexpected error: {e}"

        return render_template(
            "home.html",
            user=session.get("username"),
            availability=availability_data,
            availability_error=availability_error,
            admin_insights=admin_insights
        )

    return app
