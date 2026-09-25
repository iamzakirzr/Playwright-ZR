"""Cross-layer check: what the API returns is what we persist, field for field."""
from datetime import date, timedelta

from api.schemas import Booking, BookingDates, CreatedBooking


def test_api_booking_persists_consistently(authed_booking_client, booking_client, booking_repo):
    checkin = date.today() + timedelta(days=10)
    payload = Booking(
        firstname="Alan",
        lastname="Turing",
        totalprice=150,
        depositpaid=False,
        bookingdates=BookingDates(checkin=checkin, checkout=checkin + timedelta(days=2)),
    )
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
