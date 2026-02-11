# tests/conftest.py
import sqlite3
import pytest

from app_factory import create_app


def _init_test_schema(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS bookings;

    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT,
        password_changed_at TEXT,
        password_changed_by TEXT
    );

    CREATE TABLE bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        checkin_date TEXT NOT NULL,
        checkout_date TEXT NOT NULL,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    _init_test_schema(db_path)

    # ✅ Патчирај get_db_connection да враќа конекција кон test.db
    import database

    def _get_test_conn():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(database, "get_db_connection", _get_test_conn)

    # ✅ Fake render_template за да не зависиш од HTML во backend тестови
    import flask
    def _fake_render_template(template_name, **ctx):
        # врати „видлив“ текст за асерции
        return f"TEMPLATE:{template_name} CTX_KEYS:{sorted(list(ctx.keys()))}"

    monkeypatch.setattr(flask, "render_template", _fake_render_template)

    app = create_app({"TESTING": True, "SECRET_KEY": "test_secret"})
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
