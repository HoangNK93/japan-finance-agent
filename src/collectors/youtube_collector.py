"""
YouTube Data API v3 Collector
Finds trending finance/economy videos in Japan
"""

import httpx
from typing import List, Dict
from datetime import datetime, timezone, timedelta
import os
import logging

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "日本経済 解説",
    "株式市場 今日",
    "円安 影響",
    "日銀 金融政策",
    "インフレ 日本",
    "NISA 投資",
    "景気後退",
    "マクロ経済",
]


class YouTubeCollector:
    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def fetch(self) -> List[Dict]:
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not set, skipping YouTube collection")
            return []

        results = []
        async with httpx.AsyncClient(timeout=15) as client:
            # Get trending videos in Japan - Finance category (id=25)
            try:
                resp = await client.get(
                    f"{self.base_url}/videos",
                    params={
                        "part": "snippet,statistics",
                        "chart": "mostPopular",
                        "regionCode": "JP",
                        "videoCategoryId": "25",  # News & Politics
                        "maxResults": 10,
                        "key": self.api_key,
                    },
                )
                data = resp.json()
                for item in data.get("items", []):
                    snippet = item["snippet"]
                    stats = item.get("statistics", {})
                    results.append({
                        "source": "YouTube Trending JP",
                        "title": snippet["title"],
                        "channel": snippet["channelTitle"],
                        "views": int(stats.get("viewCount", 0)),
                        "published": snippet["publishedAt"],
                        "url": f"https://youtu.be/{item['id']}",
                        "thumbnail": snippet["thumbnails"]["medium"]["url"],
                    })
            except Exception as e:
                logger.warning(f"YouTube trending failed: {e}")

            # Search for specific finance queries
            published_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
            for query in SEARCH_QUERIES[:4]:  # limit API quota
                try:
                    resp = await client.get(
                        f"{self.base_url}/search",
                        params={
                            "part": "snippet",
                            "q": query,
                            "type": "video",
                            "regionCode": "JP",
                            "relevanceLanguage": "ja",
                            "order": "viewCount",
                            "publishedAfter": published_after,
                            "maxResults": 3,
                            "key": self.api_key,
                        },
                    )
                    data = resp.json()
                    for item in data.get("items", []):
                        snippet = item["snippet"]
                        results.append({
                            "source": "YouTube Search",
                            "query": query,
                            "title": snippet["title"],
                            "channel": snippet["channelTitle"],
                            "published": snippet["publishedAt"],
                            "url": f"https://youtu.be/{item['id']['videoId']}",
                        })
                except Exception as e:
                    logger.warning(f"YouTube search '{query}' failed: {e}")

        # Deduplicate by title
        seen = set()
        unique = []
        for r in results:
            if r["title"] not in seen:
                seen.add(r["title"])
                unique.append(r)

        return unique[:20]
