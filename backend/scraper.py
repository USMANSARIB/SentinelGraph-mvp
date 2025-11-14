import json
import os
import requests
from datetime import datetime

class SimpleTwitterScraper:
    """
    Backup scraper using Nitter HTML as a lightweight fallback.
    Does not require Twitter login or cookies.
    """

    def __init__(self):
        self.base_url = "https://nitter.net/search?f=tweets&q={query}"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def search(self, query, limit=20):
        """Fetch tweets by HTML parsing via Nitter."""
        url = self.base_url.format(query=query)
        print(f"[SimpleScraper] Fetching: {url}")

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                print("[SimpleScraper] Failed request:", resp.status_code)
                return []

            return self._parse_nitter_html(resp.text)[:limit]

        except Exception as e:
            print("[SimpleScraper] Error:", e)
            return []

    def _parse_nitter_html(self, html):
        """Extract tweet text from Nitter HTML."""
        tweets = []
        parts = html.split('<div class="tweet-body">')

        for p in parts[1:]:
            start = p.find("<p>")
            end = p.find("</p>")
            if start != -1 and end != -1:
                content = p[start + 3:end]
                tweets.append(content)

        return tweets

    def save(self, tweets, path="data/raw/simple_scrape.json"):
        """Save tweets to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": datetime.utcnow().isoformat(), "tweets": tweets},
                f,
                indent=4
            )

        print(f"[SimpleScraper] Saved data → {path}")


def run_simple_scrape(query="india", limit=20):
    scraper = SimpleTwitterScraper()
    tweets = scraper.search(query, limit)
    print(f"[SimpleScraper] Retrieved {len(tweets)} tweets")
    scraper.save(tweets)
    return tweets


if __name__ == "__main__":
    print(run_simple_scrape())
