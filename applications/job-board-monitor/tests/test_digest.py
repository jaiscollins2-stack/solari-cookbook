"""Unit tests for digest_job.py — run locally, no Solari key needed."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from digest_job import build_digest, normalize_url  # noqa: E402


class TestNormalizeUrl(unittest.TestCase):
    def test_strips_query_and_fragment(self):
        self.assertEqual(
            normalize_url("https://example.com/jobs/1?utm_source=x#top"),
            "https://example.com/jobs/1",
        )

    def test_lowercases_host_and_strips_trailing_slash(self):
        self.assertEqual(
            normalize_url("HTTPS://EXAMPLE.COM/Jobs/1/"),
            "https://example.com/Jobs/1",
        )


class TestBuildDigest(unittest.TestCase):
    def setUp(self):
        self.jobs = [
            {
                "title": "Python Developer",
                "company": "Acme",
                "location": "Remote",
                "url": "https://example.com/jobs/1?ref=board",
                "posted": "2026-09-27",
            },
            {
                "title": "Data Analyst",
                "company": "Beta",
                "location": "Regina, SK",
                "url": "https://example.com/jobs/2",
                "posted": "2026-09-26",
            },
        ]

    def test_all_new_on_first_run(self):
        markdown, seen = build_digest(self.jobs, [])
        self.assertIn("Python Developer", markdown)
        self.assertIn("Data Analyst", markdown)
        self.assertEqual(len(seen), 2)

    def test_dedupes_by_url_ignoring_tracking_params(self):
        seen = [normalize_url("https://example.com/jobs/1")]
        markdown, updated = build_digest(self.jobs, seen)
        self.assertNotIn("Python Developer", markdown)
        self.assertIn("Data Analyst", markdown)
        self.assertEqual(len(updated), 2)

    def test_empty_digest_message(self):
        seen = [normalize_url(j["url"]) for j in self.jobs]
        markdown, _ = build_digest(self.jobs, seen)
        self.assertIn("No new postings", markdown)

    def test_missing_fields_do_not_crash(self):
        markdown, seen = build_digest([{"url": "https://example.com/jobs/9"}], [])
        self.assertIn("https://example.com/jobs/9", markdown)
        self.assertEqual(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
