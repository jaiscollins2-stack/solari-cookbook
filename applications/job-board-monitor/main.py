"""Job-board monitor — scrape with a Solari cloud browser, digest in a sandbox.

Usage:
    export SOLARI_API_KEY=<redacted>   # get one at https://console.getsolari.com
    pip install -r requirements.txt
    python main.py [--url https://www.python.org/jobs/]
"""

import argparse
import asyncio
import os
import sys
import traceback
from pathlib import Path

from browser_step import DEFAULT_URL, scrape_jobs
from sandbox_step import build_digest

HERE = Path(__file__).resolve().parent


def scrub(text: str, secret: str) -> str:
    return text.replace(secret, "[REDACTED]") if secret else text


async def run(url: str, seen_path: Path) -> int:
    api_key = os.environ.get("SOLARI_API_KEY")
    if not api_key:
        print("error: SOLARI_API_KEY is not set.", file=sys.stderr)
        print("Get a key at https://console.getsolari.com, then:", file=sys.stderr)
        print("    export SOLARI_API_KEY=<redacted>", file=sys.stderr)
        return 2

    try:
        print(f"scraping {url} ...")
        postings = await scrape_jobs(api_key, url)
        print(f"found {len(postings)} posting(s)")
    except Exception as e:  # noqa: BLE001 — report, don't crash with a traceback
        print(f"error: browser step failed: {scrub(str(e), api_key)}", file=sys.stderr)
        return 1

    try:
        print("building digest in sandbox ...")
        digest = await build_digest(api_key, postings, seen_path, HERE / "digest_job.py")
    except Exception as e:  # noqa: BLE001
        print(f"error: sandbox step failed: {scrub(str(e), api_key)}", file=sys.stderr)
        return 1

    digest_path = HERE / "digest.md"
    digest_path.write_text(digest)
    print(f"wrote {digest_path}")
    print("---")
    print(digest)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape a job board, digest new postings.")
    parser.add_argument("--url", default=DEFAULT_URL, help="job board listing page")
    parser.add_argument(
        "--seen",
        default=str(HERE / "seen.json"),
        help="local seen-list file (created if missing)",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(run(args.url, Path(args.seen)))
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001 — last resort, never leak the key
        sys.stderr.write("error: unexpected failure:\n")
        sys.stderr.write(scrub(traceback.format_exc(), os.environ.get("SOLARI_API_KEY", "")))
        return 1


if __name__ == "__main__":
    sys.exit(main())
