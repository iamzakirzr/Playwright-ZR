"""Cross-layer check: what the API returns is what we persist, field for field."""

from api.schemas import Booking, CreatedBooking
from data import BookingFactory


def test_api_booking_persists_consistently(authed_booking_client, booking_client, booking_repo):
    """Create via API, read back, persist to SQL: every column matches the request payload."""
    payload = BookingFactory.build()
    created = CreatedBooking.model_validate(authed_booking_client.create_booking(payload).json())
    try:
        fetched = Booking.model_validate(booking_client.get_booking(created.bookingid).json())
        booking_repo.save(created.bookingid, fetched)

        row = booking_repo.find(created.bookingid)
        assert row == {
            "id": created.bookingid,
            "firstname": payload.firstname,
            "lastname": payload.lastname,
            "totalprice": payload.totalprice,
            "depositpaid": int(payload.depositpaid),
            "checkin": payload.bookingdates.checkin.isoformat(),
            "checkout": payload.bookingdates.checkout.isoformat(),
        }
    finally:
        authed_booking_client.delete_booking(created.bookingid)
