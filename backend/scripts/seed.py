"""
Bulk recipe ingestion script.

Reads URLs from scripts/recipes.txt, fetches each page, parses the recipe,
and caches it in the database. Bypasses the API rate limit by calling
service functions directly.

Usage:
    python scripts/seed.py
"""

import asyncio
import random
import sys
from pathlib import Path
from urllib.parse import urlparse

# Allow imports from the backend root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.pool import create_pool
from db.recipes import cache_recipe, get_cached_recipe
from services.parser import parse_recipe
from services.scraper import fetch_page
from utils.url import normalize_url, validate_url

RECIPES_FILE = Path(__file__).resolve().parent / "recipes.txt"


def load_urls(path: Path) -> list[str]:
    """Read URLs from file, skip blanks and comments, normalize and deduplicate."""
    seen: set[str] = set()
    urls: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        normalized = normalize_url(line)
        if normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls


def group_by_domain(urls: list[str]) -> list[list[str]]:
    """Group URLs by domain, then shuffle the domain order for politeness."""
    domains: dict[str, list[str]] = {}
    for url in urls:
        domain = urlparse(url).netloc
        domains.setdefault(domain, []).append(url)

    groups = list(domains.values())
    random.shuffle(groups)
    return groups


def interleave(groups: list[list[str]]) -> list[str]:
    """Interleave URLs from different domains so no single site is hit repeatedly."""
    result: list[str] = []
    # Round-robin across groups
    while any(groups):
        for group in groups:
            if group:
                result.append(group.pop(0))
        # Remove empty groups
        groups = [g for g in groups if g]
    return result


async def seed() -> None:
    if not RECIPES_FILE.exists():
        print(f"Error: {RECIPES_FILE} not found")
        sys.exit(1)

    urls = load_urls(RECIPES_FILE)
    if not urls:
        print("No URLs found in recipes.txt")
        return

    print(f"Loaded {len(urls)} unique URLs")

    groups = group_by_domain(urls)
    ordered_urls = interleave(groups)

    pool = await create_pool()

    success = 0
    skipped = 0
    failed = 0
    failed_urls: list[tuple[str, str]] = []
    prev_domain: str | None = None

    try:
        for i, url in enumerate(ordered_urls, 1):
            current_domain = urlparse(url).netloc
            label = f"[{i}/{len(ordered_urls)}]"

            # Extra delay when switching domains
            if prev_domain and current_domain != prev_domain:
                delay = random.uniform(3, 5)
                await asyncio.sleep(delay)
            elif prev_domain:
                delay = random.uniform(1, 2)
                await asyncio.sleep(delay)

            prev_domain = current_domain

            try:
                validate_url(url)
            except ValueError as e:
                print(f"{label} SKIP (invalid) {url}: {e}")
                failed += 1
                failed_urls.append((url, str(e)))
                continue

            try:
                cached = await get_cached_recipe(pool, url)
                if cached:
                    print(f"{label} SKIP (cached) {url}")
                    skipped += 1
                    continue
            except Exception as e:
                print(f"{label} FAIL (cache check) {url}: {e}")
                failed += 1
                failed_urls.append((url, str(e)))
                continue

            try:
                html = await fetch_page(url)
                data = parse_recipe(html)
                await cache_recipe(pool, url, data, embedding=None)
                print(f"{label} OK {url} — {data['title']}")
                success += 1
            except Exception as e:
                print(f"{label} FAIL {url}: {e}")
                failed += 1
                failed_urls.append((url, str(e)))
    finally:
        await pool.close()

    # Summary
    print("\n" + "=" * 60)
    print(f"Total:   {len(ordered_urls)}")
    print(f"Success: {success}")
    print(f"Skipped: {skipped} (already cached)")
    print(f"Failed:  {failed}")

    if failed_urls:
        print("\nFailed URLs:")
        for url, reason in failed_urls:
            print(f"  {url}")
            print(f"    → {reason}")


if __name__ == "__main__":
    asyncio.run(seed())
