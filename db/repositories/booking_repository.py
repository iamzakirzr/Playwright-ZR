from api.schemas.booking import Booking
from db.repositories.base_repository import BaseRepository


class BookingRepository(BaseRepository):
    def save(self, booking_id: int, booking: Booking) -> None:
        self.execute(
            """
            INSERT INTO bookings (id, firstname, lastname, totalprice, depositpaid, checkin, checkout)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                booking.firstname,
                booking.lastname,
                booking.totalprice,
                int(booking.depositpaid),
                booking.bookingdates.checkin.isoformat(),
                booking.bookingdates.checkout.isoformat(),
            ),
        )

    def find(self, booking_id: int) -> dict | None:
        return self.fetch_one("SELECT * FROM bookings WHERE id = ?", (booking_id,))
