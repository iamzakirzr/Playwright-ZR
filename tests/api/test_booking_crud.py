"""Booking CRUD API tests with pydantic contract validation on every response."""

import pytest

from api.schemas import Booking, BookingId, CreatedBooking
from data import BookingFactory


@pytest.fixture
def new_booking() -> Booking:
    """A fresh, valid, randomly generated booking (Faker) used as the request body."""
    return BookingFactory.build()


@pytest.mark.parametrize(
    "overrides",
    [{"totalprice": 0}, {"depositpaid": False}, {"additionalneeds": None}],
    ids=["zero-price", "no-deposit", "no-needs"],
)
def test_boundary_bookings_round_trip(authed_booking_client, booking_client, overrides):
    """Data-driven: factory defaults plus one boundary value each; the API stores exactly what it was sent."""
    booking = BookingFactory.build(**overrides)
    created = CreatedBooking.model_validate(authed_booking_client.create_booking(booking).json())
    try:
        assert Booking.model_validate(booking_client.get_booking(created.bookingid).json()) == booking
    finally:
        authed_booking_client.delete_booking(created.bookingid)


@pytest.fixture
def created_booking(authed_booking_client, new_booking):
    """Create a booking for the test and delete it afterwards (setup + teardown)."""
    response = authed_booking_client.create_booking(new_booking)
    assert response.ok, response.text()
    created = CreatedBooking.model_validate(response.json())
    yield created
    authed_booking_client.delete_booking(created.bookingid)


@pytest.mark.smoke
def test_create_booking_matches_contract(created_booking, new_booking):
    """The API stores exactly what was sent (the fixture's ``model_validate`` already enforced the schema)."""
    assert created_booking.booking == new_booking


def test_get_booking_round_trip(booking_client, created_booking):
    """GET returns the same booking that POST created."""
    response = booking_client.get_booking(created_booking.bookingid)

    assert response.status == 200
    assert Booking.model_validate(response.json()) == created_booking.booking


def test_full_update(authed_booking_client, created_booking):
    """PUT replaces the booking and echoes the new state."""
    updated = BookingFactory.build(bookingdates=created_booking.booking.bookingdates)

    response = authed_booking_client.update_booking(created_booking.bookingid, updated)

    assert response.status == 200
    assert Booking.model_validate(response.json()) == updated


def test_partial_update(authed_booking_client, created_booking):
    """PATCH changes only the given field and keeps the rest."""
    new_lastname = BookingFactory.build().lastname + "-patched"
    response = authed_booking_client.partial_update(created_booking.bookingid, {"lastname": new_lastname})

    assert response.status == 200
    body = Booking.model_validate(response.json())
    assert body.lastname == new_lastname
    assert body.firstname == created_booking.booking.firstname


def test_delete_booking(authed_booking_client, booking_client, new_booking):
    """DELETE removes the booking; a later GET returns 404."""
    booking_id = CreatedBooking.model_validate(authed_booking_client.create_booking(new_booking).json()).bookingid

    assert authed_booking_client.delete_booking(booking_id).status == 201
    assert booking_client.get_booking(booking_id).status == 404


def test_filter_by_name_returns_created_booking(booking_client, created_booking):
    """Query filters find the created booking by name."""
    booking = created_booking.booking
    response = booking_client.list_ids(firstname=booking.firstname, lastname=booking.lastname)

    ids = [BookingId.model_validate(b).bookingid for b in response.json()]
    assert created_booking.bookingid in ids


def test_get_unknown_booking_returns_404(booking_client):
    """A non-existent id returns 404, not 500."""
    assert booking_client.get_booking(999_999_999).status == 404
