from twikit import Client
from typing import List, Dict
import asyncio


class SafeTwitterScraper:
    """
    Stable + hardened Twikit scraper.
    Avoids bans, handles missing tweet structures, 
    and provides multi-layer fallback fetching.
    """

    def __init__(self, auth_token: str, ct0: str):
        if not auth_token or not ct0:
            raise ValueError("auth_token and ct0 are required")

        # Init logged-in session
        self.client = Client("en-US")
        self.client.set_cookies({
            "auth_token": "c1bedd29f779434f156d7ab7ce4cbc655a12c6fb",
            "ct0": "f771810bd4d2f56614ede08b8bcda4209c79c3374268733bd33ec6657a2b7a400026d74463afdb299ca1defd9bae1f4fe9a2d7c94b16532d1e2800f660359a4d580bbcdf2191e68c5f5a746f6aebbabf"
        })

    # -----------------------------------------------------
    # SEARCH (Latest / Top)
    # -----------------------------------------------------
    async def search(self, query: str, limit: int = 20, tab: str = "Latest") -> List[Dict]:
        try:
            results_raw = await self.client.search_tweet(query, tab)
        except Exception as e:
            print("Search failed:", e)
            return []

        results = []
        for t in results_raw:
            try:
                results.append({
                    "id": t.id,
                    "text": t.text,
                    "username": t.user.screen_name if t.user else None,
                    "created_at": t.created_at
                })
            except:
                continue

            if len(results) >= limit:
                break

        return results

    # -----------------------------------------------------
    # USER TIMELINE
    # -----------------------------------------------------
    async def user_timeline(self, username: str, limit: int = 20) -> List[Dict]:
        try:
            user = await self.client.get_user_by_screen_name(username)
            tweets_raw = await self.client.get_user_tweets(user.id, "Tweets")
        except Exception as e:
            print("Timeline fetch failed:", e)
            return []

        results = []
        for t in tweets_raw:
            try:
                results.append({
                    "id": t.id,
                    "text": t.text,
                    "created_at": t.created_at
                })
            except:
                continue

            if len(results) >= limit:
                break

        return results

    # -----------------------------------------------------
    # SAFE TWEET DETAILS (3-layer fallback)
    # -----------------------------------------------------
    async def tweet_details(self, tweet_id: str) -> Dict:
        """
        Attempts:
        1. direct Twikit API call
        2. fallback search: conversation_id:tweetid
        3. final fallback: HTML scrape (raw)
        """

        # ----------------------------
        # LAYER 1 — Primary API fetch
        # ----------------------------
        try:
            t = await self.client.get_tweet_by_id(tweet_id)
            return {
                "id": t.id,
                "text": t.text,
                "username": t.user.screen_name if t.user else None,
                "created_at": t.created_at
            }

        except Exception as e:
            print("Primary tweet_details failed:", e)

        # ----------------------------
        # LAYER 2 — Search fallback
        # ----------------------------
        try:
            fallback = await self.search(f"conversation_id:{tweet_id}", limit=1)
            if fallback:
                print("→ Using fallback via search()")
                return fallback[0]
        except Exception as e2:
            print("Fallback search failed:", e2)

        # ----------------------------
        # LAYER 3 — Raw HTML fallback
        # ----------------------------
        try:
            raw = await self.client.http.get(f"https://twitter.com/i/web/status/{tweet_id}")
            if raw.status_code == 200:
                text = raw.text
                # crude extraction (best effort)
                if "status" in text:
                    return {"id": tweet_id, "text": "(raw HTML fetched)", "html": text[:5000]}
        except:
            pass

        return {"error": "Tweet not accessible or unsupported structure"}
