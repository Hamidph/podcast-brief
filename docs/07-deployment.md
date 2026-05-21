# Deployment

Step-by-step build order. Designed for a Claude Code agent to execute end to end.

---

## Prerequisites checklist

Before writing any code, confirm Hamid has done these manual setup steps. The builder agent should ask Hamid to confirm each one.

- [ ] **Anthropic API account** with Managed Agents enabled (public beta, default-on as of April 2026). API key in hand, with permission to create agents and schedules.
- [ ] **Notion workspace** with two empty databases created per `02-notion-schemas.md`. Database IDs collected.
- [ ] **Notion internal integration** created at notion.so/profile/integrations. Token collected. Both databases + the interest profile page shared with the integration.
- [ ] **Slack workspace** with a new app created. App has `chat:write` and `chat:write.public` scopes. App installed. Bot token (xoxb-...) collected. Target channel/DM ID collected.
- [ ] **Resend account** at resend.com, with a verified sender domain (or use Resend's onboarding sandbox domain for testing). API key collected.
- [ ] **Interest Profile page** in Notion drafted with Hamid's themes, people, companies, and "what to skip" rules (template in `02-notion-schemas.md`).
- [ ] **3-5 podcasts** added to the Podcasts database with RSS feed URLs and YouTube channel URLs filled in. Active=true.

If any of these are missing, pause and surface to Hamid before continuing.

---

## Build order

### Phase 1: Local prototype of the Python helpers
Before deploying to Managed Agents, validate the helpers work end-to-end on one podcast.

1. Create a local working directory (anywhere).
2. Write `fetch_rss.py`, `find_youtube_video.py`, `fetch_transcript.py`, `send_email.py` per `06-code-modules.md`.
3. `pip install feedparser youtube-transcript-api yt-dlp resend requests python-dateutil`
4. Run an end-to-end smoke test manually:
   ```bash
   python fetch_rss.py "https://feeds.megaphone.fm/investlikethebest" "2026-05-15T00:00:00Z"
   # Pick one episode's title from the output
   python find_youtube_video.py "https://youtube.com/@InvestLikeTheBest" "<that title>" 5
   # Pick the matching video_id
   python fetch_transcript.py <video_id>
   # Confirm transcript text comes back
   ```
5. If any step fails, fix locally before deploying. Most likely failure points: `yt-dlp` version mismatch, YouTube returning empty results for a channel URL format, transcript_api breakage for newer videos.

### Phase 2: Create the Managed Agent

1. Set environment variables for the build session:
   ```bash
   export ANTHROPIC_API_KEY="..."
   export NOTION_TOKEN="..."
   export NOTION_PODCASTS_DB_ID="..."
   export NOTION_BRIEFINGS_DB_ID="..."
   export NOTION_INTEREST_PROFILE_PAGE_ID="..."
   export SLACK_BOT_TOKEN="..."
   export SLACK_CHANNEL_ID="..."
   export RESEND_API_KEY="..."
   export EMAIL_TO="hamid@lendhub.co.uk"
   export EMAIL_FROM="podcasts@<your-resend-domain>"
   ```

2. Store these secrets in the Managed Agents secret vault. Refer to the current Managed Agents docs for the exact API call — likely a POST to `/v1/secrets` or via the dashboard.

3. Create the agent via the platform API. The body matches `03-managed-agent-config.md`:
   ```bash
   curl https://api.anthropic.com/v1/agents \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "anthropic-beta: managed-agents-2026-04-01" \
     -H "content-type: application/json" \
     -d @agent-definition.json
   ```
   Save the returned `agent_id`.

4. Upload the helper scripts to the agent's sandbox. The exact API depends on the current Managed Agents file-deployment story — check docs. Two likely paths:
   - **If sandbox supports preinstalled files:** upload via the agent's `sandbox.files` field at creation, or via a separate `/agents/{id}/files` endpoint.
   - **If not:** include the scripts inline in the system prompt under a `<helpers>` tag, and have the system prompt instruct the agent to write them to disk on first run.

### Phase 3: Manual test run

1. Trigger a one-off session with the **debug run prompt** from `05-daily-run-prompt.md`:
   ```bash
   curl https://api.anthropic.com/v1/agents/$AGENT_ID/sessions \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "anthropic-beta: managed-agents-2026-04-01" \
     -H "content-type: application/json" \
     -d '{"input": "This is a manual debug run. Today is 2026-05-21. ...full debug prompt..."}'
   ```

2. Stream or poll the session output. Watch for:
   - Agent reads Notion Podcasts DB ✓
   - Agent reads Interest Profile page ✓
   - Agent fetches RSS for at least one podcast ✓
   - Agent finds matching YouTube video ✓
   - Agent fetches transcript ✓
   - Agent writes to Notion Daily Briefings ✓
   - Agent posts to Slack ✓
   - Agent sends email ✓

3. Check the actual output in Notion, Slack, and email. Compare against the verification checklist in `08-verification.md`.

4. If the briefing quality is off, iterate on the **interest profile** (in Notion — no redeploy needed) and the **system prompt** (requires agent update). Aim for 3-5 iterations.

### Phase 4: Enable the schedule

Once a manual run produces a satisfying briefing:

1. Add the schedule trigger to the agent:
   ```bash
   curl https://api.anthropic.com/v1/agents/$AGENT_ID/schedules \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "anthropic-beta: managed-agents-2026-04-01" \
     -H "content-type: application/json" \
     -d '{
       "cron": "0 7 * * *",
       "timezone": "Europe/London",
       "input_template": "Run your daily podcast briefing for {{TODAY_DATE}}. ...full production prompt..."
     }'
   ```

2. Confirm it appears in the dashboard with "next run: tomorrow 07:00 BST".

3. Wait for the first automated run. Check the briefing the next morning.

### Phase 5: Tuning loop (week 1)

For the first 7 days:
- Each morning, read the briefing, check "Useful?" boxes on items that delivered signal.
- Note in a working file (in this repo, `tuning-notes.md`) what felt off: too long, missed the key point, surfaced irrelevant episodes, etc.
- After 7 days, iterate on:
  - **Interest profile** (edit the Notion page directly)
  - **System prompt** (update the agent definition)
  - **Podcast list** (add/remove rows in Notion)

The feedback log inside the agent's memory will start influencing summaries automatically — no manual prompt-tuning required for that loop.

### Phase 6: Optional — enable Dreaming

After 2-3 weeks of stable daily runs with feedback flowing in:

1. Request Dreaming access at the form linked from the Managed Agents docs.
2. Once granted, add `dreaming-2026-04-21` to the beta header.
3. Configure Dreaming to run weekly over the past 7 days of sessions.
4. Dreaming will surface patterns in `feedback_log.json` and refine `recent_themes.md` better than the agent can do incrementally.

This is a "nice to have." Skip if you don't get to it.

---

## What to ship vs. what to defer

**Ship in v1:**
- Full daily run with Notion + Slack + email delivery
- Interest profile in Notion (read each run)
- Memory: seen_episodes, feedback_log, recent_themes
- Outcomes rubric for self-checking
- 3-5 podcasts to start, expandable via Notion

**Defer to v2:**
- Dreaming (research preview, not critical)
- Multi-agent orchestration (don't need it for personal use)
- Webhook-based real-time triggering (daily cron is plenty)
- Multiple interest profiles (e.g., "work mode" vs. "weekend mode")
- Per-podcast custom prompts beyond the Notes field
- Auto-discovery of new podcasts based on stated interests
- Audio clip generation (Snipd-style) — would need a separate audio download + clipping pipeline

---

## Estimated build time

For a competent Claude Code agent with API access already provisioned:
- Phase 1 (local prototype): 30-60 min
- Phase 2 (deploy agent): 30-60 min
- Phase 3 (manual test): 30-60 min, plus 1-2 cycles of fixes
- Phase 4 (schedule): 5 min
- Total to first scheduled run: half a day

Plus 1-2 weeks of tuning runs after that to dial in the interest profile.
