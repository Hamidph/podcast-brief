# Verification & Troubleshooting

A checklist for the builder agent to confirm the system is working end-to-end, plus a guide to the most likely failure modes and their fixes.

---

## First-run verification checklist

After Phase 3 of `07-deployment.md` (the first manual debug run), confirm:

### Inputs read correctly
- [ ] Agent successfully read the Notion Podcasts database — count of active rows matches what's in Notion
- [ ] Agent successfully read the Interest Profile page — its summary references at least one specific theme from the profile
- [ ] Agent successfully read prior memory (empty on first run — confirm it gracefully handles "no seen episodes yet")

### Episode discovery
- [ ] For each active podcast, agent fetched RSS feed without error
- [ ] For each podcast with recent episodes, agent correctly identified what's "new" (i.e., everything is "new" on first run)
- [ ] If a podcast's RSS is broken (404, malformed XML), agent skipped it gracefully and surfaced the issue in the briefing, did not crash

### Transcript fetching
- [ ] For each new episode, agent attempted to find a YouTube video match
- [ ] Agent's match decisions are sensible — spot-check 2-3 episodes by clicking through to the YouTube URL it picked
- [ ] For matched videos, transcript was successfully fetched
- [ ] For unmatched episodes (no YouTube upload yet, or no YouTube channel for the show), agent marked them `pending_youtube` and noted this in the briefing

### Summarization
- [ ] Each episode summary has all four fields: key_points, why_you_care, listen_if_verdict, notable_quotes
- [ ] Key points are claim-shaped, not topic-shaped (see system prompt examples)
- [ ] Why-you-care explicitly references items from the Interest Profile
- [ ] Verdicts are differentiated — not every episode is "Listen to the whole thing"

### Delivery
- [ ] Notion: a new page exists in the Daily Briefings database with today's date as title
- [ ] Notion: each episode appears as a child block with the expected structure (h2, paragraphs, h3, bullets, quote, divider)
- [ ] Notion: "Useful?" to-do checkbox appears below each episode
- [ ] Slack: a message was posted to the configured channel with link to Notion
- [ ] Slack: message format is human-readable, not raw JSON
- [ ] Email: an email was received at hamid@lendhub.co.uk with the briefing as HTML

### State persistence
- [ ] After the run, `seen_episodes.json` in memory contains the GUIDs of all processed episodes
- [ ] `recent_themes.md` has today's themes appended
- [ ] If the run is triggered again immediately, the agent finds no new episodes (idempotency check)

### Outcomes rubric
- [ ] The Outcomes self-evaluation reports all critical/high checks as passed (or surfaces honest failures)

---

## Common failure modes and fixes

### Failure: "No transcripts available" for every episode
**Symptoms:** Agent marks every episode `transcript_unusable` or `pending_youtube`.

**Likely causes:**
1. `youtube-transcript-api` has broken due to a YouTube-side change. Check the library's GitHub issues for a recent "broken" report. Fix: `pip install --upgrade youtube-transcript-api`. Redeploy the agent's sandbox.
2. The YouTube channel URLs in Notion are wrong format. They should be either `https://youtube.com/@HandleName` or `https://youtube.com/channel/UCxxxx`. The `/c/` format sometimes fails with yt-dlp.
3. The agent's match logic is too strict. Look at the debug output — what candidates did it see? If candidates were present but it picked none, loosen the prompt language around match thresholds.

### Failure: Wrong YouTube video matched to RSS episode
**Symptoms:** Agent picked a video that doesn't actually correspond to the podcast episode. Often happens when a podcast's YouTube channel also hosts clips and shorts.

**Fix:**
- Update `find_youtube_video.py` to filter by duration: real podcast episodes are usually 30+ minutes. Add a `--min-duration` filter to skip clips.
- In the system prompt, add: "Prefer videos with duration ≥ 25 minutes for podcast matching, unless the RSS episode is explicitly a short."

### Failure: Notion page creation fails with "Unauthorized" or "Object not found"
**Symptoms:** Agent reports Notion API 401 or 404.

**Likely causes:**
1. The Notion integration isn't shared with the target database. Open the database → ⋯ → Connections → add the integration.
2. The database ID is wrong. The ID is the 32-char UUID in the URL, with or without dashes — Notion's API accepts both but be consistent.
3. The integration token has expired or been regenerated. Issue a new token, update the secret vault.

### Failure: Slack message posts but with no formatting
**Symptoms:** Slack receives the raw JSON of the briefing instead of a clean message.

**Fix:** The agent should post using Slack's `chat.postMessage` with `blocks` or `text` parameter, not the entire JSON payload. Update the system prompt's Slack delivery instruction to be explicit: "Post a plain text message with the headline summary; do not paste structured data."

### Failure: Email never arrives
**Symptoms:** Resend reports success, no email lands.

**Likely causes:**
1. Sender domain not verified in Resend. Check resend.com/domains and complete DNS verification.
2. Email landed in spam (common for fresh sender domains). Check spam folder, mark as not-spam, add the sender to contacts.
3. Recipient address typo in env var. Verify `EMAIL_TO` is exactly `hamid@lendhub.co.uk`.

### Failure: Agent re-processes the same episode every day
**Symptoms:** `seen_episodes.json` doesn't seem to persist across runs.

**Likely causes:**
1. Memory namespace mismatch — the agent is writing to one namespace and reading from another. Confirm `memory.namespace` is consistent in the agent definition.
2. The agent isn't actually saving — check the agent's bash logs for the actual write call. The system prompt requires the agent to save after delivery; if it skipped that step due to a delivery failure, the GUID won't be saved (which is correct behavior for failed runs, but means retry will reprocess).

### Failure: Briefing quality is poor / generic / off-target
**Symptoms:** Hamid checks no "Useful?" boxes for the first week.

**This is the most important failure to handle, because it's not a technical bug.**

**Fixes, in order:**
1. **Sharpen the Interest Profile.** Most "generic" output comes from a vague profile. Add specificity: instead of "AI infrastructure," write "Nvidia/TSMC supply chain dynamics, ASIC competitors to Nvidia, power and cooling constraints on data center buildouts." Instead of "people I follow," list 15-20 specific names.
2. **Add per-show Notes.** In each podcast row, write what you specifically want from *that* show. "On Acquired, surface the strategic frameworks not the company history."
3. **Tune the system prompt's "How to summarize an episode well" section.** Add or refine examples of good vs. bad key_points.
4. **Escalate the summarization step to Opus 4.6.** If quality is still off after the above, the model is probably the bottleneck. Cost is ~5x but for personal use that's still <$50/month.
5. **Let the feedback loop work.** The first week will be rough. By week 3, the feedback_log + Dreaming (if enabled) will be biasing toward what you actually mark useful.

### Failure: Run takes too long / costs too much
**Symptoms:** Each run is consuming hours of runtime or large token counts.

**Likely causes:**
1. The agent is fetching full transcripts for episodes it should skip (e.g., 4-hour episodes from shows that aren't a high priority). Add a duration cap in the daily run prompt: "Skip episodes over 3 hours unless the show's Notes mention they're worth the full transcript."
2. The agent is re-reading the same RSS feed multiple times (debugging itself). Tighten the system prompt to require single-pass reads.
3. There are too many podcasts. Trim to 5-7 for v1; expand once stable.

---

## How to know it's working well

After 2-3 weeks of daily runs:
- Hamid is checking "Useful?" on at least 30% of episode entries
- Hamid is actually reading the Slack ping each morning
- The "Themes" multi-select on the Daily Briefings DB has accumulated 20-30 distinct themes — the agent has built a vocabulary of what Hamid's world looks like
- Runs are completing in under 15 minutes with no manual intervention for ≥5 days in a row
- Total monthly cost is in the $5-10 range

If these are all true, the system is doing its job. Now go listen to fewer podcasts.
