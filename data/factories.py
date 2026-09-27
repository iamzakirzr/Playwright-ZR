"""Test-data factories (Builder pattern + Faker).

Hard-coded test data ("Ada Lovelace", 321) hides bugs that only appear with
other values and makes parallel runs collide. Factories give every test fresh,
realistic data, with one line to pin whatever the test actually cares about::

    booking = BookingFactory.build(totalprice=0)             # override one field
    users   = UserFactory.build_batch(3, is_locked=True)     # many at once

Seeding (``seed_factories(42)``) makes a failing run reproducible: the seed
is printed in the pytest header, and ``FAKER_SEED=<n> pytest ...`` replays it.
"""

from __future__ import annotations

import os
import random
from datetime import date, timedelta
from typing import Any, ClassVar, Generic, TypeVar

from faker import Faker

from api.schemas.booking import Booking, BookingDates

T = TypeVar("T")

fake = Faker()


def base_seed() -> int:
    """The run's seed: ``FAKER_SEED`` if set, otherwise a fresh random one."""
    value = os.getenv("FAKER_SEED", "").strip()
    return int(value) if value else random.randrange(1_000_000)


def seed_factories(seed: int | str | None = None) -> int | str:
    """Seed Faker and ``random`` with ``seed`` (default: :func:`base_seed`) and return it.

    Any hashable works, so the root conftest seeds each test with ``"<base>:<test id>"``.
    """
    seed = base_seed() if seed is None else seed
    Faker.seed(seed)
    random.seed(seed)
    return seed


class Factory(Generic[T]):
    """Base factory: subclasses implement :meth:`defaults`; :meth:`build` applies overrides."""

    model: ClassVar[type]

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        """Fresh random field values for one object."""
        raise NotImplementedError

    @classmethod
    def build(cls, **overrides: Any) -> T:
        """One object: random defaults, then ``overrides`` for the fields a test cares about."""
        return cls.model(**{**cls.defaults(), **overrides})

    @classmethod
    def build_batch(cls, count: int, **overrides: Any) -> list[T]:
        """``count`` independent objects sharing the same overrides."""
        return [cls.build(**overrides) for _ in range(count)]


class BookingFactory(Factory[Booking]):
    """Valid Restful Booker bookings: check-in 1-60 days ahead, 1-14 night stay."""

    model = Booking

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        """Random guest, price and a future stay."""
        checkin = date.today() + timedelta(days=fake.random_int(1, 60))
        return {
            "firstname": fake.first_name(),
            "lastname": fake.last_name(),
            "totalprice": fake.random_int(50, 2000),
            "depositpaid": fake.boolean(),
            "bookingdates": BookingDates(checkin=checkin, checkout=checkin + timedelta(days=fake.random_int(1, 14))),
            "additionalneeds": fake.random_element(["Breakfast", "Late checkout", "Parking", None]),
        }


class UserRecord(dict):
    """Plain dict row for the ``users`` table (repositories take keyword arguments)."""


class UserFactory(Factory[UserRecord]):
    """Rows for ``UserRepository.create``: unique username and a valid email."""

    model = UserRecord

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        """Unique username/email pair, unlocked by default."""
        username = f"{fake.user_name()}_{fake.random_int(1000, 9999)}"
        return {"username": username, "email": f"{username}@example.com", "is_locked": False}


class CheckoutCustomerFactory(Factory[dict]):
    """Customer details for the Sauce Demo checkout form."""

    model = dict

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        """First name, last name and postcode."""
        return {"first": fake.first_name(), "last": fake.last_name(), "postal": fake.postcode()}
