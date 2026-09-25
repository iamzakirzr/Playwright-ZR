"""User repository tests, each isolated in a rolled-back transaction."""

import sqlite3

import pytest


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
    """Creating and then locking a user updates count and flag."""
    before = user_repo.count()
    user_repo.create("new_user", "new@example.com")
    user_repo.lock("new_user")

    assert user_repo.count() == before + 1
    assert user_repo.find_by_username("new_user")["is_locked"] == 1


def test_changes_are_rolled_back_between_tests(user_repo):
    """Isolation: the previous test's ``new_user`` does not leak into this one."""
    assert user_repo.find_by_username("new_user") is None


def test_username_must_be_unique(user_repo):
    """The UNIQUE constraint rejects a duplicate username."""
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        user_repo.create("standard_user", "other@example.com")


@pytest.mark.parametrize("bad_email", ["no-at-sign", "a@b", "@example.com"])
def test_email_check_constraint(user_repo, bad_email):
    """The CHECK constraint rejects malformed email addresses."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        user_repo.create("someone", bad_email)
