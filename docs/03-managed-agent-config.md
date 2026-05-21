# Managed Agent Configuration

Create the agent via the Claude Platform API. This file specifies the exact agent definition.

## Required headers on all API calls

```
x-api-key: $ANTHROPIC_API_KEY
anthropic-version: 2023-06-01
anthropic-beta: managed-agents-2026-04-01
content-type: application/json
```

If using Dreaming (optional, see end of this file), also add `anthropic-beta: dreaming-2026-04-21` (comma-separated with the managed-agents header).

## Agent definition

```json
{
  "name": "podcast-monitor",
  "description": "Daily podcast monitoring agent for Hamid. Reads a Notion-maintained list of podcasts, fetches transcripts from YouTube, summarizes new episodes against a personal interest profile, and delivers to Notion + Slack + email.",
  "model": "claude-sonnet-4-6",
  "system_prompt_ref": "see 04-system-prompt.md",
  "tools": [
    {
      "type": "agent_toolset_20260401"
    }
  ],
  "mcp_servers": [
    {
      "type": "url",
      "url": "https://mcp.notion.com/mcp",
      "name": "notion",
      "authorization_token_ref": "NOTION_TOKEN"
    },
    {
      "type": "url",
      "url": "https://mcp.slack.com/mcp",
      "name": "slack",
      "authorization_token_ref": "SLACK_BOT_TOKEN"
    }
  ],
  "sandbox": {
    "preinstalled_packages": [
      "feedparser==6.0.11",
      "youtube-transcript-api>=0.6.2",
      "yt-dlp",
      "requests",
      "python-dateutil",
      "resend"
    ]
  },
  "memory": {
    "enabled": true,
    "namespace": "podcast-monitor-v1"
  },
  "outcomes": {
    "enabled": true,
    "rubric_ref": "see outcomes section below"
  }
}
```

Notes on each field:

### `model`
Use `claude-sonnet-4-6` for v1. Escalate the summarization step to Opus 4.6 only if quality is insufficient.

### `tools`
The `agent_toolset_20260401` bundle gives the agent bash, read, write, edit, glob, grep, web_search, web_fetch — everything needed to run Python helpers, read transcripts, and look up things. No need to declare these individually.

### `mcp_servers`
Two MCPs minimum: Notion and Slack. Both have stable hosted MCP endpoints in 2026.

For Notion: use the official Notion MCP URL. The integration token (from `02-notion-schemas.md`) is the authorization.

For Slack: install a Slack app for your workspace, give it `chat:write` and `chat:write.public`, install it, copy the bot token. The Slack MCP URL is the hosted endpoint.

If a hosted Notion or Slack MCP is unavailable in your region, fall back to the **MCP connector** approach — host the open-source `mcp-server-notion` and `mcp-server-slack` and point to those URLs.

### `sandbox.preinstalled_packages`
The Managed Agents sandbox can preload Python packages, saving install time on each run. Pin `feedparser` for stability. `youtube-transcript-api` should be unpinned or use `>=0.6.2` so the agent always gets the latest fix when YouTube changes things.

### `memory`
Enables the public-beta memory system. The namespace `podcast-monitor-v1` scopes the agent's memory so other agents Hamid runs don't collide. The agent stores `seen_episodes.json`, `feedback_log.json`, and `recent_themes.md` in this namespace.

### `outcomes`
Enables self-evaluation against a rubric. See the rubric definition below.

## Outcomes rubric

The agent evaluates its own run against this rubric at the end. Failures are logged and surfaced in the next run's context, so the agent learns from mistakes.

```yaml
outcomes:
  - name: notion_delivery_succeeded
    description: A new page was created in the Daily Briefings database for today's date with all expected child blocks.
    severity: critical

  - name: slack_delivery_succeeded
    description: A Slack message was posted to the configured channel containing a link to today's Notion briefing.
    severity: critical

  - name: email_delivery_succeeded
    description: An email containing today's briefing was sent to the configured address.
    severity: high

  - name: all_active_podcasts_checked
    description: Every podcast row with Active=true in the Notion Podcasts database was checked for new episodes.
    severity: critical

  - name: no_duplicate_episodes
    description: No episode that already appears in seen_episodes.json was reprocessed.
    severity: high

  - name: interest_profile_applied
    description: Each episode summary references at least one theme, person, or company from the interest profile, OR explicitly notes "not aligned with profile, surfacing because [reason]".
    severity: medium

  - name: transcripts_or_explicit_fallback
    description: For each new episode, either a transcript was successfully fetched OR the episode was marked pending_youtube with a clear reason in the briefing.
    severity: high
```

## Scheduling

Managed Agents supports scheduled triggers. Configure the schedule via the platform API or dashboard:

```json
{
  "agent_id": "<your agent id>",
  "schedule": {
    "type": "cron",
    "expression": "0 7 * * *",
    "timezone": "Europe/London"
  },
  "input_prompt_ref": "see 05-daily-run-prompt.md"
}
```

Minimum interval is 1 hour. Daily at 07:00 local time is sensible — most podcasts that drop overnight will be available.

## Environment variables / secrets

Store these in the Managed Agents secret vault, never in code:

| Variable | Source |
|---|---|
| `NOTION_TOKEN` | Notion internal integration token |
| `NOTION_PODCASTS_DB_ID` | UUID of the Podcasts database |
| `NOTION_BRIEFINGS_DB_ID` | UUID of the Daily Briefings database |
| `NOTION_INTEREST_PROFILE_PAGE_ID` | UUID of the interest profile page (optional) |
| `SLACK_BOT_TOKEN` | Slack app bot token (xoxb-...) |
| `SLACK_CHANNEL_ID` | Channel or DM to post to |
| `RESEND_API_KEY` | Resend.com API key for email |
| `EMAIL_TO` | hamid@lendhub.co.uk |
| `EMAIL_FROM` | A verified Resend sender domain |

The agent's system prompt and code helpers reference these by env var name; secrets never appear in prompts or transcripts.

## Optional: Dreaming

Dreaming (research preview) is the feature where the agent reviews past sessions and curates its own memory between runs. Worth enabling once the v1 system is stable — it'll automatically improve the quality of "what does Hamid find useful" inferences.

To enable:
1. Request access at the form linked from the Managed Agents docs.
2. Once granted, add `dreaming-2026-04-21` to the beta header.
3. Configure dreaming to run weekly (Sunday night, say) over the past week's sessions.
4. Dreaming will refine `feedback_log.json` and `recent_themes.md` automatically.

Skip for v1. Enable in v2.
