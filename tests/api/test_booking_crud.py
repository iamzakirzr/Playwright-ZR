from datetime import date, timedelta

import pytest

from api.schemas import Booking, BookingDates, BookingId, CreatedBooking


@pytest.fixture
def new_booking() -> Booking:
    checkin = date.today() + timedelta(days=30)
    return Booking(
        firstname="Ada",
        lastname="Lovelace",
        totalprice=321,
        depositpaid=True,
        bookingdates=BookingDates(checkin=checkin, checkout=checkin + timedelta(days=3)),
        additionalneeds="Breakfast",
    )


@pytest.fixture
def created_booking(authed_booking_client, new_booking):
    response = authed_booking_client.create_booking(new_booking)
    assert response.ok, response.text()
    created = CreatedBooking.model_validate(response.json())
    yield created
    authed_booking_client.delete_booking(created.bookingid)


@pytest.mark.smoke
def test_create_booking_matches_contract(created_booking, new_booking):
    # model_validate in the fixture already enforced the schema contract
    assert created_booking.booking == new_booking


def test_get_booking_round_trip(booking_client, created_booking):
    response = booking_client.get_booking(created_booking.bookingid)

    assert response.status == 200
    assert Booking.model_validate(response.json()) == created_booking.booking


def test_full_update(authed_booking_client, created_booking):
    updated = created_booking.booking.model_copy(update={"firstname": "Grace", "totalprice": 999})

    response = authed_booking_client.update_booking(created_booking.bookingid, updated)

    assert response.status == 200
    assert Booking.model_validate(response.json()) == updated


def test_partial_update(authed_booking_client, created_booking):
    response = authed_booking_client.partial_update(created_booking.bookingid, {"lastname": "Hopper"})

    assert response.status == 200
    body = Booking.model_validate(response.json())
    assert body.lastname == "Hopper"
    assert body.firstname == created_booking.booking.firstname


def test_delete_booking(authed_booking_client, booking_client, new_booking):
    booking_id = CreatedBooking.model_validate(authed_booking_client.create_booking(new_booking).json()).bookingid

    assert authed_booking_client.delete_booking(booking_id).status == 201
    assert booking_client.get_booking(booking_id).status == 404


def test_filter_by_name_returns_created_booking(booking_client, created_booking):
    response = booking_client.list_ids(firstname="Ada", lastname="Lovelace")

    ids = [BookingId.model_validate(b).bookingid for b in response.json()]
    assert created_booking.bookingid in ids


def test_get_unknown_booking_returns_404(booking_client):
    assert booking_client.get_booking(999_999_999).status == 404
