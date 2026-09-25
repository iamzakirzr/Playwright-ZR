import pytest


@pytest.mark.smoke
def test_valid_credentials_return_token(auth_client, settings):
    response = auth_client.create_token_response(settings.api_username, settings.api_password)

    assert response.status == 200
    token = response.json()["token"]
    assert isinstance(token, str) and len(token) >= 10


def test_invalid_credentials_are_rejected(auth_client):
    response = auth_client.create_token_response("admin", "not-the-password")

    # Restful Booker signals auth failure in the body, not the status code.
    assert response.status == 200
    assert response.json() == {"reason": "Bad credentials"}


def test_write_without_token_is_forbidden(booking_client):
    response = booking_client.delete_booking(1)

    assert response.status == 403
