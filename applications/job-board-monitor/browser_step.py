"""Scrape job postings with a Solari cloud browser.

Launches a cloud browser session, opens the job board, extracts postings,
and always releases the session via try/finally (closing the browser is what
releases the slot — without it the session is held until the plan deadline).
"""

from solari_browser import Solari

DEFAULT_URL = "https://www.python.org/jobs/"


async def scrape_jobs(api_key: str, url: str = DEFAULT_URL):
    """Return a list of {title, company, location, url, posted} dicts."""
    solari = Solari(api_key=api_key)
    browser = await solari.launch()
    try:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        # Gotcha from the cookbook: a page can load fine and still be the
        # wrong page. Verify the job list is really there before extracting.
        listing = page.locator("ol.list-recent-jobs")
        if await listing.count() == 0:
            raise RuntimeError(
                f"No job list found at {url} — the page layout may have "
                "changed or the URL is not a supported job board."
            )

        jobs = []
        items = listing.locator("li")
        count = await items.count()
        for i in range(count):
            item = items.nth(i)
            title_link = item.locator("h2 a").first
            title = (await title_link.inner_text()).strip()
            href = await title_link.get_attribute("href") or ""
            # python.org uses relative links
            job_url = href if href.startswith("http") else f"https://www.python.org{href}"

            async def text_of(selector):
                loc = item.locator(selector).first
                return (await loc.inner_text()).strip() if await loc.count() else ""

            company = await text_of("span.listing-company-name")
            location = await text_of("span.listing-location")
            posted = await text_of("span.listing-posted")

            if title and job_url:
                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "posted": posted,
                    }
                )
        return jobs
    finally:
        await browser.close()
