"""Dedupe postings and render the digest inside a Solari sandbox.

Uploads the scraped postings, the local seen-list, and digest_job.py to a
fresh microVM, runs the script there, then downloads the digest and the
updated seen-list. The VM is destroyed with kill() afterwards — close()
alone would leave it running until the idle timeout.
"""

import json
from pathlib import Path

from solari_sandbox import SandboxClient

BASE_URL = "https://api.getsolari.com"


async def build_digest(api_key: str, postings: list, seen_path: Path, script_path: Path) -> str:
    """Run the digest inside a sandbox; return the markdown. Updates seen_path."""
    async with SandboxClient(api_key=api_key, base_url=BASE_URL) as client:
        sandbox = await client.create(template="base", timeout_ms=5 * 60_000)
        try:
            await sandbox.connect()
            await sandbox.files.write("/tmp/postings.json", json.dumps(postings))
            seen_text = seen_path.read_text() if seen_path.exists() else "[]"
            await sandbox.files.write("/tmp/seen.json", seen_text)
            await sandbox.files.write("/tmp/digest_job.py", script_path.read_text())

            # Gotcha from the cookbook: sandbox commands are NOT
            # shell-interpreted — the binary goes in cmd, argv in args.
            command = await sandbox.commands.run("python3", args=["/tmp/digest_job.py"])
            if command.exitCode != 0:
                raise RuntimeError(f"digest script failed: {command.stderr.strip()}")

            digest = await sandbox.files.read_text("/tmp/digest.md")
            seen_path.write_text(await sandbox.files.read_text("/tmp/seen.json"))
            return digest
        finally:
            await sandbox.kill()
