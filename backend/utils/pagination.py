import base64
import json
from datetime import datetime

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
