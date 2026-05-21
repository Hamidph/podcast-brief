# Daily Run Prompt

This is the user-turn prompt that the scheduler sends to the agent each day. It tells the agent "go run your daily routine now." The agent's system prompt already explains *how* — this prompt is the trigger.

Keep it short. Heavy lifting is in the system prompt; this is just the kick-off.

---

## Production prompt

```
Run your daily podcast briefing for {{TODAY_DATE}} (timezone: Europe/London).

Steps:
1. Read the Notion Podcasts database (id: {{NOTION_PODCASTS_DB_ID}}) and filter to Active=true.
2. Read the Notion Interest Profile page (id: {{NOTION_INTEREST_PROFILE_PAGE_ID}}).
3. Read your memory: seen_episodes.json, feedback_log.json, recent_themes.md.
4. Read yesterday's briefing in the Daily Briefings database (id: {{NOTION_BRIEFINGS_DB_ID}}) and update feedback_log.json from the "Useful?" checkboxes there.
5. For each active podcast, fetch its RSS feed (use the bash tool with feedparser). Find new episodes since your last run (GUID not in seen_episodes.json).
6. For each new episode:
   a. Find the matching YouTube video in the show's channel (use yt-dlp search via bash). Use your judgement on title/description matching.
   b. Fetch the transcript via youtube-transcript-api.
   c. If transcript unavailable, mark as pending_youtube and skip.
7. Summarize each episode against the Interest Profile, producing key_points, why_you_care, listen_if_verdict, notable_quotes.
8. Create today's briefing page in the Daily Briefings database (id: {{NOTION_BRIEFINGS_DB_ID}}). Page title = today's date in YYYY-MM-DD. Use the per-episode block structure described in your context.
9. Post a Slack message to channel {{SLACK_CHANNEL_ID}}. Format: "🎙️ Daily podcast briefing — {N} new episodes, {M} worth a listen.\n{One-line headlines, one per show}\n<Notion link>"
10. Send an email to {{EMAIL_TO}} from {{EMAIL_FROM}} via the Resend API. Subject: "Podcast briefing — {{TODAY_DATE}}". Body: same content as the Notion page, rendered as HTML.
11. Update seen_episodes.json with all processed GUIDs. Update recent_themes.md with today's themes.
12. Mark Run Status = Complete (or Partial if anything failed) on the Notion briefing page.
13. Self-evaluate against the Outcomes rubric.

If no podcasts have new episodes today: still create the briefing page with "No new episodes" body, send a one-line Slack ping ("🎙️ No new episodes today"), and skip email. This confirms the system is alive.
```

---

## Template variables

The scheduler should inject these at runtime. Most are static (set once in the agent's secret vault), only `TODAY_DATE` is dynamic.

| Variable | Value source |
|---|---|
| `{{TODAY_DATE}}` | Today's date in YYYY-MM-DD, computed at trigger time in Europe/London |
| `{{NOTION_PODCASTS_DB_ID}}` | env var |
| `{{NOTION_BRIEFINGS_DB_ID}}` | env var |
| `{{NOTION_INTEREST_PROFILE_PAGE_ID}}` | env var |
| `{{SLACK_CHANNEL_ID}}` | env var |
| `{{EMAIL_TO}}` | env var |
| `{{EMAIL_FROM}}` | env var |

If your runtime doesn't support template injection in the prompt, hardcode them — they're not secrets, they're just IDs.

---

## Manual / debug run prompt

For one-off testing (you want to trigger a run manually without waiting for the cron), use this slightly looser variant:

```
This is a manual debug run. Today's date is {{TODAY_DATE}}.

Execute your daily podcast briefing routine end-to-end. Verbose mode: at each step, log what you're doing to stdout before doing it (e.g., "Fetching RSS for Invest Like the Best...", "Found 1 new episode: 'Gavin Baker — ...'"). At the end, print a summary of:
- How many podcasts you checked
- How many new episodes you found
- How many you successfully transcribed
- How many you marked pending_youtube or transcript_unusable
- What you delivered to Notion, Slack, and email

If anything failed, explain why in plain language. Do not pretend success.
```

This is what you'd send during initial testing to see the agent's reasoning out loud.
