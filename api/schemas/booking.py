"""Pydantic models that double as request builders and response-contract validators.

``Booking.model_validate(response.json())`` fails loudly if the API drops,
renames or re-types a field. That makes it a contract test for free.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class BookingDates(BaseModel):
    """Stay dates; parsed from and serialised to ISO ``YYYY-MM-DD``."""

    checkin: date
    checkout: date


class Booking(BaseModel):
    """A booking as sent to and returned by the API. Extra fields are forbidden (strict contract)."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None

    def model_dump(self, **kwargs):
        """Serialise with JSON-safe types (dates become strings) for request bodies."""
        return super().model_dump(mode="json", **kwargs)


class CreatedBooking(BaseModel):
    """Response of ``POST /booking``: the new id plus the stored booking."""

    bookingid: int = Field(gt=0)
    booking: Booking


class BookingId(BaseModel):
    """One element of the ``GET /booking`` id list."""

    bookingid: int
