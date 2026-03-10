"""
Twitter/X Collector
Uses nitter (open-source Twitter frontend) for scraping
OR Twitter API v2 if API key is available
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import os
import logging

logger = logging.getLogger(__name__)

# Finance hashtags to monitor
FINANCE_HASHTAGS = [
    "日経平均", "株価", "円安", "日銀", "インフレ",
    "NISA", "投資信託", "為替", "経済ニュース",
]

# Public Nitter instances (Twitter mirror, no API key needed)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
]


class TwitterCollector:
    def __init__(self):
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "")

    async def fetch(self) -> List[Dict]:
        if self.bearer_token:
            return await self._fetch_via_api()
        else:
            return await self._fetch_via_nitter()

    async def _fetch_via_api(self) -> List[Dict]:
        """Use Twitter API v2 (requires Bearer Token)"""
        results = []
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        async with httpx.AsyncClient(timeout=15) as client:
            for hashtag in FINANCE_HASHTAGS[:5]:  # API rate limit
                try:
                    resp = await client.get(
                        "https://api.twitter.com/2/tweets/search/recent",
                        headers=headers,
                        params={
                            "query": f"#{hashtag} lang:ja -is:retweet",
                            "max_results": 10,
                            "tweet.fields": "public_metrics,created_at",
                            "sort_order": "relevancy",
                        },
                    )
                    data = resp.json()
                    for tweet in data.get("data", []):
                        metrics = tweet.get("public_metrics", {})
                        results.append({
                            "source": "Twitter/X",
                            "hashtag": hashtag,
                            "text": tweet["text"][:200],
                            "likes": metrics.get("like_count", 0),
                            "retweets": metrics.get("retweet_count", 0),
                            "created_at": tweet.get("created_at", ""),
                        })
                except Exception as e:
                    logger.warning(f"Twitter API hashtag #{hashtag} failed: {e}")

        results.sort(key=lambda x: x.get("likes", 0) + x.get("retweets", 0) * 3, reverse=True)
        return results[:20]

    async def _fetch_via_nitter(self) -> List[Dict]:
        """Scrape Nitter as fallback (no API key needed)"""
        results = []

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for instance in NITTER_INSTANCES:
                try:
                    # Test if instance is alive
                    test = await client.get(f"{instance}/search?q=%23日経平均&f=tweets", timeout=5)
                    if test.status_code != 200:
                        continue

                    for hashtag in FINANCE_HASHTAGS[:4]:
                        try:
                            resp = await client.get(
                                f"{instance}/search",
                                params={"q": f"#{hashtag}", "f": "tweets"},
                            )
                            soup = BeautifulSoup(resp.text, "html.parser")
                            tweets = soup.select(".timeline-item")

                            for tweet in tweets[:5]:
                                text_el = tweet.select_one(".tweet-content")
                                stats = tweet.select(".tweet-stat")
                                if text_el:
                                    likes = 0
                                    retweets = 0
                                    for stat in stats:
                                        icon = stat.select_one(".icon-heart")
                                        rt_icon = stat.select_one(".icon-retweet")
                                        val = stat.get_text(strip=True).replace(",", "")
                                        if icon and val.isdigit():
                                            likes = int(val)
                                        if rt_icon and val.isdigit():
                                            retweets = int(val)

                                    results.append({
                                        "source": "Twitter/X (Nitter)",
                                        "hashtag": hashtag,
                                        "text": text_el.get_text(strip=True)[:200],
                                        "likes": likes,
                                        "retweets": retweets,
                                    })
                        except Exception as e:
                            logger.warning(f"Nitter hashtag #{hashtag} failed: {e}")

                    break  # Use first working instance
                except Exception as e:
                    logger.warning(f"Nitter instance {instance} unavailable: {e}")

        results.sort(key=lambda x: x.get("likes", 0) + x.get("retweets", 0) * 3, reverse=True)
        return results[:15]
