"""Service object for Restful Booker's ``/booking`` resource (full CRUD)."""

from playwright.sync_api import APIResponse

from api.base_client import BaseClient
from api.schemas.booking import Booking
from reporting import step


class BookingClient(BaseClient):
    """One method per booking operation; request bodies are built from pydantic models."""

    RESOURCE = "/booking"

    def authenticate(self, token: str) -> "BookingClient":
        """Attach the auth token (sent as a cookie by Restful Booker) and return ``self`` for chaining."""
        self.set_header("Cookie", f"token={token}")
        return self

    def list_ids(self, **filters) -> APIResponse:
        """List booking ids, optionally filtered (``firstname=...``, ``checkin=...``)."""
        return self.get(self.RESOURCE, params=filters or None)

    @step("GET /booking/{booking_id}")
    def get_booking(self, booking_id: int) -> APIResponse:
        """Fetch one booking."""
        return self.get(f"{self.RESOURCE}/{booking_id}")

    @step("POST /booking")
    def create_booking(self, booking: Booking) -> APIResponse:
        """Create a booking from a validated model."""
        return self.post(self.RESOURCE, data=booking.model_dump(by_alias=True))

    @step("PUT /booking/{booking_id}")
    def update_booking(self, booking_id: int, booking: Booking) -> APIResponse:
        """Replace a booking entirely (PUT). Needs :meth:`authenticate`."""
        return self.put(f"{self.RESOURCE}/{booking_id}", data=booking.model_dump(by_alias=True))

    @step("PATCH /booking/{booking_id}")
    def partial_update(self, booking_id: int, fields: dict) -> APIResponse:
        """Change only ``fields`` (PATCH). Needs :meth:`authenticate`."""
        return self.patch(f"{self.RESOURCE}/{booking_id}", data=fields)

    @step("DELETE /booking/{booking_id}")
    def delete_booking(self, booking_id: int) -> APIResponse:
        """Delete a booking. Needs :meth:`authenticate`; Restful Booker answers 201 on success."""
        return self.delete(f"{self.RESOURCE}/{booking_id}")
