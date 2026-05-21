# podcast-brief

Personal AI agent that runs once a day, checks a curated list of podcasts in Notion, fetches YouTube transcripts for new episodes, summarizes them through Claude using a personal interest profile, and delivers a structured daily briefing to Notion, Slack, and email.

## Architecture

```
Notion (Podcasts DB, Interest Profile)
        │
        ▼
Claude Managed Agent (daily cron, 07:00 London)
   ├── fetch_rss.py      → feedparser
   ├── find_youtube_video.py → yt-dlp
   ├── fetch_transcript.py  → youtube-transcript-api
   └── send_email.py        → Resend
        │
        ├─→ Notion (Daily Briefings DB)
        ├─→ Slack (#podcast-briefing)
        └─→ Email (hamid@lendhub.co.uk)
```

See `docs/01-architecture.md` for full data flow.

## Local Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Test RSS fetching
PYTHONPATH=src uv run python -m podcast_brief.fetch_rss "https://feeds.megaphone.fm/investlikethebest" "2026-05-01T00:00:00Z"

# Test YouTube search
PYTHONPATH=src uv run python -m podcast_brief.find_youtube_video "https://www.youtube.com/@joincolossus" "Gavin Baker" 5

# Test transcript fetching (requires non-cloud IP)
PYTHONPATH=src uv run python -m podcast_brief.fetch_transcript <video_id>
```

## Deployment

See `docs/07-deployment.md` for full deployment guide. Summary:

1. Create Notion databases per `docs/02-notion-schemas.md`
2. Set up secrets (Notion, Slack, Resend, Anthropic)
3. Create the Managed Agent via API using `config/agent_definition.json`
4. Upload helper scripts to the agent's sandbox
5. Create the cron schedule using `config/schedule.json`
6. Run a manual debug test using `config/debug_run_prompt.md`

## Environment Variables

Copy `.env.example` to `.env` and fill in values. See `docs/07-deployment.md` for where to get each one.

## Project Structure

```
├── src/podcast_brief/       # Python helper scripts for the agent
│   ├── fetch_rss.py         # RSS feed parser
│   ├── find_youtube_video.py # YouTube video search via yt-dlp
│   ├── fetch_transcript.py  # YouTube transcript fetcher
│   └── send_email.py        # Email sender via Resend
├── config/                  # Agent configuration
│   ├── agent_definition.json # Managed Agent definition
│   ├── system_prompt.md     # Agent system prompt
│   ├── daily_run_prompt.md  # Production daily trigger prompt
│   ├── debug_run_prompt.md  # Debug/test trigger prompt
│   └── schedule.json        # Cron schedule definition
├── docs/                    # Full build spec (00-09)
├── tests/                   # Unit tests
├── pyproject.toml           # Dependencies and tool config
└── .env.example             # Environment variable template
```

## Cost Estimate

~$5-10/month at personal scale (~10 podcasts): Claude tokens + Managed Agent runtime. All other services (RSS, YouTube transcripts, Notion MCP, Slack MCP, Resend free tier) are free.
