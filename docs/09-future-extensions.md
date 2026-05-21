# Future Extensions (v2+)

Once the v1 system is stable, here's what's worth adding, ranked by leverage.

---

## High value, low effort

### 1. Audio clip extraction for key quotes
When the agent identifies a notable quote, store the timestamp range and use `yt-dlp` + `ffmpeg` to extract a 30-60 second audio clip. Upload to a Notion page or S3 and link from the briefing. Hamid can listen to the actual delivery, not just read the transcript.

Effort: a single new helper script, ~30 lines of ffmpeg. Adds maybe $0.50/month in storage.

### 2. Weekly digest
A second scheduled run, Sundays at 18:00, that summarizes the past week's briefings into a "what mattered this week" digest. Reads the past 7 days of Notion briefings, identifies recurring themes, and produces a single page. Useful for the "I missed Tuesday and Wednesday" recovery case.

Effort: a new agent definition (or same agent with a different prompt) plus a second schedule. Half a day.

### 3. Search-by-theme over historical briefings
The Daily Briefings database is searchable in Notion natively, but a chat interface — "what did [X] say about Nvidia in the last 3 months?" — would be more useful. Build a tiny Claude-powered search over the briefing archive.

Effort: a small standalone agent or a Claude Code Routine. A few hours.

---

## High value, medium effort

### 4. Auto-discovery of new podcasts
The agent notices that recent episodes mention a podcast Hamid doesn't yet follow (e.g., Gavin Baker references Dwarkesh on Invest Like the Best). It surfaces a "consider adding?" suggestion in the next briefing.

Effort: requires tracking podcast mentions in transcripts, deduplicating against the existing list, and a clean UX for "add this" → "no thanks." One sprint.

### 5. Per-context interest profiles
Right now there's one interest profile. In reality Hamid might want different lenses: "work-Hamid" wants pure investment alpha; "weekend-Hamid" wants long-form essays on history and philosophy. Allow multiple profiles in Notion, with a "context" column on podcasts ("work", "weekend", "both") that selects which profile to apply.

Effort: small schema changes plus prompt logic. One day.

### 6. Real-time alerts for high-priority topics
If a transcript matches certain triggers (e.g., "Anthropic" + "earnings", or a specific person speaking on a specific topic), send a Slack ping immediately rather than waiting for the daily 07:00. Requires polling more frequently or moving to webhook-based triggering via Taddy (paid).

Effort: harder than it sounds because it requires either intra-day polling (5x cost) or paid webhooks. Probably not worth it for personal use.

---

## Lower value but interesting

### 7. Cross-podcast theme tracking
Build a small visualization of how a theme propagates across podcasts. "Orbital compute" first mentioned on podcast X on date Y, then appears on podcasts Z, A, B over the next 3 weeks. Useful for tracking when a meme is becoming consensus.

Effort: a Notion-backed analytics agent. Half a day, but mostly novelty value.

### 8. Quality scoring of podcasts over time
Track which podcasts consistently produce "useful" episodes for Hamid and which produce mostly noise. Show a leaderboard. Use to prune the active list.

Effort: trivial once feedback_log is populated. A few hours.

### 9. Sharing select briefings
A button on a Notion briefing page that flips a `Share` toggle, which the agent then publishes to a private Notion site or sends to a colleague. Curated podcast intel becomes a low-friction social object.

Effort: needs a UI flow, more than just agent logic. A weekend project.

### 10. Integration with other inputs
The same agent pattern works for newsletters, YouTube channels not tied to podcasts, X/Twitter threads, Substack RSS, research reports. Generalize the Notion source-of-truth schema from "Podcasts" to "Information sources" and add a `type` column.

Effort: medium — each new input type needs its own fetch helper and transcript-equivalent. Worth doing once Hamid finds he wants this for newsletters too.

---

## Things deliberately NOT recommended

### Multi-agent orchestration for this use case
Managed Agents supports multi-agent orchestration. It's overkill here — one agent doing sequential steps is faster, cheaper, and easier to reason about than orchestrating sub-agents per podcast. Skip.

### Switching to Opus for everything
Opus 4.6 is ~5x the cost of Sonnet 4.6 and the marginal quality gain on transcript summarization is modest. Use Sonnet, escalate only the summarization step if needed.

### Building your own UI
Notion + Slack + email is the UI. Don't build a custom dashboard. The marginal value of a custom UI is small; the maintenance cost is large.

### Adding a paid transcript vendor "to be safe"
Adding Supadata ($17/mo) or Taddy ($75/mo) buys robustness, but the youtube-transcript-api free path is robust enough for personal use. If you find yourself spending more than 30 minutes a month fixing transcript issues, then upgrade — not before.

---

## When to walk away

If after 6 weeks of daily runs:
- Hamid isn't reading the briefings most mornings
- The "Useful?" rate is stuck below 20%
- The system needs constant babysitting

…then the *concept* might be wrong, not the implementation. The fix isn't more features — it's reconsidering whether daily podcast monitoring is really the right tool for what Hamid is trying to achieve. Maybe he wants weekly, or maybe he wants only specific people, or maybe the whole thing should be replaced by a different agent entirely.

Don't extend a system that isn't earning its keep.
