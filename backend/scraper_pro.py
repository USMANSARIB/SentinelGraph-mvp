"""
backend/scraper_pro.py
Twikit + HTML hybrid scraper (safe defaults + HTML fallback)
- Search uses HTML scraping (no GQL)
- Timeline uses Twikit (requires numeric user id via user_by_login) with HTML fallback
- Tweet details tries Twikit.get_tweet_by_id then falls back to HTML parsing
- Rate limiting, retries, account rotation built in
"""

import asyncio
import random
import time
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# third-party (install in Colab if missing):
# pip install twikit httpx beautifulsoup4
try:
    from twikit import Client
except Exception:
    Client = None

import httpx
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper_pro")

# ---------- CONFIG ----------
GLOBAL_QPS = float(os.getenv("SG_QPS", "1.0"))   # requests per second global
PER_ACCOUNT_CONCURRENCY = int(os.getenv("SG_ACC_CONC", "2"))
REQUEST_TIMEOUT = int(os.getenv("SG_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("SG_RETRIES", "3"))
JITTER_LOW = 0.2
JITTER_HIGH = 1.0
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16 Safari/605.1.15"
]

# ---------- ACCOUNT / POOL ----------
@dataclass
class Account:
    name: str
    auth_token: str
    ct0: str
    proxy: Optional[str] = None
    client: Optional[Any] = field(default=None, repr=False)
    sem: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(PER_ACCOUNT_CONCURRENCY), repr=False)
    last_used: float = 0.0
    failures: int = 0

class AccountPool:
    def __init__(self, accounts: List[Account]):
        if not accounts:
            raise ValueError("AccountPool requires at least one account")
        self.accounts = accounts
        self._lock = asyncio.Lock()
        self._idx = 0

    async def init_clients(self):
        for acc in self.accounts:
            if Client is not None:
                try:
                    acc.client = Client("en-US")
                    # twikit expects a plain cookie dict
                    acc.client.set_cookies({"auth_token": acc.auth_token, "ct0": acc.ct0})
                    if acc.proxy:
                        # if twikit exposes set_proxy; guard with try-except
                        try:
                            acc.client.set_proxy(acc.proxy)
                        except Exception:
                            logger.debug(f"Proxy method not available for twikit client (acc={acc.name})")
                except Exception as e:
                    logger.warning(f"Failed to init twikit client for {acc.name}: {e}")
                    acc.client = None
            else:
                acc.client = None

    async def get_account(self) -> Account:
        async with self._lock:
            acc = self.accounts[self._idx]
            self._idx = (self._idx + 1) % len(self.accounts)
            return acc

# ---------- RATE LIMITER ----------
class GlobalRateLimiter:
    def __init__(self, qps: float):
        if qps <= 0:
            qps = 1.0
        self.min_delay = 1.0 / qps
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self):
        async with self._lock:
            now = time.time()
            elapsed = now - self._last
            to_wait = max(0.0, self.min_delay - elapsed)
            if to_wait > 0:
                await asyncio.sleep(to_wait + random.uniform(JITTER_LOW, JITTER_HIGH))
            self._last = time.time()

# ---------- UTILITIES ----------
def retryable(max_retries: int = MAX_RETRIES):
    def deco(fn):
        async def wrapper(*args, **kwargs):
            exc = None
            for i in range(max_retries):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    exc = e
                    backoff = (2 ** i) + random.random()
                    logger.debug(f"Retry {i+1}/{max_retries} for {fn.__name__} after error: {e}; sleeping {backoff:.1f}s")
                    await asyncio.sleep(backoff)
            logger.error(f"Operation {fn.__name__} failed after {max_retries} attempts: {exc}")
            raise exc
        return wrapper
    return deco

def _choose_ua():
    return random.choice(USER_AGENT_LIST)

def _quote_q(q: str):
    return httpx.utils.quote(q, safe='')

# ---------- HTML PARSING FALLBACK ----------
def parse_tweet_html(html: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    # Return minimal safe fields + raw snippet
    data = {"id": None, "text": None, "username": None, "created_at": None,
            "likes": None, "retweets": None, "replies": None, "media": [], "raw_html": None}
    data["raw_html"] = html[:4000]

    # Prefer meta tags (og:description often contains tweet text snippet)
    og_desc = soup.find("meta", {"property": "og:description"})
    if og_desc and og_desc.get("content"):
        data["text"] = og_desc["content"]

    # username from canonical link or meta
    author = soup.find("meta", {"property": "og:site_name"})
    if author and author.get("content"):
        data["username"] = author["content"]

    # created time meta
    time_tag = soup.find("meta", {"property": "article:published_time"})
    if time_tag and time_tag.get("content"):
        data["created_at"] = time_tag["content"]

    # Try to find tweet text from article or divs
    if not data["text"]:
        # look for main tweet text nodes
        tweet_div = soup.find("div", attrs={"data-testid": "tweetText"})
        if tweet_div:
            data["text"] = tweet_div.get_text(" ", strip=True)
        else:
            # fallback: first <article> text
            art = soup.find("article")
            if art:
                data["text"] = art.get_text(" ", strip=True)[:1000]

    # images
    og_image = soup.find("meta", {"property": "og:image"})
    if og_image and og_image.get("content"):
        data["media"].append(og_image["content"])

    return data

# ---------- SCRAPER ----------
class SafeScraper:
    def __init__(self, pool: AccountPool, qps: float = GLOBAL_QPS):
        self.pool = pool
        self.rate = GlobalRateLimiter(qps)
        self.http = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    async def _acquire(self, acc: Account):
        await acc.sem.acquire()
        acc.last_used = time.time()
        return acc

    async def _release(self, acc: Account):
        try:
            acc.sem.release()
        except Exception:
            pass

    # -------- SEARCH (HTML only) --------
    @retryable()
    async def search(self, query: str, limit: int = 20) -> List[Dict]:
        await self.rate.wait()
        acc = await self.pool.get_account()
        await self._acquire(acc)
        try:
            # Use web search (HTML) to avoid GQL / numeric ID constraints
            url = f"https://x.com/search?q={_quote_q(query)}&src=typed_query"
            headers = {"User-Agent": _choose_ua()}
            r = await self.http.get(url, headers=headers, follow_redirects=True)
            if r.status_code != 200:
                logger.warning(f"Search HTML returned {r.status_code} for query={query}")
                return []
            soup = BeautifulSoup(r.text, "html.parser")

            # Very best-effort parsing: locate tweet containers
            results = []
            # try 'article' tags (modern layout)
            articles = soup.find_all("article", limit=limit*2)
            for art in articles:
                if len(results) >= limit:
                    break
                text_el = art.find("div", attrs={"data-testid": "tweetText"})
                text = text_el.get_text(" ", strip=True) if text_el else art.get_text(" ", strip=True)[:800]
                # try to find link to tweet for id
                a = art.find("a", href=True)
                tweet_id = None
                if a:
                    href = a["href"]
                    # href like /username/status/12345
                    parts = href.split("/")
                    if len(parts) >= 4 and parts[-2] == "status":
                        tweet_id = parts[-1]
                results.append({"id": tweet_id, "text": text, "scraped_with_query": query})
            # final fallback: if no articles, return raw snippet
            if not results:
                return [{"id": None, "text": None, "raw_html": r.text[:1000], "scraped_with_query": query}]
            return results[:limit]
        finally:
            await self._release(acc)

    # -------- HELP: get numeric user id via twikit when possible --------
    async def _get_user_id(self, acc: Account, username: str) -> Optional[str]:
        """
        Try Twikit's user_by_login or user_by_id methods to resolve numeric id.
        Returns string id or None.
        """
        if acc.client:
            try:
                # try user_by_login (awaitable)
                u = await acc.client.user_by_login(username)
                if u and getattr(u, "id", None):
                    return str(getattr(u, "id"))
            except Exception as e:
                logger.debug(f"Twikit user_by_login failed for {username}: {e}")
        # last resort: try HTML (not robust)
        try:
            url = f"https://x.com/{username}"
            headers = {"User-Agent": _choose_ua()}
            r = await self.http.get(url, headers=headers)
            if r.status_code == 200:
                # try to parse numeric id in page (not guaranteed)
                if "profile_user_id" in r.text:
                    # crude
                    import re
                    m = re.search(r'profile_user_id["\']?\s*:\s*["\']?(\d+)', r.text)
                    if m:
                        return m.group(1)
        except Exception:
            pass
        return None

    # -------- USER TIMELINE (Twikit numeric user id preferred) --------
    @retryable()
    async def user_timeline(self, username_or_id: str, limit: int = 20) -> List[Dict]:
        await self.rate.wait()
        acc = await self.pool.get_account()
        await self._acquire(acc)
        try:
            # If the caller passed numeric id, use it directly
            numeric_id = None
            if username_or_id.isdigit():
                numeric_id = username_or_id
            else:
                numeric_id = await self._get_user_id(acc, username_or_id)

            if numeric_id and acc.client:
                try:
                    tweets_iter = await acc.client.get_user_tweets(numeric_id, "Tweets", count=limit)
                    out = []
                    for t in tweets_iter:
                        # normalize
                        out.append(self._normalize_tweet_from_twikit(t))
                        if len(out) >= limit:
                            break
                    return out
                except Exception as e:
                    logger.debug(f"Twikit timeline failed for {username_or_id} (id={numeric_id}): {e}")

            # HTML fallback timeline
            url = f"https://x.com/{username_or_id}"
            headers = {"User-Agent": _choose_ua()}
            r = await self.http.get(url, headers=headers)
            if r.status_code != 200:
                logger.warning(f"Timeline HTML returned {r.status_code} for {username_or_id}")
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            articles = soup.find_all("article", limit=limit*2)
            out = []
            for art in articles:
                if len(out) >= limit: break
                text_el = art.find("div", attrs={"data-testid": "tweetText"})
                text = text_el.get_text(" ", strip=True) if text_el else art.get_text(" ", strip=True)[:800]
                # try to extract id from links
                a = art.find("a", href=True)
                tweet_id = None
                if a:
                    href = a["href"]
                    parts = href.split("/")
                    if len(parts) >= 4 and parts[-2] == "status":
                        tweet_id = parts[-1]
                out.append({"id": tweet_id, "text": text, "username": username_or_id})
            return out
        finally:
            await self._release(acc)

    # -------- TWEET DETAILS (GQL then HTML fallback) --------
    @retryable()
    async def tweet_details(self, tweet_id: str) -> Dict:
        await self.rate.wait()
        acc = await self.pool.get_account()
        await self._acquire(acc)
        try:
            if acc.client:
                try:
                    t = await acc.client.get_tweet_by_id(tweet_id)
                    return self._normalize_tweet_from_twikit(t)
                except Exception as e:
                    logger.debug(f"Twikit get_tweet_by_id failed for {tweet_id}: {e}")

            # HTML fallback
            url = f"https://x.com/i/status/{tweet_id}"
            headers = {"User-Agent": _choose_ua()}
            r = await self.http.get(url, headers=headers, follow_redirects=True)
            if r.status_code == 200:
                parsed = parse_tweet_html(r.text)
                parsed["id"] = tweet_id
                parsed["scraped_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                # minimal text extraction from HTML page if missing
                if not parsed.get("text"):
                    parsed["text"] = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:1000]
                return parsed
            else:
                return {"error": f"HTTP {r.status_code}", "id": tweet_id}
        finally:
            await self._release(acc)

    # -------- normalizer for twikit objects ----------
    def _normalize_tweet_from_twikit(self, t, query: Optional[str] = None) -> Dict:
        out = {}
        try:
            out["id"] = getattr(t, "id", None)
            out["text"] = getattr(t, "text", None) or getattr(t, "rawContent", None) or getattr(t, "content", None)
            out["created_at"] = getattr(t, "created_at", None) or getattr(t, "createdAt", None)
            out["likes"] = getattr(t, "likeCount", None) or getattr(t, "likes", None)
            out["retweets"] = getattr(t, "retweetCount", None)
            out["replies"] = getattr(t, "replyCount", None)
            out["views"] = getattr(t, "viewCount", None)
            out["conversation_id"] = getattr(t, "conversation_id", None) or getattr(t, "conversationId", None)
            u = getattr(t, "user", None)
            if u:
                out["user"] = {
                    "id": getattr(u, "id", None),
                    "username": getattr(u, "username", None),
                    "name": getattr(u, "displayName", None) or getattr(u, "name", None),
                    "followers": getattr(u, "followersCount", None),
                    "verified": getattr(u, "verified", None),
                    "profile_image": getattr(u, "profile_image_url", None) or getattr(u, "avatar", None),
                }
            if query:
                out["scraped_with_query"] = query
        except Exception:
            out["error"] = "normalize_failed"
        return out

# ---------- USAGE DEMO FUNCTION ----------
async def demo_from_env():
    """
    Example bootstrap: reads AUTH/CT0 env vars (AUTH1/CT01, AUTH2/CT02 etc).
    DO NOT commit real secrets.
    """
    # Build accounts list from env variables AUTH1/CT01, AUTH2/CT02 ...
    accounts = []
    for i in range(1, 5):
        a = os.getenv(f"AUTH{i}")
        c = os.getenv(f"CT0{i}")
        if a and c:
            accounts.append(Account(name=f"acc{i}", auth_token=a, ct0=c, proxy=os.getenv(f"PROXY{i}")))
    if not accounts:
        # placeholder single account (replace with real values before running)
        accounts = [Account(name="local1", auth_token=os.getenv("AUTH1", "YOUR_AUTH"), ct0=os.getenv("CT01", "YOUR_CT0"))]
    pool = AccountPool(accounts)
    await pool.init_clients()
    scraper = SafeScraper(pool, qps=GLOBAL_QPS)

    # Quick smoke tests (for manual run)
    s = await scraper.search("india", limit=5)
    print("---SEARCH---")
    print(s)
    tl = await scraper.user_timeline("narendramodi", limit=5)  # prefer numeric id; this will try to resolve
    print("---TIMELINE---")
    print(tl)
    d = await scraper.tweet_details("1989415450447679764")
    print("---DETAILS---")
    print(d)

# End of file
