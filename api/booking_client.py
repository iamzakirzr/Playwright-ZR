from playwright.sync_api import APIResponse

from api.base_client import BaseClient
from api.schemas.booking import Booking


class BookingClient(BaseClient):
    RESOURCE = "/booking"

    def authenticate(self, token: str) -> "BookingClient":
        # Restful Booker reads the token from a cookie for write operations.
        self.set_header("Cookie", f"token={token}")
        return self

    def list_ids(self, **filters) -> APIResponse:
        return self.get(self.RESOURCE, params=filters or None)

    def get_booking(self, booking_id: int) -> APIResponse:
        return self.get(f"{self.RESOURCE}/{booking_id}")

    def create_booking(self, booking: Booking) -> APIResponse:
        return self.post(self.RESOURCE, data=booking.model_dump(by_alias=True))

    def update_booking(self, booking_id: int, booking: Booking) -> APIResponse:
        return self.put(f"{self.RESOURCE}/{booking_id}", data=booking.model_dump(by_alias=True))

    def partial_update(self, booking_id: int, fields: dict) -> APIResponse:
        return self.patch(f"{self.RESOURCE}/{booking_id}", data=fields)

    def delete_booking(self, booking_id: int) -> APIResponse:
        return self.delete(f"{self.RESOURCE}/{booking_id}")
