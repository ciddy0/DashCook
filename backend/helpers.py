import urllib.parse


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.path == "/":
        return urllib.parse.urlunparse(parsed._replace(path=""))
    return url
