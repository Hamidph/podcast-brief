# Architecture

## High-level data flow

```
                       ┌─────────────────────────────────────────────────┐
                       │           Hamid (manual, infrequent)            │
                       │  edits Notion "Podcasts" table + interest doc   │
                       └─────────────────────────────────────────────────┘
                                            │
                                            ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │                              Notion                                        │
   │  ┌────────────────────────┐   ┌───────────────────────┐   ┌─────────────┐ │
   │  │  Podcasts (source)     │   │ Daily Briefings       │   │ Interest    │ │
   │  │  Name / RSS / YT / etc │   │ (agent writes here)   │   │ Profile doc │ │
   │  └────────────────────────┘   └───────────────────────┘   └─────────────┘ │
   └────────────────────────────────────────────────────────────────────────────┘
                ▲              ▲                                  ▲
                │ read         │ write                            │ read
                │              │                                  │
   ┌────────────────────────────────────────────────────────────────────────────┐
   │             Anthropic Claude Managed Agent (cloud-hosted)                  │
   │                                                                            │
   │   Triggered: daily on cron schedule (e.g., 07:00 local)                    │
   │                                                                            │
   │   Tools:                                                                   │
   │   ├─ agent_toolset_20260401 (bash, read, web_fetch, ...)                   │
   │   ├─ Notion MCP (databases + pages)                                        │
   │   ├─ Slack MCP (post message)                                              │
   │   └─ Email (via bash → Resend API or SMTP)                                 │
   │                                                                            │
   │   Memory:                                                                  │
   │   ├─ seen_episodes.json (which episodes already processed)                 │
   │   ├─ feedback_log.json (what user marked useful/not useful)                │
   │   └─ recent_themes.md (rolling context of last 30 days of briefings)       │
   │                                                                            │
   │   Bash helpers (Python):                                                   │
   │   ├─ fetch_rss.py    (uses feedparser)                                     │
   │   ├─ fetch_yt.py     (uses youtube-transcript-api + yt-dlp for search)    │
   │   └─ render_brief.py (formats final output)                                │
   └────────────────────────────────────────────────────────────────────────────┘
                │                       │                       │
                ▼                       ▼                       ▼
   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
   │   Notion briefing   │   │   Slack DM ping     │   │   Email fallback    │
   │   (full content)    │   │   (link to Notion)  │   │   (full content)    │
   └─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

## Step-by-step run sequence

A single daily run executes in this order. The agent's run-prompt (see `05-daily-run-prompt.md`) instructs it to follow these steps; the agent decides how to interleave tool calls.

### Step 1 — Read state and source data
- Read the Notion "Podcasts" database. Filter to `Active = true`.
- Read the interest profile (Notion doc OR baked into system prompt — see `04-system-prompt.md`).
- Read agent memory: `seen_episodes.json` and `recent_themes.md`.

### Step 2 — Discover new episodes
- For each active podcast row, fetch the RSS feed (`feedparser`).
- Compare episode GUIDs against `seen_episodes.json`.
- Build a list of `(podcast, episode_guid, title, audio_url, published_date, youtube_channel_url)` for everything new since the last successful run.

### Step 3 — Fetch transcripts
For each new episode:
- Use `yt-dlp` (or YouTube search) to find the matching video in the show's YouTube channel by title similarity. If multiple candidates, ask Claude to pick the best match using episode title + description + publish date as context. This is where Claude reasoning replaces brittle fuzzy-string logic.
- If found, fetch the auto-caption transcript via `youtube-transcript-api`.
- If not found (e.g., YouTube upload lags RSS by a day), mark the episode as `pending_youtube` in memory and skip — retry on next run.

### Step 4 — Summarize
For each episode with a transcript:
- Run a focused Claude reasoning step using the interest profile + per-show notes from Notion + the transcript.
- Output structured fields: `key_points`, `why_you_care`, `listen_if_verdict`, `notable_quotes`.

### Step 5 — Deliver
- Create a new page in the Notion "Daily Briefings" database with structured fields filled in. One page per day, with a child block per episode.
- Post a Slack message: `"🎙️ Daily podcast briefing — N new episodes, M worth a listen. <Notion link>"` Include one-line headline per show.
- Send an email with the same content as the Notion page.

### Step 6 — Update state
- Append all processed episode GUIDs to `seen_episodes.json`.
- Append today's theme summary to `recent_themes.md` (trim to last 30 days).
- Log run completion timestamp.

### Step 7 — Outcome check (optional)
If using the **Outcomes** beta feature, the agent self-evaluates against a rubric:
- "Did I deliver to all three channels?"
- "Did I correctly identify at least one new episode if one existed?"
- "Did each episode summary match the interest profile?"

The rubric lives in the Outcomes config and is checked automatically by Managed Agents.

## Why this architecture, decision rationale

### Why Notion as source-of-truth
Hamid already uses Notion. Adding/removing podcasts shouldn't require touching code. Notion's MCP integration is mature in 2026, so both read and write are first-class.

### Why YouTube auto-captions instead of paid transcription
- Cost: zero vs. $17-100/month
- Coverage: 95%+ of the podcasts a finance/AI-interested user would track are on YouTube
- Quality: imperfect (no speaker labels, occasional jargon errors) but good enough — Claude handles ambiguity in the summarization step
- Maintenance: `youtube-transcript-api` breaks occasionally (1-2x/year) but is actively maintained

### Why daily polling instead of webhooks
Personal scale — there's no need for sub-minute latency. A daily 07:00 run captures everything that dropped overnight. Webhooks would require a hosted endpoint and add infra. Skipped.

### Why Claude reasoning for the title-mismatch step
Examples that break naive matching:
- RSS: "423: Gavin Baker — On Watts, Wafers, and the AI Buildout"
- YouTube: "Gavin Baker - Insights from a Public Markets Investor | Invest Like the Best"

A fuzzy-string library scores these poorly. Claude reading the title, description, and publish date gets it right every time. The cost is one extra Claude call per episode — pennies.

### Why three delivery channels
- Notion: persistent, searchable, supports the feedback loop (Hamid checks "Useful?" boxes)
- Slack: where Hamid will actually notice it in the morning
- Email: fallback if Slack and Notion are missed (travel, weekends, etc.)

Building all three at v1 is barely more work than one, because each is a single MCP call.

### Why Sonnet 4.6, not Opus 4.6
Summarization of clear transcripts against a focused profile is well within Sonnet's range. Opus is overkill for this and costs ~5x. If output quality disappoints, escalate the *summarization* step to Opus while keeping orchestration on Sonnet.

## Idempotency and failure modes

The agent must be safely re-runnable. Same-day re-runs should produce the same briefing, not duplicates.

- `seen_episodes.json` is only updated after successful delivery, so a crashed run will reprocess on next try.
- The Notion briefing page is keyed by date; if today's page exists, the agent updates it rather than creating a duplicate.
- Slack and email are idempotent only at the day level — if the run partially succeeds, the agent should send a "partial briefing" rather than re-sending the whole thing.

## Cost estimate (monthly, personal scale, ~10 podcasts)

| Item | Estimate |
|---|---|
| Managed Agent runtime (~20 min/day × 30 days) | ~$0.80 |
| Claude tokens (Sonnet 4.6, ~5 episodes/day × 30K tokens each) | ~$4-8 |
| Notion MCP, Slack MCP | Free |
| Email via Resend (low volume) | Free tier |
| YouTube transcripts, RSS | Free |
| **Total** | **~$5-10/month** |
