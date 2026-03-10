"""
Google Trends collector - Japan region
Tracks finance/economy keywords trending in Japan
"""

from pytrends.request import TrendReq
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

FINANCE_KEYWORDS = [
    "日経平均", "株価", "円安", "円高", "インフレ",
    "金利", "日銀", "GDP", "景気", "仮想通貨",
    "投資", "経済", "物価", "為替", "NISA",
]


class GoogleTrendsCollector:
    def __init__(self):
        self.pytrends = TrendReq(hl="ja-JP", tz=540)  # JST timezone

    async def fetch(self) -> List[Dict]:
        results = []

        # Get daily trending searches in Japan
        try:
            trending = self.pytrends.trending_searches(pn="japan")
            for term in trending[0].tolist()[:20]:
                results.append({
                    "source": "Google Trends",
                    "title": term,
                    "type": "trending_search",
                    "score": None,
                })
        except Exception as e:
            logger.warning(f"Trending searches failed: {e}")

        # Get interest over time for finance keywords
        try:
            # Split keywords into batches of 5 (API limit)
            for i in range(0, len(FINANCE_KEYWORDS), 5):
                batch = FINANCE_KEYWORDS[i:i+5]
                self.pytrends.build_payload(batch, geo="JP", timeframe="now 1-d")
                interest = self.pytrends.interest_over_time()

                if not interest.empty:
                    latest = interest.iloc[-1]
                    for kw in batch:
                        if kw in latest and latest[kw] > 30:  # threshold: score > 30
                            results.append({
                                "source": "Google Trends",
                                "title": kw,
                                "type": "keyword_spike",
                                "score": int(latest[kw]),
                            })
        except Exception as e:
            logger.warning(f"Interest over time failed: {e}")

        # Sort by score descending
        results.sort(key=lambda x: x.get("score") or 0, reverse=True)
        return results[:15]
