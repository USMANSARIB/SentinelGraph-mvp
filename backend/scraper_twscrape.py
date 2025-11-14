"""
SentinelGraph - Advanced Async Twitter Scraper (twscrape)
---------------------------------------------------------

This is the REAL scraper engine for SentinelGraph.
It uses async/await and twscrape's GraphQL API for:
- Fast scraping
- Better rate-limit handling
- Multi-account rotation
- Parallel scraping
- Streaming tweet processing

IMPORTANT:
    - This DOES NOT RUN on Termux.
    - Must run on Colab / Laptop / Server only.
    - Requires twscrape + a valid Twitter cookie.

Usage (in Colab or main backend):
---------------------------------
from backend.scraper_twscrape import TwitterScraper
scraper = TwitterScraper()
data = await scraper.search("india", limit=200)

"""

import asyncio
from typing import List, Dict, Optional, Union

try:
    from twscrape import API, gather
except Exception:
    API = None
    gather = None


# ----------------------------------------------------------
# NORMALIZATION UTILITIES
# ----------------------------------------------------------

def normalize_tweet(t) -> Dict:
    """Convert raw twscrape Tweet object into a clean dictionary."""
    return {
        "id": t.id,
        "date": str(t.date),
        "username": getattr(t.user, "username", None),
        "displayName": getattr(t.user, "displayName", None),
        "content": getattr(t, "rawContent", "") or getattr(t, "content", ""),
        "likes": getattr(t, "likeCount", None),
        "retweets": getattr(t, "retweetCount", None),
        "replies": getattr(t, "replyCount", None),
        "views": getattr(t, "viewCount", None),
        "source_label": getattr(t, "sourceLabel", None),
    }


def normalize_user(u) -> Dict:
    """Normalize user object."""
    return {
        "id": u.id,
        "username": u.username,
        "displayName": u.displayName,
        "followers": u.followersCount,
        "following": u.friendsCount,
        "verified": u.verified,
    }


# ----------------------------------------------------------
# SCRAPER CLASS
# ----------------------------------------------------------

class TwitterScraper:
    """
    Async scraper using twscrape API.
    Must run in an async context.

    Example:
    --------
    scraper = TwitterScraper()
    data = asyncio.run(scraper.search("india", limit=200))
    """

    def __init__(self):
        if API is None:
            raise RuntimeError(
                "twscrape is not installed or cannot be imported. "
                "This scraper must run in Colab or laptop, never Termux."
            )

        self.api = API()  # automatically loads stored accounts

    # ------------------------------------------------------
    # SEARCH SCRAPER
    # ------------------------------------------------------
    async def search(self, query: str, limit: int = 100) -> List[Dict]:
        """Search tweets asynchronously."""
        tweets = await gather(self.api.search(query, limit=limit))
        return [normalize_tweet(t) for t in tweets]

    # ------------------------------------------------------
    # USER TIMELINE SCRAPER
    # ------------------------------------------------------
    async def user_timeline(self, username: str, limit: int = 200) -> List[Dict]:
        """Scrape tweets from a user's timeline."""
        tweets = await gather(self.api.user_tweets(username, limit=limit))
        return [normalize_tweet(t) for t in tweets]

    # ------------------------------------------------------
    # USER INFO SCRAPER
    # ------------------------------------------------------
    async def get_user(self, username: str) -> Optional[Dict]:
        """Fetch user profile."""
        user = await self.api.user_by_login(username)
        return normalize_user(user) if user else None

    # ------------------------------------------------------
    # TWEET DETAILS
    # ------------------------------------------------------
    async def tweet_details(self, tweet_id: Union[str, int]) -> Optional[Dict]:
        """Fetch full details about a tweet."""
        t = await self.api.tweet_details(int(tweet_id))
        return normalize_tweet(t) if t else None

    # ------------------------------------------------------
    # PARALLEL SCRAPING
    # ------------------------------------------------------
    async def parallel_search(self, queries: List[str], limit: int = 50) -> Dict[str, List[Dict]]:
        """
        Run multiple searches in parallel.
        Example:
            await scraper.parallel_search(["bjp", "congress"], limit=100)

        """
        tasks = [self.api.search(q, limit=limit) for q in queries]
        results = await gather(*tasks)

        return {
            q: [normalize_tweet(t) for t in tweets]
            for q, tweets in zip(queries, results)
        }


# ----------------------------------------------------------
# TEST ENVIRONMENT CHECK (used by backend)
# ----------------------------------------------------------

def test_environment():
    return {
        "twscrape_installed": API is not None,
        "async_ready": asyncio.iscoroutinefunction(TwitterScraper.search),
        "message": "Environment ready for async scraping on Colab/laptop."
    }


# ----------------------------------------------------------
# SAFE MAIN EXECUTION BLOCK
# ----------------------------------------------------------

if __name__ == "__main__":
    print("This scraper is async and must be run inside Colab or a Python async environment.")
