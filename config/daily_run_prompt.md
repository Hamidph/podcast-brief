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
