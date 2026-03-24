"""
Content Analyzer using Claude API
Analyzes collected data and generates YouTube content recommendations
"""

import httpx
import json
import os
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """
あなたは日本の経済・ビジネス系YouTubeチャンネル「shiba_japan_finance」のコンテンツストラテジストです。

【チャンネル情報】
- ターゲット: 30〜50代の日本人ビジネスパーソン
- テーマ: 日本経済 + 世界経済・国際情勢
- 競合: すあし社長（大人の学び直しTV, 100万人）、サムライ経済学
- 差別化: 時事性が高い、数字重視、「なぜ？」の深掘り

【重要な優先順位】
世界・国際テーマも積極的に取り上げる。特に以下の国・地域は日本人の関心が高い:
🇺🇸 米国（トランプ政策・Fed・AI）> 🇨🇳 中国（経済・EV・地政学）> 🇷🇺🇺🇦 ロシア/ウクライナ > 🇰🇷 韓国 > 🇩🇪 ドイツ > 🇮🇳 インド > その他

【効果的なタイトル公式】
- 「なぜ〜なのか？——〜の真実」
- 「〜が崩壊しつつある理由——日本への影響」
- 「〜はなぜ失敗したのか？——経済学で読み解く」

【topic選定基準（優先順位順）】
1. 日本に直接または間接的に影響がある
2. 「ショック」または逆説的な要素がある（意外な事実）
3. 競合チャンネルがまだ深く扱っていない
4. 単なるニュースではなく経済学的に説明できる

各topicに必ず含めること:
- title: 日本語タイトル（上記の公式を使う）
- title_jp: タイトル（同じでOK）
- why_trending: なぜ今これが重要か（1〜2文）
- video_angle: 差別化できる切り口（競合と何が違うか）
- suggested_title: クリックされやすい完成形タイトル
- key_points: 動画で必ず触れるべき3つのポイント
- japan_connection: 必ず「これは日本にとって何を意味するか」で締める
- thumbnail_number: サムネイルに入れるべき数字や数値（例: "-2.3%", "30年ぶり"）
- urgency: "high" | "medium" | "low"
- category: "japan" | "global" | "us" | "china" | "geopolitics" | "markets"
- country_flag: 関連国の国旗絵文字（例: 🇺🇸🇨🇳）
- shorts_hooks: rank 1のみ — YouTubeショーツ用の60秒フックアイデア3つ（list[str]）
"""


class ContentAnalyzer:
    async def generate_digest(self, all_data: Dict[str, List]) -> Dict:
        """Send all collected data to Claude and get content recommendations"""

        data_summary = self._prepare_summary(all_data)

        prompt = f"""以下は本日（{datetime.now().strftime('%Y-%m-%d')}）のトレンドデータです:

{data_summary}

以下のJSON形式で回答してください。JSONのみ返すこと:
{{
  "top_topics": [
    {{
      "rank": 1,
      "title": "日本語タイトル",
      "title_jp": "日本語タイトル（同じでOK）",
      "category": "japan|global|us|china|geopolitics|markets",
      "urgency": "high|medium|low",
      "country_flag": "🇺🇸",
      "why_trending": "なぜ今重要か（1〜2文）",
      "video_angle": "差別化できる切り口",
      "suggested_title": "クリックされやすい完成形タイトル",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"],
      "japan_connection": "これは日本にとって何を意味するか",
      "thumbnail_number": "-2.3%",
      "shorts_hooks": ["フック1", "フック2", "フック3"],
      "sources": ["source1"]
    }}
  ],
  "macro_summary": "本日の日本マクロ経済概況（2〜3文）",
  "micro_summary": "注目の企業・ミクロ動向（2〜3文）",
  "weekly_theme": "今週の大テーマ",
  "alert": "重要予定イベント（なければ空文字）"
}}

Top 2 topics（最もホットなものだけ）。shorts_hooksはrank 1のみ含める。"""

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    CLAUDE_API_URL,
                    headers={
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                    },
                    json={
                        "model": MODEL,
                        "max_tokens": 8192,
                        "system": SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                result = resp.json()
                text = result["content"][0]["text"]

                # Clean and parse JSON
                text = text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                text = text.strip()

                return json.loads(text)

        except Exception as e:
            logger.error(f"Claude API failed: {e}")
            return self._fallback_digest(all_data)

    def _prepare_summary(self, all_data: Dict) -> str:
        lines = []

        # Google Trends
        trends = all_data.get("Google Trends", [])
        if trends:
            lines.append("=== GOOGLE TRENDS JAPAN ===")
            for item in trends[:10]:
                score = f" (score: {item['score']})" if item.get("score") else ""
                lines.append(f"- {item['title']}{score}")

        # RSS News
        rss_items = all_data.get("RSS (Nikkei/Bloomberg)", [])
        if rss_items:
            lines.append("\n=== LATEST NEWS (RSS) ===")
            for item in rss_items[:15]:
                lines.append(f"[{item['source']}] {item['title']}")
                if item.get("summary"):
                    lines.append(f"  → {item['summary'][:100]}")

        # YouTube
        yt_items = all_data.get("YouTube", [])
        if yt_items:
            lines.append("\n=== YOUTUBE TRENDING JP ===")
            for item in yt_items[:8]:
                views = f" ({item['views']:,} views)" if item.get("views") else ""
                lines.append(f"- {item['title']} [{item.get('channel', '')}]{views}")

        # Twitter
        tw_items = all_data.get("Twitter/X", [])
        if tw_items:
            lines.append("\n=== TWITTER/X TRENDING ===")
            for item in tw_items[:10]:
                lines.append(f"#{item['hashtag']}: {item['text'][:100]}")

        return "\n".join(lines)

    def _fallback_digest(self, all_data: Dict) -> Dict:
        """Simple fallback if Claude API fails"""
        topics = []
        for item in all_data.get("RSS (Nikkei/Bloomberg)", [])[:2]:
            topics.append({
                "rank": len(topics) + 1,
                "title": item["title"],
                "title_jp": item["title"],
                "category": "japan",
                "urgency": "medium",
                "country_flag": "🇯🇵",
                "why_trending": item.get("summary", ""),
                "video_angle": "",
                "suggested_title": item["title"],
                "key_points": [],
                "japan_connection": "",
                "thumbnail_number": "",
                "sources": [item["source"]],
            })
        return {
            "top_topics": topics,
            "macro_summary": "Không thể phân tích tự động. Vui lòng kiểm tra dữ liệu thủ công.",
            "micro_summary": "",
            "weekly_theme": "",
            "alert": "",
        }
