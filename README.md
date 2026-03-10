# 🗾 Japan Finance AI Agent

Daily digest agent cho kênh YouTube kinh tế Nhật Bản.  
Tự động thu thập trending topics và gợi ý nội dung video mỗi sáng qua Telegram.

## 📊 Nguồn dữ liệu

| Nguồn | Loại | API Key cần? |
|-------|------|-------------|
| Google Trends JP | Trending keywords | ❌ Không cần |
| Nikkei RSS | Tin tức kinh tế | ❌ Không cần |
| Reuters Japan RSS | Tin tức macro/micro | ❌ Không cần |
| Bloomberg Japan RSS | Tin tức tài chính | ❌ Không cần |
| Bank of Japan RSS | Chính sách tiền tệ | ❌ Không cần |
| Yahoo Finance JP RSS | Tin doanh nghiệp | ❌ Không cần |
| YouTube Data API v3 | Trending videos JP | ✅ Optional |
| Twitter/X | Trending hashtags | ✅ Optional (có fallback) |

## ⚙️ Setup

### Bước 1: Tạo Telegram Bot

1. Nhắn tin `@BotFather` trên Telegram
2. Gõ `/newbot` → đặt tên bot → lấy **Bot Token**
3. Tạo group/channel riêng cho digest
4. Thêm bot vào group với quyền Admin
5. Lấy **Chat ID**: nhắn tin bất kỳ vào group, rồi truy cập:  
   `https://api.telegram.org/bot<TOKEN>/getUpdates`

### Bước 2: Lấy API Keys

**Anthropic (Claude) - BẮT BUỘC:**
- Đăng ký tại https://console.anthropic.com
- Tạo API key

**YouTube Data API v3 - OPTIONAL:**
- Vào https://console.cloud.google.com
- Tạo project → Enable "YouTube Data API v3"
- Tạo API key (miễn phí, 10,000 units/day)

**Twitter Bearer Token - OPTIONAL:**
- Đăng ký developer tại https://developer.twitter.com
- Tạo app → lấy Bearer Token
- Nếu không có, agent sẽ dùng Nitter scraping

### Bước 3: Cấu hình GitHub Secrets

Vào repo GitHub → **Settings → Secrets and variables → Actions**

Thêm các secrets sau:

| Secret Name | Required | Mô tả |
|-------------|----------|-------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token từ @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | ID của group/channel |
| `YOUTUBE_API_KEY` | Optional | YouTube Data API v3 |
| `TWITTER_BEARER_TOKEN` | Optional | Twitter API v2 |

### Bước 4: Deploy

```bash
git clone <your-repo>
cd japan-finance-agent
git add .
git commit -m "Initial setup"
git push origin main
```

GitHub Actions sẽ tự động chạy mỗi ngày lúc **7:00 sáng JST**.

### Test thủ công

Vào GitHub → **Actions → Japan Finance Daily Digest → Run workflow**

## 💰 Chi phí ước tính

| Service | Cost |
|---------|------|
| GitHub Actions | Free (2,000 min/month) |
| Claude API (claude-sonnet) | ~$0.01-0.03/ngày |
| YouTube API | Free (10k units/day) |
| Nitter scraping | Free |
| **Tổng** | **~$0.30-1/tháng** |

## 📁 Cấu trúc project

```
japan-finance-agent/
├── src/
│   ├── agent.py              # Main orchestrator
│   ├── analyzer.py           # Claude API analysis
│   ├── telegram_bot.py       # Telegram sender
│   └── collectors/
│       ├── google_trends.py  # Google Trends JP
│       ├── rss_collector.py  # Nikkei, Reuters, Bloomberg RSS
│       ├── youtube_collector.py  # YouTube trending
│       └── twitter_collector.py  # Twitter/X hashtags
├── .github/
│   └── workflows/
│       └── daily_digest.yml  # GitHub Actions schedule
├── requirements.txt
└── README.md
```

## 🔧 Tùy chỉnh

**Thay đổi giờ chạy** → Sửa cron trong `daily_digest.yml`:
```yaml
- cron: "0 22 * * *"  # 7:00 AM JST
```

**Thêm keywords theo dõi** → Sửa `FINANCE_KEYWORDS` trong `google_trends.py`

**Thêm RSS feeds** → Thêm vào `RSS_FEEDS` trong `rss_collector.py`
