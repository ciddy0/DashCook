from datetime import datetime, timezone

import pytest

from utils.pagination import decode_cursor, encode_cursor


def test_round_trip():
    ca = datetime(2026, 7, 6, 12, 30, 45, tzinfo=timezone.utc)
    url = "https://example.com/recipes/pancakes"
    decoded_ca, decoded_url = decode_cursor(encode_cursor(ca, url))
    assert decoded_ca == ca
    assert decoded_url == url


def test_round_trip_url_with_special_chars():
    ca = datetime(2026, 1, 1, tzinfo=timezone.utc)
    url = "https://example.com/r?q=a|b&x=1"
    decoded_ca, decoded_url = decode_cursor(encode_cursor(ca, url))
    assert decoded_ca == ca
    assert decoded_url == url


def test_malformed_cursor_raises():
    with pytest.raises(ValueError):
        decode_cursor("!!not-base64!!")


def test_non_json_payload_raises():
    import base64

    bogus = base64.urlsafe_b64encode(b"just plain text").decode("ascii")
    with pytest.raises(ValueError):
        decode_cursor(bogus)


def test_wrong_shape_raises():
    import base64
    import json

    bogus = base64.urlsafe_b64encode(json.dumps(["only-one"]).encode()).decode("ascii")
    with pytest.raises(ValueError):
        decode_cursor(bogus)
