import base64
import json
from datetime import datetime

# Keyset pagination cursor helpers.
#
# A cursor is an opaque, URL-safe base64 string encoding the sort key of the last
# row on a page: (created_at, url). Clients never build one — they only echo back
# the `next_cursor` returned by the previous page. Decoding is defensive: any
# malformed input raises ValueError so callers can turn it into a 422.


def encode_cursor(created_at: datetime, url: str) -> str:
    payload = json.dumps([created_at.isoformat(), url]).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        payload = base64.urlsafe_b64decode(cursor.encode("ascii"))
        created_at_iso, url = json.loads(payload)
        created_at = datetime.fromisoformat(created_at_iso)
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        raise ValueError("Malformed pagination cursor") from e

    if not isinstance(url, str):
        raise ValueError("Malformed pagination cursor")

    return created_at, url
