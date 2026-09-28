# Solari Job-Board Monitor

A real use case built with [Solari](https://getsolari.com): a Solari **cloud
browser** scrapes a job board, and a Solari **sandbox** (microVM) dedupes the
postings against a local seen-list and renders a daily markdown digest. One
`slr_live_` API key spans both products.

Built as an application for the Pinetree Research SWE Intern hiring process
(see the [Solari cookbook](https://github.com/solari-sdk/solari-cookbook)).

## How it works

1. **Browser step** (`browser_step.py`) — launches a cloud browser session,
   opens the job board (default: https://www.python.org/jobs/), and extracts
   title, company, location, URL, and posted date for each listing. The page
   is verified to actually contain a job list before extraction (a page can
   load fine and still be the wrong page).
2. **Sandbox step** (`sandbox_step.py`) — starts a fresh sandbox, uploads the
   postings plus `digest_job.py`, and runs it there. The script normalizes
   URLs (dropping tracking parameters), drops anything already in
   `seen.json`, writes `digest.md`, and returns the updated seen-list.
3. `main.py` ties the steps together, handles per-step failures, and never
   prints the API key (errors are scrubbed).

## Run

```bash
pip install -r requirements.txt
export SOLARI_API_KEY=<redacted>   # get one at https://console.getsolari.com
python main.py
# python main.py --url https://www.python.org/jobs/ --seen ./seen.json
```

The digest is written to `digest.md`; `seen.json` tracks what you've already
seen so repeat runs only show new postings.

## Test (no API key needed)

The digest logic is pure stdlib and unit-tested locally:

```bash
python -m unittest discover tests
```
