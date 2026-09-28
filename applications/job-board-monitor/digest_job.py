"""Dedupe job postings and render a markdown digest.

Runs inside a Solari sandbox (stdlib only). Reads /tmp/postings.json and
/tmp/seen.json, writes /tmp/digest.md and the updated /tmp/seen.json.

The same functions are unit-tested locally in tests/test_digest.py, so the
logic is verifiable without a Solari API key.
"""

import json
import sys
from datetime import date
from urllib.parse import urlparse, urlunparse

POSTINGS_PATH = "/tmp/postings.json"
SEEN_PATH = "/tmp/seen.json"
DIGEST_PATH = "/tmp/digest.md"


def normalize_url(url: str) -> str:
    """Canonical form for dedupe: lowercase host, no query/fragment/trailing slash."""
    try:
        parts = urlparse(url.strip())
    except Exception:
        return url.strip().lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunparse((parts.scheme.lower(), netloc, path, "", "", ""))


def build_digest(postings, seen_urls):
    """Return (markdown, updated_seen_urls). Only unseen postings appear."""
    seen = set(seen_urls)
    fresh = []
    for job in postings:
        key = normalize_url(job.get("url", ""))
        if key and key not in seen:
            seen.add(key)
            fresh.append(job)

    today = date.today().isoformat()
    lines = [f"# Job digest — {today}", ""]
    if not fresh:
        lines.append("No new postings since the last run.")
    else:
        lines.append(f"{len(fresh)} new posting(s):")
        lines.append("")
        for job in fresh:
            title = job.get("title", "Untitled").strip()
            company = job.get("company", "").strip()
            location = job.get("location", "").strip()
            posted = job.get("posted", "").strip()
            url = job.get("url", "").strip()
            bits = " — ".join(b for b in (company, location, posted) if b)
            lines.append(f"- [{title}]({url})" + (f" — {bits}" if bits else ""))
    lines.append("")
    return "\n".join(lines), sorted(seen)


def main() -> int:
    try:
        with open(POSTINGS_PATH) as f:
            postings = json.load(f)
    except FileNotFoundError:
        print(f"error: {POSTINGS_PATH} not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: {POSTINGS_PATH} is not valid JSON: {e}", file=sys.stderr)
        return 1

    try:
        with open(SEEN_PATH) as f:
            seen_urls = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        seen_urls = []

    markdown, updated_seen = build_digest(postings, seen_urls)

    with open(DIGEST_PATH, "w") as f:
        f.write(markdown)
    with open(SEEN_PATH, "w") as f:
        json.dump(updated_seen, f, indent=2)

    new_count = len(updated_seen) - len(set(seen_urls))
    print(f"digest: {DIGEST_PATH} ({new_count} new)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
