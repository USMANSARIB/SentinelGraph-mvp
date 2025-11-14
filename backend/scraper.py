import json
import os
import requests
from datetime import datetime

class SimpleTwitterScraper:
    """
    Backup scraper for SentinelGraph.
    Uses Twitter's unofficial search API (no login required).
    Good for basic narrative spike detection.
    """

    BASE_URL = "https://twitter.com/i/api/2/search/adaptive.json"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

    def search(self, query, limit=50):
        """
        Fetch tweets using simple GET requests.
        Works best for small batches.
        """
        url = f"https://nitter.net/search?f=tweets&q={query}"
        print(f"[SimpleScraper] Fetching from: {url}")

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                print("[Error] Failed to fetch data.")
                return []

            tweets = self._parse_nitter_html(resp.text)
            return tweets[:limit]

        except Exception as e:
            print("Error:", e)
            return []

    def _parse_nitter_html(self, html):
        """
        VERY basic HTML parsing.  
        Enough to extract text content for testing.
        """
        tweets = []
        parts = html.split('<div class="tweet-body">')

        for p in parts[1:]:
            content_start = p.find("<p>")
            content_end = p.find("</p>")
            if content_start != -1 and content_end != -1:
                content = p[content_start+3:content_end]
                tweets.append(content)

        return tweets

    def save(self, tweets, path="data/raw/simple_scrape.json"):
        """
        Save scraped tweets to JSON.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "tweets": tweets
            }, f, indent=4)

        print(f"[SimpleScraper] Saved: {path}")


def run_simple_scrape(query="india", limit=20):
    scraper = SimpleTwitterScraper()
    tweets = scraper.search(query, limit)

    print(f"[SimpleScraper] Retrieved {len(tweets)} tweets")
    
    scraper.save(tweets)

    return tweets


if __name__ == "__main__":
    print(run_simple_scrape())
