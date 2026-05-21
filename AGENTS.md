# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a personal podcast monitoring agent that runs daily on Anthropic's Managed Agents platform. The Python helpers in `src/podcast_brief/` are thin I/O scripts invoked by the agent via bash — all reasoning lives in the agent's prompt, not in code.

### Development commands

- **Install deps:** `uv sync`
- **Run tests:** `uv run pytest`
- **Lint:** `uv run ruff check src/ tests/`
- **Auto-fix lint:** `uv run ruff check --fix src/ tests/`

### Running helpers locally

All helpers require `PYTHONPATH=src` prefix when running as modules:

```bash
PYTHONPATH=src uv run python -m podcast_brief.fetch_rss <rss_url> <cutoff_iso>
PYTHONPATH=src uv run python -m podcast_brief.find_youtube_video <channel_url> <query> [max_results]
PYTHONPATH=src uv run python -m podcast_brief.fetch_transcript <video_id>
```

### Known caveats

- **YouTube transcript fetching fails from cloud IPs.** `youtube-transcript-api` is blocked by YouTube when running from AWS/GCP/Azure IPs. This is expected in CI and cloud dev environments. The actual production agent runs in Anthropic's Managed Agent sandbox which has different IP handling. Test transcripts locally or use a proxy.
- **YouTube channel handles vary.** The RSS feed publisher and the YouTube channel may have different names. Example: "Invest Like the Best" podcast → YouTube channel is `@joincolossus`, not `@InvestLikeTheBest`. The agent uses Claude reasoning to match episodes, not string matching.
- **`yt-dlp` breaks periodically** when YouTube changes its API. Run `uv lock --upgrade-package yt-dlp && uv sync` if video search stops working.

### Slack channel

The `#podcast-briefing` channel (ID: `C0B5CNS4RJ5`) is set up for delivery.

### Notion setup (required)

Notion MCP is not connected to this Cursor environment. The agent needs:
1. A "Podcasts" database (schema in `docs/02-notion-schemas.md`)
2. A "Daily Briefings" database (schema in `docs/02-notion-schemas.md`)
3. An "Interest Profile" page
4. A Notion integration token shared with all three

See `docs/07-deployment.md` for full deployment steps.
