"""Google News article collection for bird-flu research.

Collects Google News articles about bird flu / avian influenza using the
SerpApi Google search engine (https://serpapi.com), iterating month by month
over a date range, filtering by title keywords, de-duplicating by link, and
saving the results to a CSV file.

The SerpApi key is read from the SERPAPI_API_KEY environment variable so that
no secret is committed to source control. See ``.env.example``.

Usage:
    python google_news_collection.py
"""

import csv
import os
import time
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests

try:
    # Optional: load SERPAPI_API_KEY from a local .env file if python-dotenv
    # is installed. Not required if the variable is already set in the shell.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Configuration ----------------------------------------------------------

START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)

# Search query: any of these phrases (SerpApi OR syntax).
QUERY = (
    '"bird flu" OR "avian influenza" OR "H5N1" OR "avian flu" '
    'OR "highly pathogenic avian influenza" OR "HPAI" '
    'OR "low pathogenic avian influenza" OR "LPAI" '
    'OR "H5 avian influenza" OR "H7N9" OR "H5Nx" OR "poultry influenza" '
    'OR "wild bird influenza" OR "zoonotic influenza" OR "bird influenza"'
)

# An article is kept only if its title contains one of these terms.
TITLE_TERMS = [
    "bird flu",
    "avian influenza",
    "h5n1",
    "avian flu",
    "highly pathogenic avian influenza",
    "hpai",
    "low pathogenic avian influenza",
    "lpai",
    "h5 avian influenza",
    "h7n9",
    "h5nx",
    "poultry influenza",
    "wild bird influenza",
    "zoonotic influenza",
    "bird influenza",
]

BASE_URL = "https://serpapi.com/search.json"
OUTPUT_CSV = "serpapi_birdflu_news.csv"


def get_api_key():
    """Return the SerpApi key from the environment, or raise if missing."""
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing SERPAPI_API_KEY environment variable. "
            "See .env.example for setup instructions."
        )
    return api_key


# --- Helpers ----------------------------------------------------------------

def month_windows(start, end):
    """Yield (start, end) date tuples, one per calendar month in the range."""
    windows = []
    cur = date(start.year, start.month, 1)
    while cur <= end:
        next_month = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
        w_start = max(start, cur)
        w_end = min(end, next_month - timedelta(days=1))
        windows.append((w_start, w_end))
        cur = next_month
    return windows


def format_cd(d):
    """Format a date as M/D/YYYY for SerpApi's cd_min / cd_max parameters."""
    return f"{d.month}/{d.day}/{d.year}"


def title_matches(title):
    """Return True if the title contains any of the TITLE_TERMS."""
    if not title:
        return False
    t = title.lower()
    return any(term in t for term in TITLE_TERMS)


def serpapi_request(params, session, max_retries=5):
    """Send a SerpApi request with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            r = session.get(BASE_URL, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(min(60, 2 ** attempt))
    raise RuntimeError("Failed after retries")


def extract_next_start(serp_json):
    """Return the 'start' offset for the next results page, or None."""
    pagination = serp_json.get("serpapi_pagination") or {}
    next_link = pagination.get("next_link")
    if not next_link:
        return None
    qs = parse_qs(urlparse(next_link).query)
    if "start" in qs:
        return int(qs["start"][0])
    return None


def collect_window(api_key, w_start, w_end):
    """Collect all matching articles within a single date window."""
    tbs = f"cdr:1,cd_min:{format_cd(w_start)},cd_max:{format_cd(w_end)},sbd:1"

    rows = []
    seen_links = set()
    start = 0
    session = requests.Session()

    while True:
        params = {
            "api_key": api_key,
            "engine": "google",
            "tbm": "nws",
            "q": QUERY,
            "tbs": tbs,
            "num": 100,
            "start": start,
        }

        data = serpapi_request(params, session=session)
        news_results = data.get("news_results") or []
        if not news_results:
            break

        fetched_at = datetime.utcnow().isoformat()
        added_this_page = 0

        for item in news_results:
            link = item.get("link")
            title = item.get("title")

            if not link or link in seen_links:
                continue
            if not title_matches(title):
                continue

            rows.append(
                {
                    "window_start": str(w_start),
                    "window_end": str(w_end),
                    "fetched_at_utc": fetched_at,
                    "title": title,
                    "link": link,
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "published_at": item.get("published_at"),
                    "snippet": item.get("snippet"),
                    "thumbnail": item.get("thumbnail"),
                    "position": item.get("position"),
                }
            )
            seen_links.add(link)
            added_this_page += 1

        # Pagination: follow SerpApi's next link, or step by 100 as a fallback.
        next_start = extract_next_start(data)
        if next_start is None:
            if len(news_results) < 100:
                break
            start += 100
        else:
            start = next_start

        time.sleep(0.5)  # light throttle to respect hourly throughput

        # Stop going deeper once pages stop adding new articles.
        if added_this_page == 0 and start >= 300:
            break

    return rows


def run_collection(api_key):
    """Collect articles across every month in the configured date range."""
    all_rows = []
    global_seen = set()

    for w_start, w_end in month_windows(START_DATE, END_DATE):
        for row in collect_window(api_key, w_start, w_end):
            if row["link"] in global_seen:
                continue
            global_seen.add(row["link"])
            all_rows.append(row)

    return all_rows


def save_csv(rows, path=OUTPUT_CSV):
    """Write collected article rows to a CSV file."""
    if not rows:
        print("No rows to save.")
        return

    fieldnames = sorted(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {path}")


def main():
    """Run the full collection and write the output CSV."""
    api_key = get_api_key()
    rows = run_collection(api_key)
    save_csv(rows)
    print("Unique articles:", len(rows))


if __name__ == "__main__":
    main()
