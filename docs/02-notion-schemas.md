# Notion Database Schemas

Two databases to create, plus one optional doc. Both databases must be shared with the Notion integration that the Managed Agent will use.

---

## Database 1: "Podcasts" (source of truth)

Hamid maintains this by hand. Agent reads only.

| Property | Type | Required | Notes |
|---|---|---|---|
| `Name` | Title | yes | e.g., "Invest Like the Best" |
| `RSS Feed URL` | URL | yes | The actual RSS feed, not Apple/Spotify links. Find via podchaser.com or castro.fm. |
| `YouTube Channel URL` | URL | recommended | The show's YouTube channel. Leave blank if not on YouTube — agent will fall back to title+description only. |
| `Active` | Checkbox | yes | Uncheck to pause without deleting |
| `Notes` | Text | optional | Per-show context: "Skip celebrity guest episodes" or "I care about portfolio construction discussions here". Read by agent each run. |
| `Priority` | Select: High / Normal / Low | optional | Influences how detailed the summary is. Default Normal. |
| `Last Episode Date` | Date | auto | Agent updates this after each successful processing. Used for debugging. |

### Example rows

```
Name                        | RSS Feed URL                                      | YouTube Channel URL                              | Active | Notes
Invest Like the Best        | https://feeds.megaphone.fm/investlikethebest      | https://youtube.com/@InvestLikeTheBest           | ✓      | Care about: portfolio construction, AI investing, capital allocation. Skip: lifestyle episodes.
Dwarkesh Podcast            | https://dwarkesh.com/feed.xml                     | https://youtube.com/@DwarkeshPatel               | ✓      | All episodes worth a listen. Care about: AI safety, geopolitics, hardware.
Acquired                    | https://acquired.fm/episodes?format=rss           | https://youtube.com/@AcquiredFM                  | ✓      | Long episodes — surface the key thesis, not the full narrative.
```

### Notion integration setup

1. Go to notion.so/profile/integrations
2. Create a new internal integration: name "Podcast Agent", workspace your personal workspace
3. Copy the integration token (starts with `secret_` or `ntn_`)
4. Open the Podcasts database in Notion → ⋯ menu → "Connections" → add the integration
5. Note the database ID (the UUID in the URL when viewing the database as a full page)

---

## Database 2: "Daily Briefings" (agent output)

Agent writes here. One row per day, with a child block per episode.

| Property | Type | Set by | Notes |
|---|---|---|---|
| `Date` | Title (formatted as YYYY-MM-DD) | agent | One row per day. Acts as deduplication key. |
| `Episodes Found` | Number | agent | Count of new episodes processed today |
| `Worth Listening` | Number | agent | Count agent flagged as worth listening |
| `Run Status` | Select: Complete / Partial / Failed | agent | Health indicator |
| `Themes` | Multi-select | agent | Top themes across today's episodes (e.g., "AI compute", "rate cuts", "geopolitics"). Builds up a vocabulary over time. |

The actual content of each briefing lives as **page content** (child blocks), not properties. The agent creates structured blocks per episode:

```
# 2026-05-21 — Daily Podcast Briefing

## Invest Like the Best — Gavin Baker on AI Investing
**Listen-If verdict:** Listen to the whole thing — directly relevant to your AI compute & power thesis
**Why you care:** Discusses orbital compute, TSMC capacity constraints, and Anthropic's revenue ramp — all themes you've flagged
**Useful?** ☐  *(check this box if the briefing was useful — feeds the agent's memory)*

### Key Points
- Anthropic added $11B ARR in one month, larger than Palantir+Snowflake+Databricks combined
- Frontier model tokens still capture the overwhelming majority of economic value at the model layer
- ...

### Notable Quotes
> "Anthropic added their combined businesses in one month. That's just nothing like that has ever happened in the history of capitalism."

### Themes
AI compute, capital allocation, Anthropic, frontier models

---

## Dwarkesh Podcast — [next episode]
...
```

### Per-episode child block structure

Each episode is rendered as:

1. **Heading 2** — `Podcast — Episode title`
2. **Paragraph** — Listen-If verdict (bold label)
3. **Paragraph** — Why you care
4. **To-do block** — "Useful?" checkbox (this is the feedback loop)
5. **Heading 3** — "Key Points"
6. **Bulleted list** — 3-7 key points
7. **Heading 3** — "Notable Quotes" (if any)
8. **Quote block** — 1-3 quotes
9. **Paragraph** — Episode URL + listen time
10. **Divider**

The `Useful?` checkbox is structurally important: at the start of each run, the agent reads yesterday's briefing, sees which boxes Hamid checked, and updates its `feedback_log.json` memory. Over time it learns which podcasts and themes correlate with "useful" and prioritizes accordingly.

---

## Optional: Interest Profile doc

You can either bake the interest profile into the agent's system prompt (simpler) or store it as a Notion page that the agent reads each run (more flexible — Hamid can edit without redeploying).

**Recommended: Notion page.** Easier to evolve.

### Page structure

A simple Notion page titled "Podcast Interest Profile" with sections:

```
# What I want to know about

## Themes I care about
- AI infrastructure (compute, memory, power, fabs)
- AI labs (model performance, business models, talent, capital)
- Capital allocation and corporate strategy
- Geopolitics where it touches tech/AI
- ...

## Specific people whose views I always want flagged
- Gavin Baker, Bill Gurley, Jensen Huang, Dario Amodei, Sam Altman, Elon Musk, ...

## Companies I follow closely
- Nvidia, TSMC, Anthropic, OpenAI, Tesla, SpaceX, Meta, Google, Microsoft, ...

## Types of insight I prize
- Non-obvious mental models
- Specific numbers/datapoints that update priors
- Predictions with explicit reasoning
- Management compensation/incentive structures (per the Gavin Baker example)
- Contrarian takes from informed people

## What to skip
- Generic intros, sponsor reads, recap of last episode
- Celebrity guest interviews unless they have real domain expertise
- Pure entertainment / lifestyle content
```

The agent reads this page at the start of each run and uses it as the lens for summarization.

Share this page with the Notion integration too.

---

## IDs the builder will need

After setup, collect these and store them as environment variables for the Managed Agent:

- `NOTION_TOKEN` — integration token
- `NOTION_PODCASTS_DB_ID` — the Podcasts database UUID
- `NOTION_BRIEFINGS_DB_ID` — the Daily Briefings database UUID
- `NOTION_INTEREST_PROFILE_PAGE_ID` — the interest profile page UUID (optional)
