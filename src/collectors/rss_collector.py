"""
RSS Collector - Nikkei, Bloomberg Japan, BOJ, NHK, Japan Times
Fetches latest economic/financial news articles
"""

import feedparser
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

RSS_FEEDS = [
    {
        "name": "Nikkei",
        "url": "https://www.nikkei.com/rss/news.rdf",
        "category": "macro",
    },
    {
        "name": "NHK World - Economy",
        "url": "https://www3.nhk.or.jp/nhkworld/en/news/feeds/economy/",
        "category": "macro",
    },
    {
        "name": "Japan Times - Business",
        "url": "https://www.japantimes.co.jp/news/business/feed/",
        "category": "micro",
    },
    {
        "name": "Bloomberg Japan",
        "url": "https://www.bloomberg.co.jp/feeds/bbiz",
        "category": "macro",
    },
    {
        "name": "Bank of Japan",
        "url": "https://www.boj.or.jp/en/rss/feed.xml",
        "category": "macro",
    },
    {
        "name": "Yahoo Finance Japan",
        "url": "https://news.yahoo.co.jp/rss/topics/business.xml",
        "category": "micro",
    },
    {
        "name": "東洋経済オンライン",
        "url": "https://toyokeizai.net/list/feed/rss",
        "category": "macro",
    },
]

FINANCE_KEYWORDS_JA = [
    "経済", "株", "円", "金利", "インフレ", "物価", "日銀", "GDP",
    "景気", "為替", "投資", "企業", "収益", "利益", "市場",
    "上場", "増収", "減収", "赤字", "黒字",
]


def is_finance_related(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in FINANCE_KEYWORDS_JA)


def parse_date(entry) -> Optional[datetime]:
    for attr in ["published_parsed", "updated_parsed"]:
        if hasattr(entry, attr) and getattr(entry, attr):
            import time
            return datetime.fromtimestamp(time.mktime(getattr(entry, attr)), tz=JST)
    return None


class RSSCollector:
    async def fetch(self) -> List[Dict]:
        results = []
        cutoff = datetime.now(JST) - timedelta(hours=24)

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for feed_config in RSS_FEEDS:
                try:
                    resp = await client.get(feed_config["url"])
                    feed = feedparser.parse(resp.text)

                    for entry in feed.entries[:20]:
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        link = entry.get("link", "")
                        pub_date = parse_date(entry)

                        # Only last 24h
                        if pub_date and pub_date < cutoff:
                            continue

                        # Finance filter (skip for finance-specific feeds)
                        if feed_config["name"] not in ["Nikkei", "Bank of Japan", "Bloomberg Japan"]:
                            if not is_finance_related(title, summary):
                                continue

                        results.append({
                            "source": feed_config["name"],
                            "category": feed_config["category"],
                            "title": title,
                            "summary": summary[:200] if summary else "",
                            "url": link,
                            "published": pub_date.isoformat() if pub_date else "",
                        })

                except Exception as e:
                    logger.warning(f"RSS {feed_config['name']} failed: {e}")

        # Sort by date descending
        results.sort(key=lambda x: x.get("published", ""), reverse=True)
        return results[:30]
