"""
Japan Finance AI Agent
Collects trending topics and sends daily digest to Telegram
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional

from collectors.google_trends import GoogleTrendsCollector
from collectors.rss_collector import RSSCollector
from collectors.youtube_collector import YouTubeCollector
from collectors.twitter_collector import TwitterCollector
from analyzer import ContentAnalyzer
from telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def run_agent():
    logger.info("🚀 Japan Finance Agent starting...")

    # --- Collect data from all sources ---
    collectors_results = await asyncio.gather(
        GoogleTrendsCollector().fetch(),
        RSSCollector().fetch(),
        YouTubeCollector().fetch(),
        TwitterCollector().fetch(),
        return_exceptions=True,
    )

    source_names = ["Google Trends", "RSS (Nikkei/Bloomberg)", "YouTube", "Twitter/X"]
    all_data = {}
    for name, result in zip(source_names, collectors_results):
        if isinstance(result, Exception):
            logger.warning(f"⚠️ {name} failed: {result}")
            all_data[name] = []
        else:
            logger.info(f"✅ {name}: {len(result)} items")
            all_data[name] = result

    # --- Analyze with Claude API ---
    analyzer = ContentAnalyzer()
    digest = await analyzer.generate_digest(all_data)

    # --- Send to Telegram ---
    bot = TelegramBot(
        token=os.environ["TELEGRAM_BOT_TOKEN"],
        chat_id=os.environ["TELEGRAM_CHAT_ID"],
    )
    await bot.send_digest(digest)
    logger.info("✅ Digest sent to Telegram!")


if __name__ == "__main__":
    asyncio.run(run_agent())
