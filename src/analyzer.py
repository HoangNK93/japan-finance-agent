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


class ContentAnalyzer:
    async def generate_digest(self, all_data: Dict[str, List]) -> Dict:
        """Send all collected data to Claude and get content recommendations"""

        # Prepare data summary for Claude
        data_summary = self._prepare_summary(all_data)

        prompt = f"""Bạn là content strategist cho kênh YouTube về kinh tế vĩ mô và vi mô Nhật Bản.

Dưới đây là dữ liệu trending hôm nay ({datetime.now().strftime('%Y-%m-%d')}):

{data_summary}

Hãy phân tích và trả về JSON với cấu trúc sau:
{{
  "top_topics": [
    {{
      "rank": 1,
      "title": "Tên topic (tiếng Việt)",
      "title_jp": "Tên topic (tiếng Nhật)",
      "category": "macro|micro",
      "urgency": "high|medium|low",
      "explanation_vi": "1 câu giải thích đơn giản chủ đề này là gì bằng tiếng Việt (dành cho người chưa biết)",
      "why_trending": "Giải thích ngắn tại sao topic này đang hot",
      "video_angle": "Góc độ làm video độc đáo cho kênh kinh tế",
      "suggested_title": "Gợi ý tiêu đề YouTube hấp dẫn (tiếng Nhật hoặc Việt)",
      "key_points": ["điểm 1", "điểm 2", "điểm 3"],
      "sources": ["nguồn 1", "nguồn 2"]
    }}
  ],
  "macro_summary": "Tóm tắt bức tranh vĩ mô Nhật Bản hôm nay (2-3 câu)",
  "micro_summary": "Tóm tắt xu hướng vi mô / doanh nghiệp nổi bật (2-3 câu)",
  "weekly_theme": "Chủ đề lớn đang được quan tâm tuần này",
  "alert": "Cảnh báo hoặc sự kiện quan trọng sắp diễn ra (nếu có, để trống nếu không)"
}}

Chỉ trả về JSON, không có text thêm. Top 5 topics quan trọng nhất."""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    CLAUDE_API_URL,
                    headers={
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                    },
                    json={
                        "model": MODEL,
                        "max_tokens": 2000,
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
        for item in all_data.get("RSS (Nikkei/Bloomberg)", [])[:5]:
            topics.append({
                "rank": len(topics) + 1,
                "title": item["title"],
                "title_jp": item["title"],
                "category": item.get("category", "macro"),
                "urgency": "medium",
                "why_trending": item.get("summary", ""),
                "video_angle": "Phân tích tác động đến kinh tế Nhật",
                "suggested_title": item["title"],
                "key_points": [],
                "sources": [item["source"]],
            })
        return {
            "top_topics": topics,
            "macro_summary": "Không thể phân tích tự động. Vui lòng kiểm tra dữ liệu thủ công.",
            "micro_summary": "",
            "weekly_theme": "",
            "alert": "",
        }
