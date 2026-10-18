"""Fetch Google Scholar citation data for the homepage.

Only two values are consumed by the site (see _includes/fetch_google_scholar_stats.html):
the total number of citations and the per-publication citation counts. Both are
present on the public author profile page, so a single HTTP request is enough.

The `scholarly` package was used before, but it retries HTTP 403 responses inside
an unbounded loop (the `continue` statements in `scholarly._navigator._get_page`
skip the retry counter), which made the daily GitHub Actions job hang until the
6 hour job limit whenever Google Scholar throttled the runner. Here the request
count and the retry budget are both bounded.
"""

import json
import os
import re
import sys
import time
from datetime import datetime

import requests

AUTHOR_ID = os.environ["GOOGLE_SCHOLAR_ID"]
PROFILE_URL = (
    "https://scholar.google.com/citations"
    f"?hl=en&user={AUTHOR_ID}&cstart=0&pagesize=100"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_ATTEMPTS = 4
TIMEOUT = 20


def fetch_profile_html() -> str:
    """Download the profile page, with a bounded number of retries."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(PROFILE_URL, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code == 200 and "gsc_prf_in" in response.text:
                return response.text
            last_error = f"HTTP {response.status_code} ({len(response.text)} bytes)"
        except requests.RequestException as exc:
            last_error = repr(exc)
        print(f"Attempt {attempt}/{MAX_ATTEMPTS} failed: {last_error}", file=sys.stderr)
        if attempt < MAX_ATTEMPTS:
            time.sleep(15 * attempt)
    raise SystemExit(f"Could not fetch the Google Scholar profile page: {last_error}")


def parse_profile(html: str) -> dict:
    def first_int(pattern: str, default: int = 0) -> int:
        match = re.search(pattern, html)
        return int(match.group(1)) if match else default

    # The summary table holds, in order: citations, citations since 2020,
    # h-index, h-index since 2020, i10-index, i10-index since 2020.
    stats = [int(v) for v in re.findall(r'class="gsc_rsb_std">(\d+)<', html)]
    if not stats:
        raise SystemExit("No citation summary found on the profile page (layout changed?)")

    citedby = first_int(r'class="gsc_rsb_std">(\d+)<')
    name_match = re.search(r'id="gsc_prf_in"[^>]*>([^<]+)<', html)

    publications = {}
    for row in html.split('class="gsc_a_tr"')[1:]:
        id_match = re.search(r"citation_for_view=([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)", row)
        if not id_match:
            continue
        pub_id = id_match.group(1)
        count_match = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d*)<', row)
        publications[pub_id] = {
            "author_pub_id": pub_id,
            "num_citations": int(count_match.group(1)) if count_match and count_match.group(1) else 0,
        }

    return {
        "name": name_match.group(1) if name_match else AUTHOR_ID,
        "citedby": citedby,
        "citedby5y": stats[1] if len(stats) > 1 else 0,
        "hindex": stats[2] if len(stats) > 2 else 0,
        "hindex5y": stats[3] if len(stats) > 3 else 0,
        "i10index": stats[4] if len(stats) > 4 else 0,
        "i10index5y": stats[5] if len(stats) > 5 else 0,
        "updated": str(datetime.now()),
        "publications": publications,
    }


def main() -> None:
    author = parse_profile(fetch_profile_html())
    print(json.dumps(author, indent=2))

    os.makedirs("results", exist_ok=True)
    with open("results/gs_data.json", "w") as outfile:
        json.dump(author, outfile, ensure_ascii=False)

    shieldsio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": f"{author['citedby']}",
    }
    with open("results/gs_data_shieldsio.json", "w") as outfile:
        json.dump(shieldsio_data, outfile, ensure_ascii=False)


if __name__ == "__main__":
    main()
