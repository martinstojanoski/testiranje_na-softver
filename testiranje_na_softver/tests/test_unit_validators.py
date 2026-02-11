# tests/test_unit_validators.py
import re
from datetime import datetime
import pytest


def is_valid_username(username: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]+", username or ""))


def is_valid_email(email: str) -> bool:
    email = (email or "").strip()
    return ("@" in email) and ("." in email.split("@")[-1])


def calc_stay_days(checkin: str, checkout: str) -> int:
    ci = datetime.strptime(checkin, "%Y-%m-%d")
    co = datetime.strptime(checkout, "%Y-%m-%d")
    return (co - ci).days


def test_username_only_letters():
    assert is_valid_username("Martin")
    assert is_valid_username("abcDEF")
    assert not is_valid_username("martin123")
    assert not is_valid_username("martin_")
    assert not is_valid_username("")


def test_email_basic_validation():
    assert is_valid_email("a@b.com")
    assert is_valid_email("martin@test.mk")
    assert not is_valid_email("martin.com")
    assert not is_valid_email("martin@")
    assert not is_valid_email("")


def test_stay_days_positive():
    assert calc_stay_days("2026-01-10", "2026-01-15") == 5


def test_stay_days_zero_or_negative_is_possible_but_should_be_handled_in_routes():
    # чиста математика: 0 или негативно (route треба да го валидира)
    assert calc_stay_days("2026-01-10", "2026-01-10") == 0
    assert calc_stay_days("2026-01-10", "2026-01-09") == -1
