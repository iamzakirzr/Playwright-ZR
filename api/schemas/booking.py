"""Pydantic models double as request builders and response contract validators.

`model_validate(response.json())` fails loudly if the API drops or retypes a field.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class BookingDates(BaseModel):
    checkin: date
    checkout: date


class Booking(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None

    def model_dump(self, **kwargs):  # JSON-safe dates for request bodies
        return super().model_dump(mode="json", **kwargs)


class CreatedBooking(BaseModel):
    bookingid: int = Field(gt=0)
    booking: Booking


class BookingId(BaseModel):
    bookingid: int
