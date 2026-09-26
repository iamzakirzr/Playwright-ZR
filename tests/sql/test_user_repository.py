"""User repository tests, each isolated in a rolled-back transaction."""

import sqlite3

import pytest

from data import UserFactory


@pytest.mark.smoke
def test_seeded_user_lookup(user_repo):
    """Seeded users can be found with the expected fields."""
    user = user_repo.find_by_username("standard_user")

    assert user is not None
    assert user["email"] == "standard@example.com"
    assert user["is_locked"] == 0


def test_locked_users_match_ui_fixture(user_repo, settings):
    """The DB agrees with the UI suite about which account is locked."""
    assert settings.ui_locked_user in user_repo.locked_usernames()


def test_create_and_lock_user(user_repo):
    """Creating and then locking a factory-generated user updates count and flag."""
    user = UserFactory.build()
    before = user_repo.count()
    user_repo.create(**user)
    user_repo.lock(user["username"])

    assert user_repo.count() == before + 1
    assert user_repo.find_by_username(user["username"])["is_locked"] == 1


def test_bulk_users_are_unique(user_repo):
    """Five generated users insert cleanly: the factory never repeats a username or email."""
    for user in UserFactory.build_batch(5):
        user_repo.create(**user)


def test_changes_are_rolled_back_between_tests(user_repo):
    """Isolation: only the three seeded users exist, whatever earlier tests inserted."""
    assert user_repo.count() == 3


def test_username_must_be_unique(user_repo):
    """The UNIQUE constraint rejects a duplicate username."""
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        user_repo.create("standard_user", "other@example.com")


@pytest.mark.parametrize("bad_email", ["no-at-sign", "a@b", "@example.com"])
def test_email_check_constraint(user_repo, bad_email):
    """The CHECK constraint rejects malformed email addresses."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        user_repo.create("someone", bad_email)
