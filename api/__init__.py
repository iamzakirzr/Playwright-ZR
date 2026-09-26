"""API service objects (the API-layer equivalent of page objects)."""

from api.auth_client import AuthClient
from api.booking_client import BookingClient
from api.shop_assistant_client import ShopAssistantClient

__all__ = ["AuthClient", "BookingClient", "ShopAssistantClient"]
