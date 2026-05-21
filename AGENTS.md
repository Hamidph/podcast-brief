# AGENTS.md

## Project overview

**podcast-brief** is a personal podcast monitoring agent that runs daily on Anthropic's Managed Agents platform. It reads a curated podcast list from Notion, fetches RSS feeds, summarizes new episodes against a personal interest profile, and delivers structured briefings to Notion, Slack, and email.

## Architecture

```
GitHub Actions (cron 07:00 UTC = 08:00 BST)
  → creates Anthropic Managed Agent session
    → agent reads Notion (Podcasts DB + Interest Profile)
    → fetches RSS feeds via feedparser
    → summarizes episodes using Claude reasoning
    → writes briefing to Notion Daily Briefings DB
    → posts summary to Slack #podcast-briefing
    → sends email via Resend API
```

### Key components

| Component | Location | Purpose |
|---|---|---|
| Python helpers | `src/podcast_brief/` | RSS parsing, YouTube search, transcript fetch, email |
| Agent config | `config/` | System prompt, agent definition, deployed IDs |
| GitHub Actions | `.github/workflows/daily-briefing.yml` | Daily cron trigger at 08:00 London |
| Build spec | `docs/00-09` | Full original spec documents |
| Tests | `tests/` | Unit tests for helpers |

### Deployed resources (Anthropic)

| Resource | ID |
|---|---|
| Agent (v2, no MCP) | `agent_01WJQzuPhtF7m3gSJFFicboY` |
| Agent (v1, with Notion MCP) | `agent_01NP5h8FRup4RvBHf4UGqyRm` |
| Environment | `env_01NqkFM2wqQMYZoJwS6fpSZn` |
| Vault | `vlt_011CbFpUEa6TYXyJLaa9hHrU` |

### Notion databases

| Database | ID |
|---|---|
| Podcasts | `27d43c5f-e417-4b63-ac76-970108d6440a` |
| Daily Briefings | `9efebf0f-01ba-459c-9709-ca80e1ac23af` |
| Interest Profile page | `3672897b-8e36-812a-8f1f-e186d1adedf2` |

### Slack

- Channel: `#podcast-briefing` (ID: `C0B5CNS4RJ5`)

## Development commands

```bash
uv sync                          # Install dependencies
uv run pytest                    # Run tests
uv run ruff check src/ tests/    # Lint
uv run ruff check --fix src/ tests/  # Auto-fix lint
```

### Running helpers locally

```bash
PYTHONPATH=src uv run python -m podcast_brief.fetch_rss <rss_url> <cutoff_iso>
PYTHONPATH=src uv run python -m podcast_brief.find_youtube_video <channel_url> <query> [max_results]
PYTHONPATH=src uv run python -m podcast_brief.fetch_transcript <video_id>
```

## Cursor Cloud specific instructions

### Secrets management

Secrets are stored in **GitHub Actions secrets** and passed to the Managed Agent via the user prompt at session creation. This is the only supported method for cloud environments — Anthropic's Managed Agents cloud environments do not support `init_script` or `environment` variable injection via the API (fields exist in the schema but are rejected on write).

| Secret | Where |
|---|---|
| `ANTHROPIC_API_KEY` | GitHub Actions secret |
| `NOTION_TOKEN` | GitHub Actions secret → passed in agent prompt |
| `SLACK_BOT_TOKEN` | GitHub Actions secret → passed in agent prompt |
| `RESEND_API_KEY` | GitHub Actions secret → passed in agent prompt |

To test locally or in a Cursor Cloud session, set these as Cursor runtime secrets or export them manually.

### Known issues and caveats

1. **Notion MCP auth fails with `static_bearer`** — The Notion MCP server at `https://mcp.notion.com/mcp` rejects static bearer tokens. The agent uses the Notion REST API directly via curl instead. Agent v1 (`agent_01NP5h8FRup4RvBHf4UGqyRm`) has MCP configured but falls back to bash. Agent v2 (`agent_01WJQzuPhtF7m3gSJFFicboY`) skips MCP entirely.

2. **YouTube transcripts blocked from cloud IPs** — `youtube-transcript-api` is blocked by YouTube when running from cloud provider IPs (AWS, GCP, Anthropic sandbox). The agent falls back to RSS episode descriptions + its own knowledge for summarization. Quality is acceptable since most shows have detailed RSS descriptions.

3. **Dwarkesh Podcast RSS is wrong** — The feed URL `feeds.buzzsprout.com/2040953.rss` returns a different show. Needs to be corrected in the Notion Podcasts database.

4. **Acquired RSS DNS issues** — `feeds.pacific-content.com` sometimes fails to resolve. Try `https://acquired.fm/feed.xml` as an alternative.

5. **No scheduling API** — Anthropic Managed Agents doesn't have a scheduling API yet. Daily runs are triggered by GitHub Actions cron.

6. **Managed Agent environment variables** — Cloud environments don't support `environment` or `init_script` fields via the API (rejected with "Extra inputs are not permitted"). All config must be in the system prompt or user prompt.

7. **GitHub Actions cron timezone** — Set to `0 7 * * *` UTC which is 08:00 BST (summer). In winter (GMT) it runs at 07:00. For year-round 08:00 local, a second cron line would be needed.

### Modifying the agent

To update the Managed Agent's system prompt or tools:
```bash
curl -s -X POST "https://api.anthropic.com/v1/agents/agent_01WJQzuPhtF7m3gSJFFicboY" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: managed-agents-2026-04-01" \
  -H "content-type: application/json" \
  -d '{"version": <current_version>, "system": "<new prompt>"}'
```

Always include `version` (current version number) when updating — the API requires it.

### Triggering a manual run

Use `scripts/trigger_run.sh` or run the GitHub Actions workflow manually from the Actions tab.

### Cost

~$5-10/month at personal scale (~5 podcasts). Main cost is Claude Sonnet tokens for summarization + Managed Agent runtime (~10 min/day).
